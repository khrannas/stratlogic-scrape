# Task 06: Web Scraper Implementation

## Overview
Implement a comprehensive web scraping module using Playwright with search engine integration, LLM keyword expansion, and content extraction capabilities.

## Priority: High
## Estimated Time: 4-5 days
## Dependencies: Task 01-05 (Infrastructure, Database, Storage, API, Auth)

## Checklist

### 6.1 Playwright Setup
- [ ] Install and configure Playwright
- [ ] Set up browser automation
- [ ] Configure proxy and user agents
- [ ] Implement browser pool management
- [ ] Add screenshot and video capture

### 6.2 Search Engine Integration
- [ ] Implement Google search scraping
- [ ] Implement Bing search scraping
- [ ] Implement DuckDuckGo search scraping
- [ ] Add search result parsing
- [ ] Implement rate limiting and delays

### 6.3 Content Extraction
- [ ] Implement HTML content extraction
- [ ] Add text cleaning and normalization
- [ ] Extract metadata (title, description, links)
- [ ] Implement image and media extraction
- [ ] Add content validation and filtering

### 6.4 LLM Integration
- [ ] Implement keyword expansion service
- [ ] Add content analysis and classification
- [ ] Implement content summarization
- [ ] Add language detection
- [ ] Implement content quality scoring

### 6.5 Job Management
- [ ] Create scraping job scheduler
- [ ] Implement progress tracking
- [ ] Add error handling and retry logic
- [ ] Implement job cancellation
- [ ] Add job result aggregation

## Subtasks

### Subtask 6.1.1: Playwright Configuration
```python
# src/scrapers/web_scraper/playwright_manager.py
from playwright.async_api import async_playwright, Browser, Page
import asyncio
import logging
from typing import Optional, Dict, Any
import random

class PlaywrightManager:
    def __init__(self, headless: bool = True, proxy: Optional[str] = None):
        self.headless = headless
        self.proxy = proxy
        self.logger = logging.getLogger(__name__)
        self.browser_pool = []
        self.max_browsers = 5
        
    async def get_browser(self) -> Browser:
        """Get a browser from the pool or create a new one"""
        if self.browser_pool:
            return self.browser_pool.pop()
        
        playwright = await async_playwright().start()
        
        browser = await playwright.chromium.launch(
            headless=self.headless,
            proxy={
                "server": self.proxy
            } if self.proxy else None,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu"
            ]
        )
        
        return browser
    
    async def return_browser(self, browser: Browser):
        """Return browser to the pool"""
        if len(self.browser_pool) < self.max_browsers:
            self.browser_pool.append(browser)
        else:
            await browser.close()
    
    async def create_page(self, browser: Browser) -> Page:
        """Create a new page with configured settings"""
        page = await browser.new_page()
        
        # Set user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        ]
        await page.set_extra_http_headers({
            "User-Agent": random.choice(user_agents)
        })
        
        # Set viewport
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Enable JavaScript
        await page.set_java_script_enabled(True)
        
        return page
```

