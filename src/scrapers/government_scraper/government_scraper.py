"""
Main government scraper orchestrator for Indonesian government documents.
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import aiohttp
import hashlib

from .config import GovernmentScraperSettings
from .website_crawler import GovernmentWebsiteCrawler, DocumentInfo
from .api_client import GovernmentAPIClient, APIDocument
from .document_processor import GovernmentDocumentProcessor, ProcessedDocument


@dataclass
class ScrapingJob:
    """Government scraping job information."""
    job_id: str
    user_id: str
    keywords: List[str]
    sources: List[str]
    max_documents_per_keyword: int
    status: str
    progress: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ScrapingResult:
    """Government scraping result."""
    job_id: str
    total_documents: int
    keywords_processed: int
    documents: List[Dict[str, Any]]
    processing_time: float
    success_rate: float
    error_count: int


class GovernmentScraper:
    """Main orchestrator for government document scraping."""
    
    def __init__(
        self,
        settings: GovernmentScraperSettings,
        website_crawler: Optional[GovernmentWebsiteCrawler] = None,
        api_client: Optional[GovernmentAPIClient] = None,
        document_processor: Optional[GovernmentDocumentProcessor] = None,
        storage_manager=None,
        job_manager=None,
        playwright_manager=None
    ):
        self.settings = settings
        self.website_crawler = website_crawler or GovernmentWebsiteCrawler(settings, playwright_manager)
        self.api_client = api_client or GovernmentAPIClient(settings)
        self.document_processor = document_processor or GovernmentDocumentProcessor(settings)
        self.storage_manager = storage_manager
        self.job_manager = job_manager
        self.playwright_manager = playwright_manager
        self.logger = logging.getLogger(__name__)
        
        # Statistics
        self.total_documents_processed = 0
        self.total_processing_time = 0.0
        self.total_errors = 0
    
    async def scrape_government_documents(
        self,
        keywords: List[str],
        job_id: str,
        user_id: str,
        sources: List[str] = ['websites', 'apis'],
        max_documents_per_keyword: int = 20
    ) -> ScrapingResult:
        """Main government document scraping orchestration."""
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Create scraping job
            job = ScrapingJob(
                job_id=job_id,
                user_id=user_id,
                keywords=keywords,
                sources=sources,
                max_documents_per_keyword=max_documents_per_keyword,
                status='running',
                progress=0,
                created_at=datetime.utcnow().isoformat(),
                started_at=datetime.utcnow().isoformat()
            )
            
            # Update job status if job manager is available
            if self.job_manager:
                await self.job_manager.update_job_status(job_id, 'running')
            
            self.logger.info(f"Starting government document scraping job {job_id}")
            self.logger.info(f"Keywords: {keywords}")
            self.logger.info(f"Sources: {sources}")
            
            all_documents = []
            total_keywords = len(keywords)
            error_count = 0
            
            for i, keyword in enumerate(keywords):
                self.logger.info(f"Processing keyword {i+1}/{total_keywords}: {keyword}")
                
                # Update progress
                progress = int((i / total_keywords) * 100)
                if self.job_manager:
                    await self.job_manager.update_job_progress(job_id, progress)
                
                documents = []
                
                # Search websites
                if 'websites' in sources:
                    try:
                        website_docs = await self._search_government_websites(keyword)
                        documents.extend(website_docs)
                        self.logger.info(f"Found {len(website_docs)} documents from websites for keyword: {keyword}")
                    except Exception as e:
                        self.logger.error(f"Website search failed for keyword {keyword}: {e}")
                        error_count += 1
                
                # Search APIs
                if 'apis' in sources:
                    try:
                        api_docs = await self._search_government_apis(keyword)
                        documents.extend(api_docs)
                        self.logger.info(f"Found {len(api_docs)} documents from APIs for keyword: {keyword}")
                    except Exception as e:
                        self.logger.error(f"API search failed for keyword {keyword}: {e}")
                        error_count += 1
                
                # Remove duplicates
                unique_documents = self._remove_duplicates(documents)
                self.logger.info(f"Found {len(unique_documents)} unique documents for keyword: {keyword}")
                
                # Process documents
                processed_docs = []
                for doc in unique_documents[:max_documents_per_keyword]:
                    try:
                        processed_doc = await self._process_document(doc, user_id, job_id)
                        if processed_doc:
                            processed_doc['keyword'] = keyword
                            processed_docs.append(processed_doc)
                    except Exception as e:
                        self.logger.error(f"Failed to process document: {e}")
                        error_count += 1
                        continue
                
                all_documents.extend(processed_docs)
                self.logger.info(f"Processed {len(processed_docs)} documents for keyword: {keyword}")
                
                # Add delay between keywords
                await asyncio.sleep(self.settings.crawl_delay)
            
            # Calculate processing time
            processing_time = asyncio.get_event_loop().time() - start_time
            
            # Update statistics
            self.total_documents_processed += len(all_documents)
            self.total_processing_time += processing_time
            self.total_errors += error_count
            
            # Update job completion
            if self.job_manager:
                await self.job_manager.update_job_status(job_id, 'completed')
                await self.job_manager.update_job_progress(job_id, 100)
            
            # Calculate success rate
            total_attempts = len(keywords) * 2  # websites + APIs
            success_rate = ((total_attempts - error_count) / total_attempts) * 100 if total_attempts > 0 else 0
            
            result = ScrapingResult(
                job_id=job_id,
                total_documents=len(all_documents),
                keywords_processed=len(keywords),
                documents=all_documents,
                processing_time=processing_time,
                success_rate=success_rate,
                error_count=error_count
            )
            
            self.logger.info(f"Completed government document scraping job {job_id}")
            self.logger.info(f"Total documents: {len(all_documents)}")
            self.logger.info(f"Processing time: {processing_time:.2f} seconds")
            self.logger.info(f"Success rate: {success_rate:.1f}%")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Government document scraping failed for job {job_id}: {e}")
            
            if self.job_manager:
                await self.job_manager.update_job_status(job_id, 'failed', str(e))
            
            # Update statistics
            self.total_errors += 1
            
            raise
    
    async def _search_government_websites(self, keyword: str) -> List[Dict[str, Any]]:
        """Search government websites for documents."""
        
        documents = []
        
        # List of government websites to search
        government_sites = [
            'https://www.setkab.go.id',
            'https://www.kemendagri.go.id',
            'https://www.kemendikbud.go.id',
            'https://www.kemenkeu.go.id',
            'https://www.kemenlu.go.id',
            'https://www.kemenkumham.go.id',
            'https://www.kemenperin.go.id',
            'https://www.kemenkes.go.id',
            'https://www.kemenag.go.id',
            'https://www.kemenkopmk.go.id',
            'https://www.kemenpan.go.id',
            'https://www.kemenristek.go.id',
            'https://www.kemenparekraf.go.id',
            'https://www.kemenkominfo.go.id',
            'https://www.kemenko.go.id',
            'https://www.bappenas.go.id',
            'https://www.bkn.go.id',
            'https://www.bpkp.go.id',
            'https://www.bppt.go.id'
        ]
        
        for site in government_sites:
            try:
                site_documents = await self.website_crawler.crawl_government_site(site)
                
                # Filter by keyword
                filtered_docs = []
                for doc in site_documents:
                    if keyword.lower() in doc.title.lower() or keyword.lower() in (doc.description or '').lower():
                        filtered_docs.append(doc)
                
                # Convert to dictionary format
                for doc in filtered_docs:
                    documents.append({
                        'url': doc.url,
                        'title': doc.title,
                        'file_size': doc.file_size,
                        'content_type': doc.content_type,
                        'last_modified': doc.last_modified,
                        'domain': doc.domain,
                        'document_type': doc.document_type,
                        'description': doc.description,
                        'source': 'government_website',
                        'extraction_timestamp': doc.extraction_timestamp
                    })
                
            except Exception as e:
                self.logger.error(f"Failed to search {site}: {e}")
                continue
        
        return documents
    
    async def _search_government_apis(self, keyword: str) -> List[Dict[str, Any]]:
        """Search government APIs for documents."""
        
        documents = []
        
        async with self.api_client as client:
            try:
                api_documents = await client.search_multiple_apis(keyword)
                
                # Convert to dictionary format
                for doc in api_documents:
                    documents.append({
                        'url': doc.url,
                        'title': doc.title,
                        'description': doc.description,
                        'published_date': doc.published_date,
                        'source': doc.source,
                        'api_endpoint': doc.api_endpoint,
                        'metadata': doc.metadata,
                        'extraction_timestamp': doc.extraction_timestamp
                    })
                
            except Exception as e:
                self.logger.error(f"Failed to search government APIs: {e}")
        
        return documents
    
    async def _process_document(
        self,
        document: Dict[str, Any],
        user_id: str,
        job_id: str
    ) -> Optional[Dict[str, Any]]:
        """Process individual document."""
        
        try:
            # Download document if needed
            if 'url' in document and not document.get('text_content'):
                document_data = await self._download_document(document['url'])
                if document_data:
                    processed_doc = await self.document_processor.process_document(
                        document['url'],
                        document_data['content'],
                        document_data['content_type']
                    )
                    if processed_doc:
                        document.update({
                            'text_content': processed_doc.text_content,
                            'metadata': processed_doc.metadata,
                            'analysis': processed_doc.analysis,
                            'content_hash': processed_doc.content_hash,
                            'word_count': processed_doc.word_count,
                            'language': processed_doc.language,
                            'quality_score': processed_doc.quality_score
                        })
            
            # Store document as artifact if storage manager is available
            if self.storage_manager:
                artifact_id = await self._store_document(document, user_id, job_id)
                document['artifact_id'] = artifact_id
            
            return document
            
        except Exception as e:
            self.logger.error(f"Document processing failed: {e}")
            return None
    
    async def _download_document(self, url: str) -> Optional[Dict[str, Any]]:
        """Download document from URL."""
        
        try:
            headers = {'User-Agent': self.settings.user_agent}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=self.settings.api_timeout) as response:
                    if response.status == 200:
                        content = await response.read()
                        content_type = response.headers.get('content-type', '')
                        
                        return {
                            'content': content,
                            'content_type': content_type
                        }
                    else:
                        self.logger.error(f"Document download failed: {response.status}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Document download failed: {e}")
            return None
    
    async def _store_document(
        self,
        document: Dict[str, Any],
        user_id: str,
        job_id: str
    ) -> str:
        """Store document as artifact."""
        
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
            artifact_id = await self.storage_manager.create_artifact(artifact_data)
            
            # Store document in MinIO
            document_json = json.dumps(document, default=str)
            await self.storage_manager.upload_artifact(
                document_json.encode('utf-8'),
                f"{artifact_id}.json",
                "application/json",
                metadata={
                    'document_type': document.get('analysis', {}).get('document_type', ''),
                    'language': document.get('analysis', {}).get('language', ''),
                    'source': 'government',
                    'quality_score': str(document.get('quality_score', 0.0))
                },
                user_id=user_id
            )
            
            return artifact_id
            
        except Exception as e:
            self.logger.error(f"Failed to store document: {e}")
            return ""
    
    def _remove_duplicates(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate documents."""
        seen_urls = set()
        unique_documents = []
        
        for doc in documents:
            url = doc.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_documents.append(doc)
        
        return unique_documents
    
    async def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        
        try:
            if self.storage_manager:
                artifact = await self.storage_manager.get_artifact(document_id)
                if artifact:
                    return json.loads(artifact.content.decode('utf-8'))
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get document by ID: {e}")
            return None
    
    async def search_documents_by_keyword(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for documents by keyword."""
        
        try:
            # Search both websites and APIs
            website_docs = await self._search_government_websites(keyword)
            api_docs = await self._search_government_apis(keyword)
            
            # Combine and remove duplicates
            all_docs = website_docs + api_docs
            unique_docs = self._remove_duplicates(all_docs)
            
            return unique_docs[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to search documents by keyword: {e}")
            return []
    
    async def get_scraping_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        
        return {
            'total_documents_processed': self.total_documents_processed,
            'total_processing_time': self.total_processing_time,
            'total_errors': self.total_errors,
            'average_processing_time': (
                self.total_processing_time / self.total_documents_processed 
                if self.total_documents_processed > 0 else 0
            ),
            'error_rate': (
                (self.total_errors / (self.total_documents_processed + self.total_errors)) * 100
                if (self.total_documents_processed + self.total_errors) > 0 else 0
            ),
            'crawl_stats': self.website_crawler.get_crawl_stats(),
            'api_stats': await self.api_client.get_api_stats(),
            'processing_stats': self.document_processor.get_processing_stats()
        }
    
    async def validate_system(self) -> Dict[str, Any]:
        """Validate the scraping system."""
        
        validation_results = {
            'website_crawler': True,
            'api_client': True,
            'document_processor': True,
            'storage_manager': self.storage_manager is not None,
            'job_manager': self.job_manager is not None,
            'playwright_manager': self.playwright_manager is not None
        }
        
        # Validate API endpoints
        try:
            api_health = await self.api_client.validate_api_endpoints()
            validation_results['api_endpoints'] = api_health
        except Exception as e:
            validation_results['api_client'] = False
            validation_results['api_error'] = str(e)
        
        # Validate document processor
        processing_stats = self.document_processor.get_processing_stats()
        validation_results['document_processing'] = {
            'pdf_available': processing_stats['pdf_available'],
            'docx_available': processing_stats['docx_available'],
            'excel_available': processing_stats['excel_available']
        }
        
        return validation_results
