"""
Government website crawler for Indonesian government documents.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse
from datetime import datetime
from dataclasses import dataclass
from playwright.async_api import Page, Browser
from bs4 import BeautifulSoup
import aiohttp
import hashlib

from .config import GovernmentScraperSettings


@dataclass
class DocumentInfo:
    """Information about a government document."""
    url: str
    title: str
    file_size: Optional[int]
    content_type: Optional[str]
    last_modified: Optional[str]
    extraction_timestamp: str
    domain: str
    document_type: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None


class GovernmentWebsiteCrawler:
    """Crawler for Indonesian government websites."""
    
    def __init__(self, settings: GovernmentScraperSettings, playwright_manager=None):
        self.settings = settings
        self.playwright_manager = playwright_manager
        self.logger = logging.getLogger(__name__)
        
        # Document file extensions
        self.doc_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']
        
        # Track visited URLs to avoid duplicates
        self.visited_urls: Set[str] = set()
        
        # Rate limiting
        self.last_request_time = 0.0
    
    async def crawl_government_site(
        self,
        base_url: str,
        max_pages: Optional[int] = None,
        max_depth: Optional[int] = None
    ) -> List[DocumentInfo]:
        """Crawl government website for documents."""
        
        if not self._is_government_domain(base_url):
            self.logger.warning(f"Not a government domain: {base_url}")
            return []
        
        max_pages = max_pages or self.settings.max_pages_per_site
        max_depth = max_depth or self.settings.max_crawl_depth
        
        self.logger.info(f"Starting crawl of government site: {base_url}")
        
        documents = []
        urls_to_visit = [(base_url, 0)]  # (url, depth)
        self.visited_urls.clear()
        
        browser = None
        if self.playwright_manager:
            browser = await self.playwright_manager.get_browser()
        
        try:
            while urls_to_visit and len(documents) < max_pages:
                url, depth = urls_to_visit.pop(0)
                
                if url in self.visited_urls or depth > max_depth:
                    continue
                
                self.visited_urls.add(url)
                
                try:
                    # Rate limiting
                    await self._respect_rate_limit()
                    
                    if browser:
                        # Use Playwright for JavaScript-heavy sites
                        page_documents = await self._crawl_with_playwright(browser, url, base_url)
                    else:
                        # Use aiohttp for simple sites
                        page_documents = await self._crawl_with_aiohttp(url, base_url)
                    
                    documents.extend(page_documents)
                    
                    # Find new links if not at max depth
                    if depth < max_depth and len(documents) < max_pages:
                        new_links = await self._extract_links(url, base_url)
                        for link in new_links:
                            if link not in self.visited_urls:
                                urls_to_visit.append((link, depth + 1))
                    
                    self.logger.debug(f"Crawled {url}: found {len(page_documents)} documents")
                    
                except Exception as e:
                    self.logger.error(f"Failed to crawl {url}: {e}")
                    continue
                
                # Add delay between requests
                await asyncio.sleep(self.settings.crawl_delay)
        
        finally:
            if browser and self.playwright_manager:
                await self.playwright_manager.return_browser(browser)
        
        self.logger.info(f"Completed crawl of {base_url}: found {len(documents)} documents")
        return documents
    
    async def _crawl_with_playwright(
        self,
        browser: Browser,
        url: str,
        base_url: str
    ) -> List[DocumentInfo]:
        """Crawl page using Playwright."""
        
        page = await self.playwright_manager.create_page(browser)
        documents = []
        
        try:
            # Navigate to page
            await page.goto(url, wait_until="networkidle", timeout=self.settings.page_timeout)
            
            # Get page content
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract documents
            document_links = self._find_document_links(soup, url)
            
            for link in document_links:
                try:
                    document = await self._extract_document_info(page, link)
                    if document:
                        documents.append(document)
                except Exception as e:
                    self.logger.error(f"Failed to extract document {link}: {e}")
                    continue
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Playwright crawl failed for {url}: {e}")
            return []
        finally:
            await page.close()
    
    async def _crawl_with_aiohttp(self, url: str, base_url: str) -> List[DocumentInfo]:
        """Crawl page using aiohttp."""
        
        documents = []
        
        try:
            headers = {'User-Agent': self.settings.user_agent}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=self.settings.api_timeout) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Extract documents
                        document_links = self._find_document_links(soup, url)
                        
                        for link in document_links:
                            try:
                                document = await self._extract_document_info_aiohttp(session, link)
                                if document:
                                    documents.append(document)
                            except Exception as e:
                                self.logger.error(f"Failed to extract document {link}: {e}")
                                continue
                    
                    return documents
                    
        except Exception as e:
            self.logger.error(f"aiohttp crawl failed for {url}: {e}")
            return []
    
    async def _extract_document_info(
        self,
        page: Page,
        document_url: str
    ) -> Optional[DocumentInfo]:
        """Extract information about a document using Playwright."""
        
        try:
            # Get document metadata
            response = await page.goto(document_url, wait_until="domcontentloaded")
            
            if response and response.status == 200:
                headers = response.headers
                
                return DocumentInfo(
                    url=document_url,
                    title=self._extract_document_title(page),
                    file_size=int(headers.get('content-length', 0)) if headers.get('content-length') else None,
                    content_type=headers.get('content-type'),
                    last_modified=headers.get('last-modified'),
                    extraction_timestamp=datetime.utcnow().isoformat(),
                    domain=urlparse(document_url).netloc,
                    document_type=self._classify_document_type(document_url),
                    description=self._extract_document_description(page)
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to extract document info from {document_url}: {e}")
            return None
    
    async def _extract_document_info_aiohttp(
        self,
        session: aiohttp.ClientSession,
        document_url: str
    ) -> Optional[DocumentInfo]:
        """Extract information about a document using aiohttp."""
        
        try:
            headers = {'User-Agent': self.settings.user_agent}
            
            async with session.head(document_url, headers=headers) as response:
                if response.status == 200:
                    headers = response.headers
                    
                    return DocumentInfo(
                        url=document_url,
                        title=self._extract_title_from_url(document_url),
                        file_size=int(headers.get('content-length', 0)) if headers.get('content-length') else None,
                        content_type=headers.get('content-type'),
                        last_modified=headers.get('last-modified'),
                        extraction_timestamp=datetime.utcnow().isoformat(),
                        domain=urlparse(document_url).netloc,
                        document_type=self._classify_document_type(document_url)
                    )
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to extract document info from {document_url}: {e}")
            return None
    
    def _find_document_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find document links on the page."""
        
        document_links = []
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                # Make URL absolute
                absolute_url = urljoin(base_url, href)
                
                # Check if it's a document
                if self._is_document_url(absolute_url):
                    document_links.append(absolute_url)
        
        return list(set(document_links))  # Remove duplicates
    
    def _is_document_url(self, url: str) -> bool:
        """Check if URL points to a document."""
        url_lower = url.lower()
        return any(ext in url_lower for ext in self.doc_extensions)
    
    def _is_government_domain(self, url: str) -> bool:
        """Check if URL is from a government domain."""
        domain = urlparse(url).netloc.lower()
        return any(gov_domain in domain for gov_domain in self.settings.government_domains)
    
    async def _extract_links(self, url: str, base_url: str) -> List[str]:
        """Extract links from a page."""
        
        try:
            headers = {'User-Agent': self.settings.user_agent}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=self.settings.api_timeout) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        links = []
                        for link in soup.find_all('a', href=True):
                            href = link.get('href')
                            if href:
                                absolute_url = urljoin(base_url, href)
                                # Only include links from the same domain
                                if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
                                    links.append(absolute_url)
                        
                        return list(set(links))  # Remove duplicates
                    
                    return []
                    
        except Exception as e:
            self.logger.error(f"Failed to extract links from {url}: {e}")
            return []
    
    def _extract_document_title(self, page: Page) -> str:
        """Extract document title from page."""
        try:
            title = page.title()
            if title and title != "Document":
                return title
            
            # Try to get title from meta tags
            meta_title = page.locator('meta[property="og:title"]').get_attribute('content')
            if meta_title:
                return meta_title
            
            # Try to get title from h1
            h1_title = page.locator('h1').first.text_content()
            if h1_title:
                return h1_title.strip()
            
            return "Untitled Document"
            
        except Exception as e:
            self.logger.error(f"Failed to extract document title: {e}")
            return "Untitled Document"
    
    def _extract_document_description(self, page: Page) -> Optional[str]:
        """Extract document description from page."""
        try:
            # Try meta description
            meta_desc = page.locator('meta[name="description"]').get_attribute('content')
            if meta_desc:
                return meta_desc
            
            # Try og:description
            og_desc = page.locator('meta[property="og:description"]').get_attribute('content')
            if og_desc:
                return og_desc
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to extract document description: {e}")
            return None
    
    def _extract_title_from_url(self, url: str) -> str:
        """Extract title from URL."""
        try:
            # Extract filename from URL
            filename = url.split('/')[-1]
            if '.' in filename:
                filename = filename.rsplit('.', 1)[0]
            
            # Clean up filename
            title = filename.replace('-', ' ').replace('_', ' ').title()
            return title if title else "Untitled Document"
            
        except Exception as e:
            self.logger.error(f"Failed to extract title from URL: {e}")
            return "Untitled Document"
    
    def _classify_document_type(self, url: str) -> Optional[str]:
        """Classify document type based on URL and extension."""
        url_lower = url.lower()
        
        if '.pdf' in url_lower:
            return 'pdf'
        elif '.doc' in url_lower or '.docx' in url_lower:
            return 'word'
        elif '.xls' in url_lower or '.xlsx' in url_lower:
            return 'excel'
        elif '.ppt' in url_lower or '.pptx' in url_lower:
            return 'powerpoint'
        elif '.txt' in url_lower:
            return 'text'
        else:
            return None
    
    async def _respect_rate_limit(self):
        """Respect rate limiting."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        
        min_interval = 60.0 / self.settings.rate_limit_requests_per_minute
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        self.last_request_time = asyncio.get_event_loop().time()
    
    def get_crawl_stats(self) -> Dict[str, Any]:
        """Get crawling statistics."""
        return {
            'visited_urls': len(self.visited_urls),
            'unique_documents_found': len(set(url for url in self.visited_urls if self._is_document_url(url))),
            'government_domains': self.settings.government_domains,
            'crawl_settings': {
                'max_pages_per_site': self.settings.max_pages_per_site,
                'max_crawl_depth': self.settings.max_crawl_depth,
                'crawl_delay': self.settings.crawl_delay
            }
        }