### Subtask 6.1.2: Search Engine Scrapers
```python
# src/scrapers/web_scraper/search_engines.py
from typing import List, Dict, Any, Optional
import asyncio
import logging
from urllib.parse import quote_plus, urlparse
import re

class SearchEngineScraper:
    def __init__(self, playwright_manager: PlaywrightManager):
        self.playwright_manager = playwright_manager
        self.logger = logging.getLogger(__name__)
    
    async def search_google(
        self,
        query: str,
        max_results: int = 10,
        delay: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Search Google and extract results"""
        
        browser = await self.playwright_manager.get_browser()
        page = await self.playwright_manager.create_page(browser)
        
        try:
            # Construct search URL
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}"
            
            await page.goto(search_url, wait_until="networkidle")
            await asyncio.sleep(delay)
            
            # Extract search results
            results = await page.evaluate("""
                () => {
                    const results = [];
                    const elements = document.querySelectorAll('div.g');
                    
                    elements.forEach((element, index) => {
                        const titleElement = element.querySelector('h3');
                        const linkElement = element.querySelector('a');
                        const snippetElement = element.querySelector('.VwiC3b');
                        
                        if (titleElement && linkElement) {
                            results.push({
                                title: titleElement.textContent,
                                url: linkElement.href,
                                snippet: snippetElement ? snippetElement.textContent : '',
                                position: index + 1
                            });
                        }
                    });
                    
                    return results;
                }
            """)
            
            return results[:max_results]
            
        except Exception as e:
            self.logger.error(f"Google search failed: {e}")
            return []
        finally:
            await page.close()
            await self.playwright_manager.return_browser(browser)
    
    async def search_bing(
        self,
        query: str,
        max_results: int = 10,
        delay: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Search Bing and extract results"""
        
        browser = await self.playwright_manager.get_browser()
        page = await self.playwright_manager.create_page(browser)
        
        try:
            search_url = f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}"
            
            await page.goto(search_url, wait_until="networkidle")
            await asyncio.sleep(delay)
            
            results = await page.evaluate("""
                () => {
                    const results = [];
                    const elements = document.querySelectorAll('li.b_algo');
                    
                    elements.forEach((element, index) => {
                        const titleElement = element.querySelector('h2 a');
                        const snippetElement = element.querySelector('.b_caption p');
                        
                        if (titleElement) {
                            results.push({
                                title: titleElement.textContent,
                                url: titleElement.href,
                                snippet: snippetElement ? snippetElement.textContent : '',
                                position: index + 1
                            });
                        }
                    });
                    
                    return results;
                }
            """)
            
            return results[:max_results]
            
        except Exception as e:
            self.logger.error(f"Bing search failed: {e}")
            return []
        finally:
            await page.close()
            await self.playwright_manager.return_browser(browser)
    
    async def search_duckduckgo(
        self,
        query: str,
        max_results: int = 10,
        delay: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Search DuckDuckGo and extract results"""
        
        browser = await self.playwright_manager.get_browser()
        page = await self.playwright_manager.create_page(browser)
        
        try:
            search_url = f"https://duckduckgo.com/?q={quote_plus(query)}"
            
            await page.goto(search_url, wait_until="networkidle")
            await asyncio.sleep(delay)
            
            results = await page.evaluate("""
                () => {
                    const results = [];
                    const elements = document.querySelectorAll('.result');
                    
                    elements.forEach((element, index) => {
                        const titleElement = element.querySelector('.result__title a');
                        const snippetElement = element.querySelector('.result__snippet');
                        
                        if (titleElement) {
                            results.push({
                                title: titleElement.textContent,
                                url: titleElement.href,
                                snippet: snippetElement ? snippetElement.textContent : '',
                                position: index + 1
                            });
                        }
                    });
                    
                    return results;
                }
            """)
            
            return results[:max_results]
            
        except Exception as e:
            self.logger.error(f"DuckDuckGo search failed: {e}")
            return []
        finally:
            await page.close()
            await self.playwright_manager.return_browser(browser)
```

### Subtask 6.1.3: Content Extractor
```python
# src/scrapers/web_scraper/content_extractor.py
from typing import Dict, Any, Optional, List
import re
from bs4 import BeautifulSoup
import hashlib
from urllib.parse import urljoin, urlparse
import logging

class ContentExtractor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def extract_content(
        self,
        page,
        url: str,
        extract_images: bool = True,
        extract_links: bool = True
    ) -> Dict[str, Any]:
        """Extract content from a web page"""
        
        try:
            # Get page content
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract basic information
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            text_content = self._extract_text(soup)
            
            # Extract metadata
            metadata = self._extract_metadata(soup, url)
            
            # Extract images
            images = []
            if extract_images:
                images = self._extract_images(soup, url)
            
            # Extract links
            links = []
            if extract_links:
                links = self._extract_links(soup, url)
            
            # Calculate content hash
            content_hash = hashlib.sha256(text_content.encode()).hexdigest()
            
            return {
                'url': url,
                'title': title,
                'description': description,
                'text_content': text_content,
                'metadata': metadata,
                'images': images,
                'links': links,
                'content_hash': content_hash,
                'word_count': len(text_content.split()),
                'extraction_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Content extraction failed for {url}: {e}")
            return {}
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Fallback to h1
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description"""
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        return ""
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract main text content"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text from body
        body = soup.find('body')
        if body:
            text = body.get_text()
        else:
            text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract page metadata"""
        metadata = {
            'url': url,
            'domain': urlparse(url).netloc,
            'language': self._detect_language(soup),
            'author': self._extract_author(soup),
            'published_date': self._extract_published_date(soup),
            'keywords': self._extract_keywords(soup)
        }
        
        return metadata
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract images from the page"""
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # Make URL absolute
                absolute_url = urljoin(base_url, src)
                
                images.append({
                    'src': absolute_url,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', ''),
                    'width': img.get('width'),
                    'height': img.get('height')
                })
        
        return images
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract links from the page"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and not href.startswith(('#', 'javascript:', 'mailto:')):
                # Make URL absolute
                absolute_url = urljoin(base_url, href)
                
                links.append({
                    'url': absolute_url,
                    'text': link.get_text().strip(),
                    'title': link.get('title', '')
                })
        
        return links
```

