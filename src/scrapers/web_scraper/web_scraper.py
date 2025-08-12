from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime
import uuid
from urllib.parse import urlparse

from .playwright_manager import PlaywrightManager
from .search_engines import SearchEngineScraper
from .content_extractor import ContentExtractor
from src.services.llm_service import llm_service
from src.services.artifact_service import artifact_service
from src.services.job_service import job_service
from src.storage.artifact_storage import ArtifactStorage
from src.core.database import get_db

class WebScraper:
    """
    Main web scraper orchestrator
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.playwright_manager = PlaywrightManager()
        self.search_engine_scraper = SearchEngineScraper(self.playwright_manager)
        self.content_extractor = ContentExtractor()
        self.artifact_storage = ArtifactStorage()

        self.logger.info("WebScraper initialized")

    async def scrape_web_content(
        self,
        keywords: List[str],
        job_id: str,
        user_id: str,
        max_results_per_keyword: int = 10,
        search_engines: List[str] = ['google', 'bing'],
        expand_keywords: bool = True,
        extract_images: bool = True,
        extract_links: bool = True
    ) -> Dict[str, Any]:
        """Main web scraping orchestration"""

        try:
            # Update job status
            await self._update_job_status(job_id, 'running')

            # Expand keywords if requested
            if expand_keywords:
                expanded_keywords = await llm_service.expand_keywords(keywords)
                self.logger.info(f"Expanded keywords: {expanded_keywords}")
            else:
                expanded_keywords = keywords

            all_results = []
            total_keywords = len(expanded_keywords)

            for i, keyword in enumerate(expanded_keywords):
                self.logger.info(f"Processing keyword {i+1}/{total_keywords}: {keyword}")

                # Update progress
                progress = int((i / total_keywords) * 100)
                await self._update_job_progress(job_id, progress)

                # Search across engines
                search_results = await self.search_engine_scraper.search_all_engines(
                    keyword, max_results_per_keyword, search_engines
                )

                # Remove duplicates
                unique_results = self._remove_duplicates(search_results)

                # Extract content from each URL
                for result in unique_results[:max_results_per_keyword]:
                    try:
                        content = await self._extract_page_content(
                            result['url'], extract_images, extract_links
                        )
                        if content and self.content_extractor.validate_content(content):
                            # Add keyword context
                            content['keyword'] = keyword
                            content['search_position'] = result.get('position', 0)
                            content['search_source'] = result.get('source', 'unknown')

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
            await self._update_job_status(job_id, 'completed')
            await self._update_job_progress(job_id, 100)

            return {
                'job_id': job_id,
                'total_results': len(all_results),
                'keywords_processed': len(expanded_keywords),
                'results': all_results
            }

        except Exception as e:
            self.logger.error(f"Web scraping failed: {e}")
            await self._update_job_status(job_id, 'failed', str(e))
            raise

    async def _extract_page_content(
        self,
        url: str,
        extract_images: bool = True,
        extract_links: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Extract content from a single page"""

        browser = await self.playwright_manager.get_browser()
        page = await self.playwright_manager.create_page(browser)

        try:
            # Navigate to page
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await self.playwright_manager.wait_for_load(page)

            # Extract content
            content = await self.content_extractor.extract_content(
                page, url, extract_images, extract_links
            )

            # Analyze content with LLM if available
            if content and content.get('text_content'):
                try:
                    analysis = await llm_service.analyze_content(content['text_content'])
                    content['llm_analysis'] = analysis
                except Exception as e:
                    self.logger.warning(f"LLM analysis failed: {e}")

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

        try:
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
            db = next(get_db())
            artifact = artifact_service.create_artifact(db, artifact_in=artifact_data)
            artifact_id = str(artifact.id)

            # Store content in MinIO
            content_bytes = content['text_content'].encode('utf-8')
            metadata = {
                'url': content['url'],
                'keyword': content.get('keyword', ''),
                'search_position': str(content.get('search_position', 0)),
                'search_source': content.get('search_source', 'unknown'),
                'word_count': str(content.get('word_count', 0)),
                'extraction_timestamp': content.get('extraction_timestamp', '')
            }

            await self.artifact_storage.upload_artifact(
                content_bytes,
                f"{artifact_id}.txt",
                "text/plain",
                metadata,
                user_id
            )

            self.logger.info(f"Stored artifact {artifact_id} for URL: {content['url']}")
            return artifact_id

        except Exception as e:
            self.logger.error(f"Failed to store artifact: {e}")
            raise

    async def _update_job_status(self, job_id: str, status: str, error_message: str = None):
        """Update job status in database"""
        try:
            db = next(get_db())
            job = job_service.get_job(db, job_id=uuid.UUID(job_id))
            if job:
                job.status = status
                if error_message:
                    job.error_message = error_message
                db.commit()
        except Exception as e:
            self.logger.error(f"Failed to update job status: {e}")

    async def _update_job_progress(self, job_id: str, progress: int):
        """Update job progress in database"""
        try:
            db = next(get_db())
            job = job_service.get_job(db, job_id=uuid.UUID(job_id))
            if job:
                job.progress = progress
                db.commit()
        except Exception as e:
            self.logger.error(f"Failed to update job progress: {e}")

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

    async def scrape_single_url(
        self,
        url: str,
        user_id: str,
        job_id: str,
        extract_images: bool = True,
        extract_links: bool = True
    ) -> Dict[str, Any]:
        """Scrape a single URL"""

        try:
            # Validate URL
            if not self._validate_url(url):
                raise ValueError(f"Invalid URL: {url}")

            # Extract content
            content = await self._extract_page_content(url, extract_images, extract_links)

            if not content:
                raise ValueError(f"Failed to extract content from {url}")

            # Store artifact
            artifact_id = await self._store_artifact(content, user_id, job_id)
            content['artifact_id'] = artifact_id

            return {
                'url': url,
                'artifact_id': artifact_id,
                'content': content
            }

        except Exception as e:
            self.logger.error(f"Single URL scraping failed for {url}: {e}")
            raise

    def _validate_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in ['http', 'https'] and
                parsed.netloc and
                len(parsed.netloc) > 0
            )
        except Exception:
            return False

    async def get_scraping_stats(self) -> Dict[str, Any]:
        """Get scraping statistics"""
        return {
            'playwright_pool_status': self.playwright_manager.get_pool_status(),
            'search_stats': self.search_engine_scraper.get_search_stats(),
            'llm_provider_info': llm_service.get_provider_info(),
            'timestamp': datetime.utcnow().isoformat()
        }

    async def cleanup(self):
        """Cleanup resources"""
        await self.playwright_manager.stop()
        self.logger.info("WebScraper cleanup completed")

# Create singleton instance
web_scraper = WebScraper()
