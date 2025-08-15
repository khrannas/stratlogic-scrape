import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
import os
import xml.etree.ElementTree as ET
from pathlib import Path
import urllib.parse

from .config import paper_scraper_settings

class ArxivClient:
    """
    Client for interacting with arXiv API using direct REST API calls
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "http://export.arxiv.org/api/query"
        self.settings = paper_scraper_settings
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def _make_request(self, params: Dict[str, str]) -> Optional[str]:
        """Make request to arXiv API"""
        try:
            session = await self._get_session()

            # Add delay to respect rate limits
            if hasattr(self.settings, 'arxiv_delay_seconds'):
                await asyncio.sleep(self.settings.arxiv_delay_seconds)

            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    self.logger.error(f"ArXiv API request failed with status {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Error making request to arXiv API: {e}")
            return None

    def _parse_arxiv_response(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse arXiv API XML response"""
        try:
            root = ET.fromstring(xml_content)

            # Define namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}

            papers = []
            for entry in root.findall('.//atom:entry', ns):
                paper_data = {
                    'arxiv_id': entry.find('atom:id', ns).text.split('/')[-1] if entry.find('atom:id', ns) is not None else None,
                    'title': entry.find('atom:title', ns).text.strip() if entry.find('atom:title', ns) is not None else None,
                    'summary': entry.find('atom:summary', ns).text.strip() if entry.find('atom:summary', ns) is not None else None,
                    'published_date': entry.find('atom:published', ns).text if entry.find('atom:published', ns) is not None else None,
                    'updated_date': entry.find('atom:updated', ns).text if entry.find('atom:updated', ns) is not None else None,
                    'pdf_url': None,
                    'doi': None,
                    'journal_ref': None,
                    'primary_category': None,
                    'comment': None,
                    'links': [],
                    'source': 'arxiv'
                }

                # Extract authors
                authors = []
                for author in entry.findall('.//atom:author/atom:name', ns):
                    if author.text:
                        authors.append(author.text)
                paper_data['authors'] = authors

                # Extract categories
                categories = []
                for category in entry.findall('.//atom:category', ns):
                    if category.get('term'):
                        categories.append(category.get('term'))
                paper_data['categories'] = categories

                # Extract links
                for link in entry.findall('.//atom:link', ns):
                    href = link.get('href')
                    if href:
                        paper_data['links'].append(href)
                        # Set PDF URL if it's a PDF link
                        if 'pdf' in href:
                            paper_data['pdf_url'] = href

                # Extract additional metadata
                for field in entry.findall('.//atom:field', ns):
                    name = field.get('name')
                    if name == 'doi':
                        paper_data['doi'] = field.text
                    elif name == 'journal_ref':
                        paper_data['journal_ref'] = field.text
                    elif name == 'comment':
                        paper_data['comment'] = field.text

                # Set primary category
                if paper_data['categories']:
                    paper_data['primary_category'] = paper_data['categories'][0]

                papers.append(paper_data)

            return papers
        except Exception as e:
            self.logger.error(f"Error parsing arXiv response: {e}")
            return []

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

            # Map sort parameters to arXiv API format
            sort_mapping = {
                "relevance": "relevance",
                "lastUpdatedDate": "lastUpdatedDate",
                "submittedDate": "submittedDate"
            }

            order_mapping = {
                "ascending": "ascending",
                "descending": "descending"
            }

            params = {
                'search_query': query,
                'start': 0,
                'max_results': max_results,
                'sortBy': sort_mapping.get(sort_by, 'relevance'),
                'sortOrder': order_mapping.get(sort_order, 'descending')
            }

            self.logger.info(f"Searching arXiv for: {query}")

            xml_content = await self._make_request(params)
            if xml_content:
                papers = self._parse_arxiv_response(xml_content)
                self.logger.info(f"Found {len(papers)} papers on arXiv")
                return papers
            else:
                return []

        except Exception as e:
            self.logger.error(f"Error searching arXiv: {e}")
            return []

    async def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific paper by arXiv ID

        Args:
            arxiv_id: arXiv paper ID

        Returns:
            Paper metadata dictionary or None if not found
        """
        try:
            params = {
                'id_list': arxiv_id
            }

            xml_content = await self._make_request(params)
            if xml_content:
                papers = self._parse_arxiv_response(xml_content)
                return papers[0] if papers else None
            else:
                return None

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
            # Get paper metadata first
            paper_data = await self.get_paper_by_id(arxiv_id)
            if not paper_data or not paper_data.get('pdf_url'):
                self.logger.error(f"No PDF URL found for {arxiv_id}")
                return None

            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Download PDF
            session = await self._get_session()
            async with session.get(paper_data['pdf_url']) as response:
                if response.status == 200:
                    with open(output_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)

                    self.logger.info(f"Downloaded PDF for {arxiv_id} to {output_path}")
                    return output_path
                else:
                    self.logger.error(f"Failed to download PDF for {arxiv_id}: HTTP {response.status}")
                    return None

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
            params = {
                'id_list': ','.join(arxiv_ids)
            }

            xml_content = await self._make_request(params)
            if xml_content:
                return self._parse_arxiv_response(xml_content)
            else:
                return []

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
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        date_query = f"submittedDate:[{start_date.strftime('%Y%m%d')}0000 TO {end_date.strftime('%Y%m%d')}2359]"
        full_query = f"({query}) AND {date_query}"

        return await self.search_papers(full_query, max_results, "submittedDate", "descending")

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