### Subtask 6.1.4: LLM Keyword Expansion
```python
# src/scrapers/web_scraper/keyword_expander.py
from typing import List, Dict, Any
import openai
import logging
from src.services.llm_service import LLMService

class KeywordExpander:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.logger = logging.getLogger(__name__)
    
    async def expand_keywords(
        self,
        keywords: List[str],
        max_expansions: int = 10,
        context: str = ""
    ) -> List[str]:
        """Expand keywords using LLM"""
        
        try:
            # Create prompt for keyword expansion
            prompt = f"""
            Given the following keywords: {', '.join(keywords)}
            
            Context: {context}
            
            Please expand these keywords with related terms, synonyms, and variations that would be useful for web scraping. 
            Focus on terms that would help find relevant content.
            
            Return only the expanded keywords as a comma-separated list, without numbering or additional text.
            Maximum {max_expansions} additional keywords.
            """
            
            response = await self.llm_service.generate_text(prompt)
            
            # Parse response
            expanded_keywords = [
                keyword.strip() 
                for keyword in response.split(',') 
                if keyword.strip()
            ]
            
            # Combine original and expanded keywords
            all_keywords = list(set(keywords + expanded_keywords))
            
            return all_keywords[:max_expansions + len(keywords)]
            
        except Exception as e:
            self.logger.error(f"Keyword expansion failed: {e}")
            return keywords
    
    async def analyze_content(
        self,
        content: str,
        max_length: int = 1000
    ) -> Dict[str, Any]:
        """Analyze content using LLM"""
        
        try:
            # Truncate content if too long
            if len(content) > max_length:
                content = content[:max_length] + "..."
            
            prompt = f"""
            Analyze the following web content and provide:
            1. Main topics/themes
            2. Content type (news, blog, documentation, etc.)
            3. Language
            4. Quality score (1-10)
            5. Key entities mentioned
            6. Summary (2-3 sentences)
            
            Content: {content}
            
            Return as JSON format.
            """
            
            response = await self.llm_service.generate_text(prompt)
            
            # Parse JSON response
            import json
            analysis = json.loads(response)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Content analysis failed: {e}")
            return {}
```

### Subtask 6.1.5: Web Scraper Orchestrator
```python
# src/scrapers/web_scraper/web_scraper.py
from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime
import uuid

class WebScraper:
    def __init__(
        self,
        search_engine_scraper: SearchEngineScraper,
        content_extractor: ContentExtractor,
        keyword_expander: KeywordExpander,
        storage_manager,
        job_manager
    ):
        self.search_engine_scraper = search_engine_scraper
        self.content_extractor = content_extractor
        self.keyword_expander = keyword_expander
        self.storage_manager = storage_manager
        self.job_manager = job_manager
        self.logger = logging.getLogger(__name__)
    
    async def scrape_web_content(
        self,
        keywords: List[str],
        job_id: str,
        user_id: str,
        max_results_per_keyword: int = 10,
        search_engines: List[str] = ['google', 'bing'],
        expand_keywords: bool = True
    ) -> Dict[str, Any]:
        """Main web scraping orchestration"""
        
        try:
            # Update job status
            await self.job_manager.update_job_status(job_id, 'running')
            
            # Expand keywords if requested
            if expand_keywords:
                expanded_keywords = await self.keyword_expander.expand_keywords(keywords)
                self.logger.info(f"Expanded keywords: {expanded_keywords}")
            else:
                expanded_keywords = keywords
            
            all_results = []
            total_keywords = len(expanded_keywords)
            
            for i, keyword in enumerate(expanded_keywords):
                self.logger.info(f"Processing keyword {i+1}/{total_keywords}: {keyword}")
                
                # Update progress
                progress = int((i / total_keywords) * 100)
                await self.job_manager.update_job_progress(job_id, progress)
                
                # Search across engines
                search_results = []
                for engine in search_engines:
                    if engine == 'google':
                        results = await self.search_engine_scraper.search_google(
                            keyword, max_results_per_keyword
                        )
                    elif engine == 'bing':
                        results = await self.search_engine_scraper.search_bing(
                            keyword, max_results_per_keyword
                        )
                    elif engine == 'duckduckgo':
                        results = await self.search_engine_scraper.search_duckduckgo(
                            keyword, max_results_per_keyword
                        )
                    
                    search_results.extend(results)
                
                # Remove duplicates
                unique_results = self._remove_duplicates(search_results)
                
                # Extract content from each URL
                for result in unique_results[:max_results_per_keyword]:
                    try:
                        content = await self._extract_page_content(result['url'])
                        if content:
                            # Add keyword context
                            content['keyword'] = keyword
                            content['search_position'] = result.get('position', 0)
                            
                            # Store artifact
                            artifact_id = await self._store_artifact(content, user_id, job_id)
                            content['artifact_id'] = artifact_id
                            
                            all_results.append(content)
                    
                    except Exception as e:
                        self.logger.error(f"Failed to extract content from {result['url']}: {e}")
                        continue
                
                # Add delay between keywords
                await asyncio.sleep(2)
            
            # Update job completion
            await self.job_manager.update_job_status(job_id, 'completed')
            await self.job_manager.update_job_progress(job_id, 100)
            
            return {
                'job_id': job_id,
                'total_results': len(all_results),
                'keywords_processed': len(expanded_keywords),
                'results': all_results
            }
            
        except Exception as e:
            self.logger.error(f"Web scraping failed: {e}")
            await self.job_manager.update_job_status(job_id, 'failed', str(e))
            raise
    
    async def _extract_page_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract content from a single page"""
        
        browser = await self.playwright_manager.get_browser()
        page = await self.playwright_manager.create_page(browser)
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for content to load
            await page.wait_for_load_state("domcontentloaded")
            
            # Extract content
            content = await self.content_extractor.extract_content(page, url)
            
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to extract content from {url}: {e}")
            return None
        finally:
            await page.close()
            await self.playwright_manager.return_browser(browser)
    
    async def _store_artifact(
        self,
        content: Dict[str, Any],
        user_id: str,
        job_id: str
    ) -> str:
        """Store extracted content as artifact"""
        
        # Create artifact record
        artifact_data = {
            'job_id': job_id,
            'user_id': user_id,
            'artifact_type': 'web_page',
            'source_url': content['url'],
            'title': content['title'],
            'content_hash': content['content_hash'],
            'file_size': len(content['text_content']),
            'mime_type': 'text/html',
            'is_public': False
        }
        
        # Store in database
        artifact_id = await self.storage_manager.create_artifact(artifact_data)
        
        # Store content in MinIO
        content_bytes = content['text_content'].encode('utf-8')
        await self.storage_manager.upload_artifact(
            content_bytes,
            f"{artifact_id}.txt",
            "text/plain",
            metadata={
                'url': content['url'],
                'keyword': content.get('keyword', ''),
                'search_position': content.get('search_position', 0)
            },
            user_id=user_id
        )
        
        return artifact_id
    
    def _remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate search results"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
```

