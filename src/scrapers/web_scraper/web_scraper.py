"""
Main web scraper orchestrator for coordinating scraping operations.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from playwright.async_api import Page
from .playwright_manager import PlaywrightManager
from .search_engines import SearchEngineScraper
from .content_extractor import ContentExtractor
from .keyword_expander import KeywordExpander
from .config import WebScraperSettings


class WebScraper:
    """Main web scraper orchestrator."""
    
    def __init__(
        self,
        settings: WebScraperSettings,
        storage_manager=None,
        job_manager=None
    ):
        self.settings = settings
        self.storage_manager = storage_manager
        self.job_manager = job_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.playwright_manager = PlaywrightManager(settings)
        self.search_engine_scraper = SearchEngineScraper(self.playwright_manager, settings)
        self.content_extractor = ContentExtractor(settings)
        self.keyword_expander = KeywordExpander(settings)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.playwright_manager.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.playwright_manager.stop()
    
    async def scrape_web_content(
        self,
        keywords: List[str],
        job_id: str,
        user_id: str,
        max_results_per_keyword: int = 10,
        search_engines: List[str] = None,
        expand_keywords: bool = True,
        analyze_content: bool = True
    ) -> Dict[str, Any]:
        """Main web scraping orchestration."""
        
        if search_engines is None:
            search_engines = self.settings.default_search_engines
        
        try:
            # Update job status
            if self.job_manager:
                await self.job_manager.update_job_status(job_id, 'running')
            
            self.logger.info(f"Starting web scraping job {job_id} for keywords: {keywords}")
            
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
                if self.job_manager:
                    progress = int((i / total_keywords) * 100)
                    await self.job_manager.update_job_progress(job_id, progress)
                
                # Search across engines
                search_results = await self.search_engine_scraper.search_multiple_engines(
                    keyword, 
                    search_engines, 
                    max_results_per_keyword
                )
                
                self.logger.info(f"Found {len(search_results)} search results for keyword: {keyword}")
                
                # Extract content from each URL
                for result in search_results[:max_results_per_keyword]:
                    try:
                        content = await self._extract_page_content(result['url'])
                        if content and not content.get('error'):
                            # Add search context
                            content['keyword'] = keyword
                            content['search_position'] = result.get('position', 0)
                            content['search_engine'] = result.get('source', 'unknown')
                            
                            # Analyze content if requested
                            if analyze_content:
                                analysis = await self._analyze_extracted_content(content)
                                content['analysis'] = analysis
                            
                            # Store artifact if storage manager is available
                            if self.storage_manager:
                                artifact_id = await self._store_artifact(content, user_id, job_id)
                                content['artifact_id'] = artifact_id
                            
                            all_results.append(content)
                            self.logger.debug(f"Successfully extracted content from {result['url']}")
                        else:
                            self.logger.warning(f"Failed to extract content from {result['url']}")
                    
                    except Exception as e:
                        self.logger.error(f"Failed to process {result['url']}: {e}")
                        continue
                
                # Add delay between keywords
                await asyncio.sleep(self.settings.delay_between_requests)
            
            # Update job completion
            if self.job_manager:
                await self.job_manager.update_job_status(job_id, 'completed')
                await self.job_manager.update_job_progress(job_id, 100)
            
            self.logger.info(f"Web scraping job {job_id} completed. Total results: {len(all_results)}")
            
            return {
                'job_id': job_id,
                'total_results': len(all_results),
                'keywords_processed': len(expanded_keywords),
                'search_engines_used': search_engines,
                'results': all_results,
                'completion_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Web scraping failed for job {job_id}: {e}")
            if self.job_manager:
                await self.job_manager.update_job_status(job_id, 'failed', str(e))
            raise
    
    async def _extract_page_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract content from a single page."""
        
        browser = await self.playwright_manager.get_browser()
        page = await self.playwright_manager.create_page(browser)
        
        try:
            self.logger.debug(f"Extracting content from: {url}")
            
            # Navigate to page
            response = await page.goto(url, wait_until="networkidle", timeout=self.settings.page_timeout)
            
            if not response or response.status >= 400:
                self.logger.warning(f"Failed to load {url}: HTTP {response.status if response else 'unknown'}")
                return None
            
            # Wait for content to load
            await page.wait_for_load_state("domcontentloaded")
            
            # Extract content
            content = await self.content_extractor.extract_content(
                page, 
                url,
                extract_images=self.settings.extract_images,
                extract_links=self.settings.extract_links
            )
            
            # Calculate content score
            content['content_score'] = self.content_extractor.calculate_content_score(content)
            
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to extract content from {url}: {e}")
            return None
        finally:
            await page.close()
            await self.playwright_manager.return_browser(browser)
    
    async def _analyze_extracted_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze extracted content using LLM."""
        try:
            # Analyze content
            analysis = await self.keyword_expander.analyze_content(
                content.get('text_content', ''),
                max_length=1000
            )
            
            # Classify content
            classification = await self.keyword_expander.classify_content(
                content.get('title', ''),
                content.get('description', ''),
                content.get('text_content', '')
            )
            
            # Extract key phrases
            key_phrases = await self.keyword_expander.extract_key_phrases(
                content.get('text_content', ''),
                max_phrases=10
            )
            
            return {
                'analysis': analysis,
                'classification': classification,
                'key_phrases': key_phrases,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Content analysis failed: {e}")
            return {
                'analysis': {},
                'classification': {},
                'key_phrases': [],
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    async def _store_artifact(
        self,
        content: Dict[str, Any],
        user_id: str,
        job_id: str
    ) -> str:
        """Store extracted content as artifact."""
        
        if not self.storage_manager:
            return str(uuid.uuid4())  # Return dummy ID if no storage manager
        
        try:
            # Create artifact record
            artifact_data = {
                'job_id': job_id,
                'user_id': user_id,
                'artifact_type': 'web_page',
                'source_url': content['url'],
                'title': content.get('title', ''),
                'content_hash': content.get('content_hash', ''),
                'file_size': len(content.get('text_content', '')),
                'mime_type': 'text/html',
                'is_public': False,
                'metadata': {
                    'keyword': content.get('keyword', ''),
                    'search_position': content.get('search_position', 0),
                    'search_engine': content.get('search_engine', ''),
                    'content_score': content.get('content_score', 0),
                    'word_count': content.get('word_count', 0),
                    'image_count': content.get('image_count', 0),
                    'link_count': content.get('link_count', 0)
                }
            }
            
            # Store in database
            artifact_id = await self.storage_manager.create_artifact(artifact_data)
            
            # Store content in MinIO
            content_bytes = content.get('text_content', '').encode('utf-8')
            await self.storage_manager.upload_artifact(
                content_bytes,
                f"{artifact_id}.txt",
                "text/plain",
                metadata={
                    'url': content['url'],
                    'keyword': content.get('keyword', ''),
                    'search_position': content.get('search_position', 0),
                    'content_score': content.get('content_score', 0)
                },
                user_id=user_id
            )
            
            return artifact_id
            
        except Exception as e:
            self.logger.error(f"Failed to store artifact: {e}")
            return str(uuid.uuid4())  # Return dummy ID on error
    
    async def scrape_single_url(
        self,
        url: str,
        user_id: str = None,
        analyze_content: bool = True
    ) -> Dict[str, Any]:
        """Scrape content from a single URL."""
        
        try:
            self.logger.info(f"Scraping single URL: {url}")
            
            content = await self._extract_page_content(url)
            if not content:
                return {'error': 'Failed to extract content', 'url': url}
            
            # Analyze content if requested
            if analyze_content:
                analysis = await self._analyze_extracted_content(content)
                content['analysis'] = analysis
            
            # Store artifact if storage manager is available
            if self.storage_manager and user_id:
                artifact_id = await self._store_artifact(content, user_id, str(uuid.uuid4()))
                content['artifact_id'] = artifact_id
            
            return content
            
        except Exception as e:
            self.logger.error(f"Single URL scraping failed for {url}: {e}")
            return {'error': str(e), 'url': url}
    
    async def get_scraping_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        pool_status = self.playwright_manager.get_pool_status()
        
        return {
            'browser_pool': pool_status,
            'settings': {
                'max_results_per_keyword': self.settings.max_results_per_keyword,
                'search_delay': self.settings.search_delay,
                'default_search_engines': self.settings.default_search_engines,
                'requests_per_minute': self.settings.requests_per_minute
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def validate_search_engines(self) -> Dict[str, bool]:
        """Validate that search engines are accessible."""
        results = {}
        
        test_query = "test query"
        
        try:
            # Test Google
            google_results = await self.search_engine_scraper.search_google(test_query, 1)
            results['google'] = len(google_results) > 0
        except Exception as e:
            self.logger.error(f"Google validation failed: {e}")
            results['google'] = False
        
        try:
            # Test Bing
            bing_results = await self.search_engine_scraper.search_bing(test_query, 1)
            results['bing'] = len(bing_results) > 0
        except Exception as e:
            self.logger.error(f"Bing validation failed: {e}")
            results['bing'] = False
        
        try:
            # Test DuckDuckGo
            ddg_results = await self.search_engine_scraper.search_duckduckgo(test_query, 1)
            results['duckduckgo'] = len(ddg_results) > 0
        except Exception as e:
            self.logger.error(f"DuckDuckGo validation failed: {e}")
            results['duckduckgo'] = False
        
        return results
