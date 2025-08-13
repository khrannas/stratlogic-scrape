import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
import aiohttp
from bs4 import BeautifulSoup
import re

from .config import government_scraper_settings

class GovernmentWebsiteCrawler:
    """
    Crawler for Indonesian government websites to find documents
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = government_scraper_settings
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=self.settings.api_timeout)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={'User-Agent': self.settings.user_agent}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def crawl_government_site(
        self,
        base_url: str,
        max_pages: int = None,
        max_depth: int = None
    ) -> List[Dict[str, Any]]:
        """
        Crawl government website for documents

        Args:
            base_url: Base URL of the government website
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum depth for crawling

        Returns:
            List of document dictionaries
        """
        max_pages = max_pages or self.settings.max_pages_per_site
        max_depth = max_depth or self.settings.max_crawl_depth

        if not self._is_government_domain(base_url):
            self.logger.warning(f"Not a government domain: {base_url}")
            return []

        self.logger.info(f"Starting crawl of government site: {base_url}")

        documents = []
        visited_urls = set()
        urls_to_visit = [(base_url, 0)]  # (url, depth)

        try:
            while urls_to_visit and len(documents) < max_pages:
                url, depth = urls_to_visit.pop(0)

                if url in visited_urls or depth > max_depth:
                    continue

                visited_urls.add(url)

                try:
                    # Fetch page content
                    page_documents = await self._extract_documents_from_page(url)
                    documents.extend(page_documents)

                    # Find new links if not at max depth
                    if depth < max_depth:
                        new_links = await self._extract_links_from_page(url, base_url)
                        for link in new_links:
                            if link not in visited_urls:
                                urls_to_visit.append((link, depth + 1))

                    # Add delay to be respectful
                    await asyncio.sleep(self.settings.crawl_delay)

                except Exception as e:
                    self.logger.error(f"Failed to crawl {url}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error during crawling: {e}")

        self.logger.info(f"Completed crawl of {base_url}. Found {len(documents)} documents")
        return documents

    async def _extract_documents_from_page(self, page_url: str) -> List[Dict[str, Any]]:
        """
        Extract documents from a single page

        Args:
            page_url: URL of the page to extract documents from

        Returns:
            List of document dictionaries
        """
        documents = []

        try:
            async with self.session.get(page_url) as response:
                if response.status != 200:
                    return []

                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')

                # Look for document links
                document_links = self._find_document_links(soup, page_url)

                for link in document_links:
                    try:
                        document = await self._extract_document_info(link)
                        if document:
                            documents.append(document)
                    except Exception as e:
                        self.logger.error(f"Failed to extract document {link}: {e}")
                        continue

            return documents

        except Exception as e:
            self.logger.error(f"Failed to extract documents from {page_url}: {e}")
            return []

    def _find_document_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Find document links on the page

        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL for making relative links absolute

        Returns:
            List of document URLs
        """
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
        """
        Check if URL points to a document

        Args:
            url: URL to check

        Returns:
            True if URL points to a document
        """
        url_lower = url.lower()
        return any(ext in url_lower for ext in self.settings.document_extensions)

    async def _extract_document_info(self, document_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract information about a document

        Args:
            document_url: URL of the document

        Returns:
            Document information dictionary or None if failed
        """
        try:
            # Get document metadata via HEAD request
            async with self.session.head(document_url) as response:
                if response.status != 200:
                    return None

                headers = response.headers

                # Extract file extension
                parsed_url = urlparse(document_url)
                file_extension = parsed_url.path.split('.')[-1].lower() if '.' in parsed_url.path else ''

                return {
                    'url': document_url,
                    'title': self._extract_document_title(document_url),
                    'file_size': headers.get('content-length'),
                    'content_type': headers.get('content-type'),
                    'last_modified': headers.get('last-modified'),
                    'file_extension': file_extension,
                    'source_domain': parsed_url.netloc,
                    'extraction_timestamp': datetime.utcnow().isoformat(),
                    'source': 'government_website'
                }

        except Exception as e:
            self.logger.error(f"Failed to extract document info from {document_url}: {e}")
            return None

    def _extract_document_title(self, document_url: str) -> str:
        """
        Extract document title from URL

        Args:
            document_url: URL of the document

        Returns:
            Document title
        """
        try:
            # Extract filename from URL
            parsed_url = urlparse(document_url)
            filename = parsed_url.path.split('/')[-1]

            # Remove file extension
            if '.' in filename:
                filename = filename.rsplit('.', 1)[0]

            # Clean up filename
            title = filename.replace('_', ' ').replace('-', ' ')
            title = re.sub(r'\s+', ' ', title).strip()

            return title if title else "Untitled Document"

        except Exception as e:
            self.logger.error(f"Failed to extract title from {document_url}: {e}")
            return "Untitled Document"

    async def _extract_links_from_page(self, page_url: str, base_url: str) -> List[str]:
        """
        Extract links from a page for further crawling

        Args:
            page_url: URL of the page
            base_url: Base URL for filtering links

        Returns:
            List of URLs to crawl
        """
        try:
            async with self.session.get(page_url) as response:
                if response.status != 200:
                    return []

                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')

                links = []
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href:
                        absolute_url = urljoin(base_url, href)

                        # Only include links from the same domain
                        if self._is_same_domain(absolute_url, base_url):
                            links.append(absolute_url)

                return list(set(links))  # Remove duplicates

        except Exception as e:
            self.logger.error(f"Failed to extract links from {page_url}: {e}")
            return []

    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """
        Check if two URLs are from the same domain

        Args:
            url1: First URL
            url2: Second URL

        Returns:
            True if URLs are from the same domain
        """
        try:
            domain1 = urlparse(url1).netloc.lower()
            domain2 = urlparse(url2).netloc.lower()
            return domain1 == domain2
        except Exception:
            return False

    def _is_government_domain(self, url: str) -> bool:
        """
        Check if URL is from a government domain

        Args:
            url: URL to check

        Returns:
            True if URL is from a government domain
        """
        try:
            domain = urlparse(url).netloc.lower()
            return any(gov_domain in domain for gov_domain in self.settings.government_domains)
        except Exception:
            return False

    async def search_government_websites(
        self,
        keywords: List[str],
        max_documents_per_site: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search multiple government websites for documents matching keywords

        Args:
            keywords: List of keywords to search for
            max_documents_per_site: Maximum documents per website

        Returns:
            List of matching documents
        """
        all_documents = []

        for website in self.settings.government_websites:
            try:
                self.logger.info(f"Searching government website: {website}")

                # Crawl the website
                documents = await self.crawl_government_site(
                    website,
                    max_pages=max_documents_per_site
                )

                # Filter documents by keywords
                matching_documents = []
                for doc in documents:
                    title = doc.get('title', '').lower()
                    if any(keyword.lower() in title for keyword in keywords):
                        matching_documents.append(doc)

                all_documents.extend(matching_documents)

                # Add delay between websites
                await asyncio.sleep(self.settings.crawl_delay * 2)

            except Exception as e:
                self.logger.error(f"Failed to search {website}: {e}")
                continue

        return all_documents