## Files to Create

1. `src/scrapers/web_scraper/__init__.py` - Web scraper package
2. `src/scrapers/web_scraper/playwright_manager.py` - Playwright browser management
3. `src/scrapers/web_scraper/search_engines.py` - Search engine scrapers
4. `src/scrapers/web_scraper/content_extractor.py` - Content extraction
5. `src/scrapers/web_scraper/keyword_expander.py` - LLM keyword expansion
6. `src/scrapers/web_scraper/web_scraper.py` - Main scraper orchestrator
7. `src/scrapers/web_scraper/config.py` - Web scraper configuration
8. `tests/scrapers/web_scraper/` - Web scraper tests

## Configuration

### Web Scraper Configuration
```python
# src/scrapers/web_scraper/config.py
from pydantic import BaseSettings
from typing import List

class WebScraperSettings(BaseSettings):
    # Playwright settings
    headless: bool = True
    max_browsers: int = 5
    page_timeout: int = 30000
    
    # Search settings
    max_results_per_keyword: int = 10
    search_delay: float = 2.0
    default_search_engines: List[str] = ['google', 'bing']
    
    # Content extraction
    max_content_length: int = 10000
    extract_images: bool = True
    extract_links: bool = True
    
    # Rate limiting
    requests_per_minute: int = 30
    delay_between_requests: float = 2.0
    
    class Config:
        env_prefix = "WEB_SCRAPER_"
```

## Testing

### Unit Tests
- [ ] Test Playwright manager
- [ ] Test search engine scrapers
- [ ] Test content extraction
- [ ] Test keyword expansion
- [ ] Test web scraper orchestration

### Integration Tests
- [ ] Test with actual websites
- [ ] Test search engine integration
- [ ] Test content storage
- [ ] Test error handling

## Documentation

- [ ] Create web scraper setup guide
- [ ] Document search engine integration
- [ ] Create content extraction guide
- [ ] Document rate limiting and best practices

## Notes

- Implement proper rate limiting to avoid being blocked
- Use rotating user agents and proxies
- Add content validation and filtering
- Implement retry logic for failed requests
- Consider implementing content deduplication
- Add support for JavaScript-heavy sites

## Next Steps

After completing this task, proceed to:
- Task 07: Paper Scraper Implementation
- Task 08: Government Document Scraper
- Task 09: Advanced Features and Optimization

## Completion Criteria

- [ ] Playwright is properly configured
- [ ] Search engine integration works
- [ ] Content extraction is functional
- [ ] LLM keyword expansion works
- [ ] Job management is implemented
- [ ] All tests are passing
- [ ] Documentation is complete
- [ ] Rate limiting and error handling work
