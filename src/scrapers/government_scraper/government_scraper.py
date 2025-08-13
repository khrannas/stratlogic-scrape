import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from .website_crawler import GovernmentWebsiteCrawler
from .api_client import GovernmentAPIClient
from .document_processor import GovernmentDocumentProcessor
from .config import government_scraper_settings
from src.services.artifact_service import artifact_service
from src.services.job_service import job_service
from src.storage.artifact_storage import ArtifactStorage

class GovernmentScraper:
    """
    Main government document scraper orchestrator
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = government_scraper_settings

        # Initialize components
        self.website_crawler = GovernmentWebsiteCrawler()
        self.api_client = GovernmentAPIClient()
        self.document_processor = GovernmentDocumentProcessor()
        self.artifact_storage = ArtifactStorage()

        self.logger.info("GovernmentScraper initialized")

    async def scrape_government_documents(
        self,
        keywords: List[str],
        job_id: str,
        user_id: str,
        sources: List[str] = ['websites', 'apis'],
        max_documents_per_keyword: int = 20,
        process_documents: bool = True,
        analyze_content: bool = True
    ) -> Dict[str, Any]:
        """
        Main government document scraping orchestration

        Args:
            keywords: List of keywords to search for
            job_id: Job identifier
            user_id: User identifier
            sources: List of sources to search ('websites', 'apis')
            max_documents_per_keyword: Maximum documents per keyword
            process_documents: Whether to process document content
            analyze_content: Whether to analyze content

        Returns:
            Dictionary containing scraping results
        """
        try:
            # Update job status
            await self._update_job_status(job_id, 'running')

            self.logger.info(f"Starting government document scraping for keywords: {keywords}")

            all_documents = []
            total_keywords = len(keywords)

            for i, keyword in enumerate(keywords):
                self.logger.info(f"Processing keyword {i+1}/{total_keywords}: {keyword}")

                # Update progress
                progress = int((i / total_keywords) * 50)  # First 50% for search
                await self._update_job_progress(job_id, progress)

                documents = []

                # Search websites
                if 'websites' in sources:
                    website_docs = await self._search_government_websites(keyword)
                    documents.extend(website_docs)

                # Search APIs
                if 'apis' in sources:
                    api_docs = await self._search_government_apis(keyword)
                    documents.extend(api_docs)

                # Remove duplicates
                unique_documents = self._remove_duplicates(documents)

                # Process documents
                processed_docs = []
                for j, doc in enumerate(unique_documents[:max_documents_per_keyword]):
                    try:
                        processed_doc = await self._process_document(
                            doc, process_documents, analyze_content, user_id, job_id
                        )
                        if processed_doc:
                            processed_doc['keyword'] = keyword
                            processed_docs.append(processed_doc)

                    except Exception as e:
                        self.logger.error(f"Failed to process document: {e}")
                        continue

                all_documents.extend(processed_docs)

                # Add delay between keywords
                await asyncio.sleep(3)

            # Update job completion
            await self._update_job_progress(job_id, 100)
            await self._update_job_status(job_id, 'completed')

            result = {
                'job_id': job_id,
                'keywords': keywords,
                'total_documents_found': len(all_documents),
                'sources_searched': sources,
                'documents': all_documents,
                'completed_at': datetime.now().isoformat()
            }

            self.logger.info(f"Government document scraping completed. Found {len(all_documents)} documents")
            return result

        except Exception as e:
            self.logger.error(f"Government document scraping failed: {e}")
            await self._update_job_status(job_id, 'failed')
            raise

    async def _search_government_websites(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search government websites for documents

        Args:
            keyword: Search keyword

        Returns:
            List of document dictionaries
        """
        try:
            async with self.website_crawler as crawler:
                documents = await crawler.search_government_websites(
                    [keyword],
                    max_documents_per_site=10
                )

                # Filter by keyword
                filtered_docs = []
                for doc in documents:
                    title = doc.get('title', '').lower()
                    if keyword.lower() in title:
                        filtered_docs.append(doc)

                return filtered_docs

        except Exception as e:
            self.logger.error(f"Website search failed for keyword {keyword}: {e}")
            return []

    async def _search_government_apis(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search government APIs for documents

        Args:
            keyword: Search keyword

        Returns:
            List of document dictionaries
        """
        try:
            async with self.api_client as client:
                documents = await client.search_government_apis(
                    [keyword],
                    max_results_per_api=10
                )

                return documents

        except Exception as e:
            self.logger.error(f"API search failed for keyword {keyword}: {e}")
            return []

    async def _process_document(
        self,
        document: Dict[str, Any],
        process_documents: bool,
        analyze_content: bool,
        user_id: str,
        job_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process individual document

        Args:
            document: Document data
            process_documents: Whether to process document content
            analyze_content: Whether to analyze content
            user_id: User identifier
            job_id: Job identifier

        Returns:
            Processed document or None if failed
        """
        try:
            # Process document content if requested
            if process_documents and document.get('url'):
                async with self.document_processor as processor:
                    processed_doc = await processor.process_document(document['url'])
                    if processed_doc:
                        document.update(processed_doc)

            # Store document as artifact
            artifact_id = await self._store_document(document, user_id, job_id)
            document['artifact_id'] = artifact_id

            return document

        except Exception as e:
            self.logger.error(f"Document processing failed: {e}")
            return None

    async def _store_document(
        self,
        document: Dict[str, Any],
        user_id: str,
        job_id: str
    ) -> str:
        """
        Store document as artifact

        Args:
            document: Document data
            user_id: User identifier
            job_id: Job identifier

        Returns:
            Artifact ID
        """
        try:
            # Create artifact record
            artifact_data = {
                'job_id': job_id,
                'user_id': user_id,
                'artifact_type': 'government_document',
                'source_url': document.get('url', ''),
                'title': document.get('title', ''),
                'content_hash': document.get('content_hash', ''),
                'file_size': len(document.get('text_content', '')),
                'mime_type': 'text/plain',
                'is_public': False
            }

            # Store in database
            artifact_id = await artifact_service.create_artifact(artifact_data)

            # Store document in MinIO
            document_json = json.dumps(document, default=str, ensure_ascii=False)
            await self.artifact_storage.upload_artifact(
                document_json.encode('utf-8'),
                f"{artifact_id}.json",
                "application/json",
                metadata={
                    'document_type': document.get('analysis', {}).get('document_type', ''),
                    'language': document.get('analysis', {}).get('language', ''),
                    'source': 'government',
                    'keyword': document.get('keyword', '')
                },
                user_id=user_id
            )

            return artifact_id

        except Exception as e:
            self.logger.error(f"Document storage failed: {e}")
            return ""

    def _remove_duplicates(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate documents

        Args:
            documents: List of documents

        Returns:
            List of unique documents
        """
        seen_urls = set()
        unique_documents = []

        for doc in documents:
            url = doc.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_documents.append(doc)

        return unique_documents

    async def _update_job_status(self, job_id: str, status: str):
        """Update job status"""
        try:
            await job_service.update_job_status(job_id, status)
        except Exception as e:
            self.logger.error(f"Error updating job status: {e}")

    async def _update_job_progress(self, job_id: str, progress: int):
        """Update job progress"""
        try:
            await job_service.update_job_progress(job_id, progress)
        except Exception as e:
            self.logger.error(f"Error updating job progress: {e}")

    async def search_specific_website(
        self,
        website_url: str,
        keywords: List[str],
        max_pages: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search a specific government website

        Args:
            website_url: URL of the government website
            keywords: List of keywords to search for
            max_pages: Maximum pages to crawl

        Returns:
            List of matching documents
        """
        try:
            async with self.website_crawler as crawler:
                documents = await crawler.crawl_government_site(
                    website_url,
                    max_pages=max_pages
                )

                # Filter by keywords
                matching_documents = []
                for doc in documents:
                    title = doc.get('title', '').lower()
                    if any(keyword.lower() in title for keyword in keywords):
                        matching_documents.append(doc)

                return matching_documents

        except Exception as e:
            self.logger.error(f"Specific website search failed: {e}")
            return []

    async def search_specific_api(
        self,
        api_endpoint: str,
        keywords: List[str],
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search a specific government API

        Args:
            api_endpoint: API endpoint URL
            keywords: List of keywords to search for
            max_results: Maximum results to return

        Returns:
            List of matching documents
        """
        try:
            async with self.api_client as client:
                documents = await client.search_government_apis(
                    keywords,
                    max_results_per_api=max_results
                )

                return documents

        except Exception as e:
            self.logger.error(f"Specific API search failed: {e}")
            return []

    async def check_services_health(self) -> Dict[str, bool]:
        """
        Check health of all government scraping services

        Returns:
            Dictionary with service health status
        """
        try:
            health_status = {
                'website_crawler': True,  # Basic health check
                'api_client': True,  # Basic health check
                'document_processor': True,  # Basic health check
                'government_apis': {}
            }

            # Check government APIs health
            async with self.api_client as client:
                api_health = await client.check_all_apis_health()
                health_status['government_apis'] = api_health

            return health_status

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                'website_crawler': False,
                'api_client': False,
                'document_processor': False,
                'government_apis': {}
            }

    async def get_document_by_url(self, document_url: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by URL

        Args:
            document_url: URL of the document

        Returns:
            Document data or None if not found
        """
        try:
            async with self.document_processor as processor:
                document = await processor.process_document(document_url)
                return document

        except Exception as e:
            self.logger.error(f"Failed to get document by URL: {e}")
            return None
