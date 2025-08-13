import arxiv
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
import os
from pathlib import Path

from .config import paper_scraper_settings

class ArxivClient:
    """
    Client for interacting with arXiv API
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=paper_scraper_settings.arxiv_delay_seconds,
            num_retries=paper_scraper_settings.arxiv_max_retries
        )
        self.settings = paper_scraper_settings

    async def search_papers(
        self,
        query: str,
        max_results: int = None,
        sort_by: str = "relevance",
        sort_order: str = "descending"
    ) -> List[Dict[str, Any]]:
        """
        Search for papers on arXiv

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            sort_by: Sort criteria ("relevance", "lastUpdatedDate", "submittedDate")
            sort_order: Sort order ("ascending", "descending")

        Returns:
            List of paper metadata dictionaries
        """
        try:
            max_results = max_results or self.settings.arxiv_max_results

            # Create search object
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=getattr(arxiv.SortCriterion, sort_by.title()),
                sort_order=getattr(arxiv.SortOrder, sort_order.title())
            )

            self.logger.info(f"Searching arXiv for: {query}")

            # Execute search
            results = list(self.client.results(search))

            # Convert to dictionary format
            papers = []
            for result in results:
                paper_data = {
                    'arxiv_id': result.entry_id.split('/')[-1],
                    'title': result.title,
                    'authors': [author.name for author in result.authors],
                    'summary': result.summary,
                    'categories': result.categories,
                    'published_date': result.published.isoformat() if result.published else None,
                    'updated_date': result.updated.isoformat() if result.updated else None,
                    'pdf_url': result.pdf_url,
                    'doi': result.doi,
                    'journal_ref': result.journal_ref,
                    'primary_category': result.primary_category,
                    'comment': result.comment,
                    'links': [link.href for link in result.links],
                    'source': 'arxiv'
                }
                papers.append(paper_data)

            self.logger.info(f"Found {len(papers)} papers on arXiv")
            return papers

        except Exception as e:
            self.logger.error(f"Error searching arXiv: {e}")
            raise

    async def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific paper by arXiv ID

        Args:
            arxiv_id: arXiv paper ID

        Returns:
            Paper metadata dictionary or None if not found
        """
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            results = list(self.client.results(search))

            if not results:
                return None

            result = results[0]
            paper_data = {
                'arxiv_id': result.entry_id.split('/')[-1],
                'title': result.title,
                'authors': [author.name for author in result.authors],
                'summary': result.summary,
                'categories': result.categories,
                'published_date': result.published.isoformat() if result.published else None,
                'updated_date': result.updated.isoformat() if result.updated else None,
                'pdf_url': result.pdf_url,
                'doi': result.doi,
                'journal_ref': result.journal_ref,
                'primary_category': result.primary_category,
                'comment': result.comment,
                'links': [link.href for link in result.links],
                'source': 'arxiv'
            }

            return paper_data

        except Exception as e:
            self.logger.error(f"Error getting paper {arxiv_id}: {e}")
            return None

    async def download_paper_pdf(
        self,
        arxiv_id: str,
        output_path: str
    ) -> Optional[str]:
        """
        Download PDF for a specific paper

        Args:
            arxiv_id: arXiv paper ID
            output_path: Path to save the PDF

        Returns:
            Path to downloaded PDF or None if failed
        """
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            paper = next(self.client.results(search))

            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Download PDF
            paper.download_pdf(filename=output_path)

            self.logger.info(f"Downloaded PDF for {arxiv_id} to {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Error downloading PDF for {arxiv_id}: {e}")
            return None

    async def get_paper_metadata_batch(
        self,
        arxiv_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get metadata for multiple papers by their arXiv IDs

        Args:
            arxiv_ids: List of arXiv paper IDs

        Returns:
            List of paper metadata dictionaries
        """
        try:
            search = arxiv.Search(id_list=arxiv_ids)
            results = list(self.client.results(search))

            papers = []
            for result in results:
                paper_data = {
                    'arxiv_id': result.entry_id.split('/')[-1],
                    'title': result.title,
                    'authors': [author.name for author in result.authors],
                    'summary': result.summary,
                    'categories': result.categories,
                    'published_date': result.published.isoformat() if result.published else None,
                    'updated_date': result.updated.isoformat() if result.updated else None,
                    'pdf_url': result.pdf_url,
                    'doi': result.doi,
                    'journal_ref': result.journal_ref,
                    'primary_category': result.primary_category,
                    'comment': result.comment,
                    'links': [link.href for link in result.links],
                    'source': 'arxiv'
                }
                papers.append(paper_data)

            return papers

        except Exception as e:
            self.logger.error(f"Error getting batch metadata: {e}")
            return []

    async def search_by_category(
        self,
        category: str,
        max_results: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search for papers in a specific arXiv category

        Args:
            category: arXiv category (e.g., 'cs.AI', 'physics.comp-ph')
            max_results: Maximum number of results to return

        Returns:
            List of paper metadata dictionaries
        """
        query = f"cat:{category}"
        return await self.search_papers(query, max_results)

    async def search_recent_papers(
        self,
        query: str,
        days: int = 30,
        max_results: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search for recent papers within specified days

        Args:
            query: Search query
            days: Number of days to look back
            max_results: Maximum number of results to return

        Returns:
            List of paper metadata dictionaries
        """
        from datetime import datetime, timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        date_query = f"submittedDate:[{start_date.strftime('%Y%m%d')}0000 TO {end_date.strftime('%Y%m%d')}2359]"
        full_query = f"({query}) AND {date_query}"

        return await self.search_papers(full_query, max_results, "submittedDate", "descending")
