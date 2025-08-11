"""
Main paper scraper orchestrator for comprehensive academic paper scraping and analysis.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
import os
import tempfile
from dataclasses import dataclass, asdict
import json


@dataclass
class ScrapingJob:
    """Paper scraping job configuration."""
    job_id: str
    user_id: str
    queries: List[str]
    sources: List[str]  # ['arxiv', 'crossref', 'semantic_scholar']
    max_results_per_query: int
    download_pdfs: bool
    analyze_content: bool
    extract_citations: bool
    parallel_processing: bool
    created_at: datetime
    status: str = "pending"
    progress: int = 0
    error_message: Optional[str] = None


@dataclass
class ScrapingResult:
    """Result of paper scraping operation."""
    job_id: str
    total_papers_found: int
    papers_processed: int
    papers_analyzed: int
    papers_downloaded: int
    total_processing_time: float
    results: List[Dict[str, Any]]
    errors: List[str]
    created_at: datetime


class PaperScraper:
    """Main orchestrator for paper scraping operations."""
    
    def __init__(
        self,
        config,
        arxiv_client,
        grobid_client,
        crossref_client,
        content_analyzer,
        storage_manager=None,
        job_manager=None
    ):
        self.config = config
        self.arxiv_client = arxiv_client
        self.grobid_client = grobid_client
        self.crossref_client = crossref_client
        self.content_analyzer = content_analyzer
        self.storage_manager = storage_manager
        self.job_manager = job_manager
        self.logger = logging.getLogger(__name__)
        
        # Semaphores for rate limiting
        self.arxiv_semaphore = asyncio.Semaphore(self.config.max_concurrent_downloads)
        self.analysis_semaphore = asyncio.Semaphore(self.config.max_concurrent_analysis)
    
    async def scrape_papers(
        self,
        queries: List[str],
        user_id: str,
        sources: List[str] = None,
        max_results_per_query: int = None,
        download_pdfs: bool = None,
        analyze_content: bool = None,
        extract_citations: bool = None,
        parallel_processing: bool = None
    ) -> ScrapingResult:
        """
        Main method to scrape papers based on queries.
        
        Args:
            queries: List of search queries
            user_id: User ID for the scraping job
            sources: List of sources to search ('arxiv', 'crossref', 'semantic_scholar')
            max_results_per_query: Maximum results per query
            download_pdfs: Whether to download PDFs
            analyze_content: Whether to analyze content with LLM
            extract_citations: Whether to extract citations
            parallel_processing: Whether to use parallel processing
            
        Returns:
            ScrapingResult with all findings
        """
        start_time = datetime.utcnow()
        
        # Set defaults
        if sources is None:
            sources = ['arxiv', 'crossref']
        if max_results_per_query is None:
            max_results_per_query = self.config.arxiv_max_results
        if download_pdfs is None:
            download_pdfs = self.config.extract_pdfs
        if analyze_content is None:
            analyze_content = self.config.analyze_content
        if extract_citations is None:
            extract_citations = self.config.extract_citations
        if parallel_processing is None:
            parallel_processing = self.config.parallel_processing
        
        # Create job
        job_id = str(uuid.uuid4())
        job = ScrapingJob(
            job_id=job_id,
            user_id=user_id,
            queries=queries,
            sources=sources,
            max_results_per_query=max_results_per_query,
            download_pdfs=download_pdfs,
            analyze_content=analyze_content,
            extract_citations=extract_citations,
            parallel_processing=parallel_processing,
            created_at=start_time
        )
        
        self.logger.info(f"Starting paper scraping job {job_id} with {len(queries)} queries")
        
        try:
            # Update job status
            if self.job_manager:
                await self.job_manager.update_job_status(job_id, "running")
            
            # Collect papers from all sources
            all_papers = []
            errors = []
            
            for i, query in enumerate(queries):
                self.logger.info(f"Processing query {i+1}/{len(queries)}: {query}")
                
                # Update progress
                progress = int((i / len(queries)) * 50)  # First 50% for collection
                if self.job_manager:
                    await self.job_manager.update_job_progress(job_id, progress)
                
                # Search across sources
                query_papers = []
                for source in sources:
                    try:
                        if source == 'arxiv':
                            papers = await self.arxiv_client.search_papers(
                                query, max_results_per_query
                            )
                            for paper in papers:
                                paper['source'] = 'arxiv'
                                paper['query'] = query
                        elif source == 'crossref':
                            papers = await self.crossref_client.search_papers(
                                query, max_results_per_query
                            )
                            for paper in papers:
                                paper['source'] = 'crossref'
                                paper['query'] = query
                        else:
                            self.logger.warning(f"Unknown source: {source}")
                            continue
                        
                        query_papers.extend(papers)
                        
                    except Exception as e:
                        error_msg = f"Failed to search {source} for query '{query}': {e}"
                        self.logger.error(error_msg)
                        errors.append(error_msg)
                
                # Remove duplicates based on content hash
                unique_papers = self._remove_duplicates(query_papers)
                all_papers.extend(unique_papers)
                
                # Add delay between queries
                await asyncio.sleep(self.config.arxiv_delay_seconds)
            
            self.logger.info(f"Found {len(all_papers)} unique papers")
            
            # Process papers (download, analyze, etc.)
            processed_papers = []
            papers_processed = 0
            papers_analyzed = 0
            papers_downloaded = 0
            
            if parallel_processing:
                # Process papers in parallel
                processing_tasks = []
                for paper in all_papers:
                    task = self._process_paper(
                        paper, job, user_id, download_pdfs, analyze_content, extract_citations
                    )
                    processing_tasks.append(task)
                
                # Execute tasks with semaphore limiting
                results = await asyncio.gather(*processing_tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        errors.append(f"Paper processing failed: {result}")
                    elif result:
                        processed_papers.append(result)
                        papers_processed += 1
                        if result.get('analysis'):
                            papers_analyzed += 1
                        if result.get('pdf_path'):
                            papers_downloaded += 1
            else:
                # Process papers sequentially
                for i, paper in enumerate(all_papers):
                    try:
                        # Update progress
                        progress = 50 + int((i / len(all_papers)) * 50)  # Second 50% for processing
                        if self.job_manager:
                            await self.job_manager.update_job_progress(job_id, progress)
                        
                        processed_paper = await self._process_paper(
                            paper, job, user_id, download_pdfs, analyze_content, extract_citations
                        )
                        
                        if processed_paper:
                            processed_papers.append(processed_paper)
                            papers_processed += 1
                            if processed_paper.get('analysis'):
                                papers_analyzed += 1
                            if processed_paper.get('pdf_path'):
                                papers_downloaded += 1
                    
                    except Exception as e:
                        error_msg = f"Failed to process paper {paper.get('title', 'Unknown')}: {e}"
                        self.logger.error(error_msg)
                        errors.append(error_msg)
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            # Create result
            result = ScrapingResult(
                job_id=job_id,
                total_papers_found=len(all_papers),
                papers_processed=papers_processed,
                papers_analyzed=papers_analyzed,
                papers_downloaded=papers_downloaded,
                total_processing_time=processing_time,
                results=processed_papers,
                errors=errors,
                created_at=end_time
            )
            
            # Update job completion
            if self.job_manager:
                await self.job_manager.update_job_status(job_id, "completed")
                await self.job_manager.update_job_progress(job_id, 100)
            
            self.logger.info(f"Paper scraping job {job_id} completed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Paper scraping job {job_id} failed: {e}"
            self.logger.error(error_msg)
            
            # Update job failure
            if self.job_manager:
                await self.job_manager.update_job_status(job_id, "failed", str(e))
            
            # Return partial result
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            return ScrapingResult(
                job_id=job_id,
                total_papers_found=0,
                papers_processed=0,
                papers_analyzed=0,
                papers_downloaded=0,
                total_processing_time=processing_time,
                results=[],
                errors=[error_msg],
                created_at=end_time
            )
    
    async def _process_paper(
        self,
        paper: Dict[str, Any],
        job: ScrapingJob,
        user_id: str,
        download_pdfs: bool,
        analyze_content: bool,
        extract_citations: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single paper (download, analyze, store).
        
        Args:
            paper: Paper metadata
            job: Scraping job configuration
            user_id: User ID
            download_pdfs: Whether to download PDF
            analyze_content: Whether to analyze content
            extract_citations: Whether to extract citations
            
        Returns:
            Processed paper data
        """
        try:
            processed_paper = paper.copy()
            
            # Download PDF if requested and available
            if download_pdfs and paper.get('source') == 'arxiv' and paper.get('arxiv_id'):
                async with self.arxiv_semaphore:
                    pdf_path = await self.arxiv_client.download_paper_pdf(paper['arxiv_id'])
                    if pdf_path:
                        processed_paper['pdf_path'] = pdf_path
                        
                        # Extract content using Grobid
                        if self.grobid_client:
                            grobid_content = await self.grobid_client.extract_pdf_content(pdf_path)
                            if grobid_content:
                                processed_paper['grobid_content'] = grobid_content
                            
                            # Extract citations if requested
                            if extract_citations:
                                citations = await self.grobid_client.extract_citations(pdf_path)
                                processed_paper['citations'] = citations
            
            # Analyze content if requested
            if analyze_content:
                async with self.analysis_semaphore:
                    analysis = await self.content_analyzer.analyze_paper(
                        processed_paper,
                        include_citations=extract_citations,
                        include_recommendations=True
                    )
                    if analysis:
                        processed_paper['analysis'] = asdict(analysis)
            
            # Store paper if storage manager is available
            if self.storage_manager:
                artifact_id = await self._store_paper(processed_paper, user_id, job.job_id)
                processed_paper['artifact_id'] = artifact_id
            
            return processed_paper
            
        except Exception as e:
            self.logger.error(f"Failed to process paper {paper.get('title', 'Unknown')}: {e}")
            return None
    
    async def _store_paper(
        self,
        paper: Dict[str, Any],
        user_id: str,
        job_id: str
    ) -> Optional[str]:
        """
        Store paper data and files in storage.
        
        Args:
            paper: Paper data to store
            user_id: User ID
            job_id: Job ID
            
        Returns:
            Artifact ID if stored successfully
        """
        try:
            # Create artifact record
            artifact_data = {
                'job_id': job_id,
                'user_id': user_id,
                'artifact_type': 'academic_paper',
                'source_url': paper.get('pdf_url', ''),
                'title': paper.get('title', ''),
                'content_hash': paper.get('content_hash', ''),
                'file_size': len(str(paper)),
                'mime_type': 'application/json',
                'is_public': False
            }
            
            # Store metadata
            artifact_id = await self.storage_manager.create_artifact(artifact_data)
            
            # Store paper data as JSON
            paper_json = json.dumps(paper, default=str).encode('utf-8')
            await self.storage_manager.upload_artifact(
                paper_json,
                f"{artifact_id}.json",
                "application/json",
                metadata={
                    'source': paper.get('source', ''),
                    'query': paper.get('query', ''),
                    'arxiv_id': paper.get('arxiv_id', ''),
                    'doi': paper.get('doi', '')
                },
                user_id=user_id
            )
            
            # Store PDF if available
            if paper.get('pdf_path') and os.path.exists(paper['pdf_path']):
                with open(paper['pdf_path'], 'rb') as f:
                    pdf_data = f.read()
                
                await self.storage_manager.upload_artifact(
                    pdf_data,
                    f"{artifact_id}.pdf",
                    "application/pdf",
                    metadata={
                        'source': paper.get('source', ''),
                        'arxiv_id': paper.get('arxiv_id', ''),
                        'doi': paper.get('doi', '')
                    },
                    user_id=user_id
                )
            
            return artifact_id
            
        except Exception as e:
            self.logger.error(f"Failed to store paper: {e}")
            return None
    
    def _remove_duplicates(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate papers based on content hash.
        
        Args:
            papers: List of papers
            
        Returns:
            List of unique papers
        """
        seen_hashes = set()
        unique_papers = []
        
        for paper in papers:
            content_hash = paper.get('content_hash')
            if content_hash and content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_papers.append(paper)
            elif not content_hash:
                # If no hash, use title as fallback
                title = paper.get('title', '')
                if title and title not in seen_hashes:
                    seen_hashes.add(title)
                    unique_papers.append(paper)
        
        return unique_papers
    
    async def get_paper_by_id(
        self,
        paper_id: str,
        source: str = 'arxiv'
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific paper by ID.
        
        Args:
            paper_id: Paper ID (arXiv ID or DOI)
            source: Source of the paper ('arxiv' or 'crossref')
            
        Returns:
            Paper data or None if not found
        """
        try:
            if source == 'arxiv':
                return await self.arxiv_client.get_paper_by_id(paper_id)
            elif source == 'crossref':
                return await self.crossref_client.get_paper_by_doi(paper_id)
            else:
                self.logger.error(f"Unknown source: {source}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get paper {paper_id} from {source}: {e}")
            return None
    
    async def get_paper_recommendations(
        self,
        paper_id: str,
        source: str = 'arxiv',
        max_recommendations: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get paper recommendations based on a specific paper.
        
        Args:
            paper_id: Paper ID
            source: Source of the paper
            max_recommendations: Maximum number of recommendations
            
        Returns:
            List of recommended papers
        """
        try:
            if source == 'arxiv':
                return await self.arxiv_client.get_paper_recommendations(
                    paper_id, max_recommendations
                )
            else:
                self.logger.warning(f"Recommendations not supported for source: {source}")
                return []
                
        except Exception as e:
            self.logger.error(f"Failed to get recommendations for {paper_id}: {e}")
            return []
    
    async def search_by_author(
        self,
        author_name: str,
        sources: List[str] = None,
        max_results: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search for papers by author name.
        
        Args:
            author_name: Name of the author
            sources: Sources to search
            max_results: Maximum results per source
            
        Returns:
            List of papers by the author
        """
        try:
            if sources is None:
                sources = ['arxiv', 'crossref']
            if max_results is None:
                max_results = self.config.arxiv_max_results
            
            all_papers = []
            
            for source in sources:
                try:
                    if source == 'arxiv':
                        papers = await self.arxiv_client.search_by_author(author_name, max_results)
                        for paper in papers:
                            paper['source'] = 'arxiv'
                    elif source == 'crossref':
                        papers = await self.crossref_client.search_by_author(author_name, max_results)
                        for paper in papers:
                            paper['source'] = 'crossref'
                    else:
                        continue
                    
                    all_papers.extend(papers)
                    
                except Exception as e:
                    self.logger.error(f"Failed to search {source} for author {author_name}: {e}")
            
            return self._remove_duplicates(all_papers)
            
        except Exception as e:
            self.logger.error(f"Author search failed: {e}")
            return []
    
    async def get_scraping_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the scraping system.
        
        Returns:
            Dictionary with scraping statistics
        """
        try:
            stats = {
                'arxiv_health': await self.arxiv_client.check_service_health(),
                'grobid_health': await self.grobid_client.check_service_health(),
                'crossref_health': await self.crossref_client.check_service_health(),
                'config': {
                    'max_concurrent_downloads': self.config.max_concurrent_downloads,
                    'max_concurrent_analysis': self.config.max_concurrent_analysis,
                    'extract_pdfs': self.config.extract_pdfs,
                    'analyze_content': self.config.analyze_content
                }
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get scraping stats: {e}")
            return {}
