import asyncio
import logging
from typing import List, Dict, Any, Optional
import tempfile
import os
from datetime import datetime
import uuid

from .arxiv_client import ArxivClient
from .grobid_client import GrobidClient
from .crossref_client import CrossRefClient
from .content_analyzer import PaperContentAnalyzer
from .config import paper_scraper_settings
from src.services.artifact_service import artifact_service
from src.services.job_service import job_service
from src.storage.artifact_storage import ArtifactStorage

class PaperScraper:
    """
    Main paper scraper orchestrator
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = paper_scraper_settings

        # Initialize components
        self.arxiv_client = ArxivClient()
        self.grobid_client = GrobidClient()
        self.crossref_client = CrossRefClient()
        self.content_analyzer = PaperContentAnalyzer()
        self.artifact_storage = ArtifactStorage()

        self.logger.info("PaperScraper initialized")

    async def scrape_papers(
        self,
        query: str,
        job_id: str,
        user_id: str,
        max_results: int = None,
        sources: List[str] = ['arxiv'],
        extract_pdfs: bool = True,
        analyze_content: bool = True,
        download_pdfs: bool = True
    ) -> Dict[str, Any]:
        """
        Main paper scraping orchestration

        Args:
            query: Search query for papers
            job_id: Job identifier
            user_id: User identifier
            max_results: Maximum number of results
            sources: List of sources to search ('arxiv', 'crossref', 'semantic_scholar')
            extract_pdfs: Whether to extract PDF content
            analyze_content: Whether to analyze content with LLM
            download_pdfs: Whether to download PDFs

        Returns:
            Dictionary containing scraping results
        """
        try:
            # Update job status
            await self._update_job_status(job_id, 'running')

            self.logger.info(f"Starting paper scraping for query: {query}")

            all_papers = []
            total_sources = len(sources)

            for i, source in enumerate(sources):
                self.logger.info(f"Processing source {i+1}/{total_sources}: {source}")

                # Update progress
                progress = int((i / total_sources) * 50)  # First 50% for search
                await self._update_job_progress(job_id, progress)

                # Search papers from source
                papers = await self._search_papers_from_source(
                    source, query, max_results
                )

                if papers:
                    all_papers.extend(papers)

                # Add delay between sources
                await asyncio.sleep(2)

            # Remove duplicates
            unique_papers = self._remove_duplicates(all_papers)
            self.logger.info(f"Found {len(unique_papers)} unique papers")

            # Process papers
            processed_papers = []
            total_papers = len(unique_papers)

            for i, paper in enumerate(unique_papers):
                self.logger.info(f"Processing paper {i+1}/{total_papers}: {paper.get('title', 'Unknown')}")

                # Update progress (50-90% for processing)
                progress = 50 + int((i / total_papers) * 40)
                await self._update_job_progress(job_id, progress)

                try:
                    processed_paper = await self._process_single_paper(
                        paper, extract_pdfs, analyze_content, download_pdfs, user_id, job_id
                    )
                    if processed_paper:
                        processed_papers.append(processed_paper)

                except Exception as e:
                    self.logger.error(f"Error processing paper {paper.get('title', 'Unknown')}: {e}")
                    continue

                # Add delay between papers
                await asyncio.sleep(1)

            # Update job completion
            await self._update_job_progress(job_id, 100)
            await self._update_job_status(job_id, 'completed')

            result = {
                'job_id': job_id,
                'query': query,
                'total_papers_found': len(all_papers),
                'unique_papers_processed': len(processed_papers),
                'sources_searched': sources,
                'papers': processed_papers,
                'completed_at': datetime.now().isoformat()
            }

            self.logger.info(f"Paper scraping completed. Processed {len(processed_papers)} papers")
            return result

        except Exception as e:
            self.logger.error(f"Error in paper scraping: {e}")
            await self._update_job_status(job_id, 'failed')
            raise

    async def _search_papers_from_source(
        self,
        source: str,
        query: str,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """
        Search papers from a specific source

        Args:
            source: Source name ('arxiv', 'crossref', etc.)
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of paper metadata dictionaries
        """
        try:
            if source.lower() == 'arxiv':
                return await self.arxiv_client.search_papers(query, max_results)
            elif source.lower() == 'crossref':
                return await self.crossref_client.search_works(query, max_results)
            else:
                self.logger.warning(f"Unknown source: {source}")
                return []

        except Exception as e:
            self.logger.error(f"Error searching {source}: {e}")
            return []

    async def _process_single_paper(
        self,
        paper: Dict[str, Any],
        extract_pdfs: bool,
        analyze_content: bool,
        download_pdfs: bool,
        user_id: str,
        job_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single paper (download, extract, analyze)

        Args:
            paper: Paper metadata
            extract_pdfs: Whether to extract PDF content
            analyze_content: Whether to analyze content
            download_pdfs: Whether to download PDFs
            user_id: User identifier
            job_id: Job identifier

        Returns:
            Processed paper data or None if failed
        """
        try:
            paper_id = paper.get('arxiv_id') or paper.get('doi')
            if not paper_id:
                self.logger.warning("Paper has no ID, skipping")
                return None

            # Download PDF if requested and available
            pdf_path = None
            if download_pdfs and paper.get('pdf_url'):
                pdf_path = await self._download_paper_pdf(paper)

            # Extract PDF content if requested
            grobid_extraction = None
            if extract_pdfs and pdf_path:
                grobid_extraction = await self.grobid_client.extract_pdf_content(pdf_path)

            # Analyze content if requested
            content_analysis = None
            if analyze_content:
                # Combine paper data with extracted content
                analysis_data = {**paper}
                if grobid_extraction:
                    analysis_data['grobid_extraction'] = grobid_extraction

                content_analysis = await self.content_analyzer.analyze_paper(analysis_data)

            # Store artifacts
            artifacts = await self._store_paper_artifacts(
                paper, pdf_path, grobid_extraction, content_analysis, user_id, job_id
            )

            # Prepare result
            result = {
                'paper_id': paper_id,
                'title': paper.get('title'),
                'authors': paper.get('authors', []),
                'source': paper.get('source'),
                'metadata': paper,
                'grobid_extraction': grobid_extraction,
                'content_analysis': content_analysis,
                'artifacts': artifacts,
                'processed_at': datetime.now().isoformat()
            }

            return result

        except Exception as e:
            self.logger.error(f"Error processing paper: {e}")
            return None

    async def _download_paper_pdf(self, paper: Dict[str, Any]) -> Optional[str]:
        """
        Download paper PDF

        Args:
            paper: Paper metadata

        Returns:
            Path to downloaded PDF or None if failed
        """
        try:
            if paper.get('source') == 'arxiv' and paper.get('arxiv_id'):
                # Create temporary file
                temp_dir = tempfile.mkdtemp()
                pdf_filename = f"{paper['arxiv_id']}.pdf"
                pdf_path = os.path.join(temp_dir, pdf_filename)

                # Download using arXiv client
                result_path = await self.arxiv_client.download_paper_pdf(
                    paper['arxiv_id'], pdf_path
                )

                if result_path and os.path.exists(result_path):
                    self.logger.info(f"Downloaded PDF: {result_path}")
                    return result_path

            elif paper.get('pdf_url'):
                # Download from direct URL
                return await self._download_from_url(paper['pdf_url'], paper.get('title', 'paper'))

            return None

        except Exception as e:
            self.logger.error(f"Error downloading PDF: {e}")
            return None

    async def _download_from_url(self, url: str, title: str) -> Optional[str]:
        """
        Download PDF from URL

        Args:
            url: PDF URL
            title: Paper title for filename

        Returns:
            Path to downloaded PDF or None if failed
        """
        try:
            import aiohttp

            # Create temporary file
            temp_dir = tempfile.mkdtemp()
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            pdf_filename = f"{safe_title[:50]}.pdf"
            pdf_path = os.path.join(temp_dir, pdf_filename)

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        with open(pdf_path, 'wb') as f:
                            f.write(await response.read())

                        self.logger.info(f"Downloaded PDF from URL: {pdf_path}")
                        return pdf_path

            return None

        except Exception as e:
            self.logger.error(f"Error downloading from URL: {e}")
            return None

    async def _store_paper_artifacts(
        self,
        paper: Dict[str, Any],
        pdf_path: Optional[str],
        grobid_extraction: Optional[Dict[str, Any]],
        content_analysis: Optional[Dict[str, Any]],
        user_id: str,
        job_id: str
    ) -> Dict[str, Any]:
        """
        Store paper artifacts in MinIO

        Args:
            paper: Paper metadata
            pdf_path: Path to PDF file
            grobid_extraction: Grobid extraction results
            content_analysis: Content analysis results
            user_id: User identifier
            job_id: Job identifier

        Returns:
            Dictionary containing artifact information
        """
        artifacts = {}

        try:
            paper_id = paper.get('arxiv_id') or paper.get('doi')

            # Store PDF if available
            if pdf_path and os.path.exists(pdf_path):
                pdf_artifact_id = await self.artifact_storage.upload_file(
                    file_path=pdf_path,
                    bucket_name=self.settings.pdf_storage_bucket,
                    object_name=f"papers/{paper_id}/{os.path.basename(pdf_path)}",
                    metadata={
                        'paper_id': paper_id,
                        'title': paper.get('title'),
                        'source': paper.get('source'),
                        'content_type': 'application/pdf',
                        'user_id': user_id,
                        'job_id': job_id
                    }
                )
                artifacts['pdf'] = pdf_artifact_id

            # Store metadata
            metadata_artifact_id = await self.artifact_storage.upload_json(
                data=paper,
                bucket_name=self.settings.metadata_storage_bucket,
                object_name=f"metadata/{paper_id}/paper_metadata.json",
                metadata={
                    'paper_id': paper_id,
                    'content_type': 'application/json',
                    'user_id': user_id,
                    'job_id': job_id
                }
            )
            artifacts['metadata'] = metadata_artifact_id

            # Store Grobid extraction if available
            if grobid_extraction:
                grobid_artifact_id = await self.artifact_storage.upload_json(
                    data=grobid_extraction,
                    bucket_name=self.settings.metadata_storage_bucket,
                    object_name=f"grobid/{paper_id}/extraction.json",
                    metadata={
                        'paper_id': paper_id,
                        'content_type': 'application/json',
                        'user_id': user_id,
                        'job_id': job_id
                    }
                )
                artifacts['grobid_extraction'] = grobid_artifact_id

            # Store content analysis if available
            if content_analysis:
                analysis_artifact_id = await self.artifact_storage.upload_json(
                    data=content_analysis,
                    bucket_name=self.settings.metadata_storage_bucket,
                    object_name=f"analysis/{paper_id}/content_analysis.json",
                    metadata={
                        'paper_id': paper_id,
                        'content_type': 'application/json',
                        'user_id': user_id,
                        'job_id': job_id
                    }
                )
                artifacts['content_analysis'] = analysis_artifact_id

            return artifacts

        except Exception as e:
            self.logger.error(f"Error storing artifacts: {e}")
            return artifacts

    def _remove_duplicates(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate papers based on ID

        Args:
            papers: List of paper dictionaries

        Returns:
            List of unique papers
        """
        seen_ids = set()
        unique_papers = []

        for paper in papers:
            paper_id = paper.get('arxiv_id') or paper.get('doi')
            if paper_id and paper_id not in seen_ids:
                seen_ids.add(paper_id)
                unique_papers.append(paper)

        return unique_papers

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

    async def get_paper_by_id(
        self,
        paper_id: str,
        source: str = 'arxiv'
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific paper by ID

        Args:
            paper_id: Paper identifier
            source: Source name ('arxiv', 'crossref')

        Returns:
            Paper data or None if not found
        """
        try:
            if source.lower() == 'arxiv':
                return await self.arxiv_client.get_paper_by_id(paper_id)
            elif source.lower() == 'crossref':
                return await self.crossref_client.get_work_by_doi(paper_id)
            else:
                self.logger.warning(f"Unknown source: {source}")
                return None

        except Exception as e:
            self.logger.error(f"Error getting paper by ID: {e}")
            return None

    async def check_services_health(self) -> Dict[str, bool]:
        """
        Check health of all paper scraping services

        Returns:
            Dictionary with service health status
        """
        try:
            health_status = {
                'arxiv': True,  # arXiv client doesn't have health check
                'grobid': await self.grobid_client.check_service_health(),
                'crossref': True,  # CrossRef is generally reliable
                'llm_service': True  # LLM service health check would be added here
            }

            return health_status

        except Exception as e:
            self.logger.error(f"Error checking services health: {e}")
            return {
                'arxiv': False,
                'grobid': False,
                'crossref': False,
                'llm_service': False
            }
