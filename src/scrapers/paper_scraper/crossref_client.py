import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from .config import paper_scraper_settings

class CrossRefClient:
    """
    Client for interacting with CrossRef API
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.crossref.org"
        self.user_agent = paper_scraper_settings.crossref_user_agent
        self.max_results = paper_scraper_settings.crossref_max_results
        self.delay_seconds = paper_scraper_settings.crossref_delay_seconds

    async def search_works(
        self,
        query: str,
        max_results: int = None,
        offset: int = 0,
        sort: str = "relevance",
        order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        Search for works in CrossRef

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            offset: Offset for pagination
            sort: Sort criteria ("relevance", "published", "updated", "is-referenced-by-count")
            order: Sort order ("asc", "desc")

        Returns:
            List of work metadata dictionaries
        """
        try:
            max_results = max_results or self.max_results

            params = {
                'query': query,
                'rows': min(max_results, 1000),  # CrossRef max is 1000
                'offset': offset,
                'sort': sort,
                'order': order
            }

            headers = {
                'User-Agent': self.user_agent
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/works",
                    params=params,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._parse_works_response(data)
                    else:
                        self.logger.error(f"CrossRef search failed with status {response.status}")
                        return []

        except Exception as e:
            self.logger.error(f"Error searching CrossRef: {e}")
            return []

    async def get_work_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific work by DOI

        Args:
            doi: Digital Object Identifier

        Returns:
            Work metadata dictionary or None if not found
        """
        try:
            headers = {
                'User-Agent': self.user_agent
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/works/{doi}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._parse_single_work(data.get('message', {}))
                    else:
                        self.logger.error(f"CrossRef DOI lookup failed with status {response.status}")
                        return None

        except Exception as e:
            self.logger.error(f"Error getting work by DOI {doi}: {e}")
            return None

    async def get_works_by_dois(self, dois: List[str]) -> List[Dict[str, Any]]:
        """
        Get multiple works by their DOIs

        Args:
            dois: List of Digital Object Identifiers

        Returns:
            List of work metadata dictionaries
        """
        results = []

        for doi in dois:
            try:
                work = await self.get_work_by_doi(doi)
                if work:
                    results.append(work)

                # Respect rate limits
                await asyncio.sleep(self.delay_seconds)

            except Exception as e:
                self.logger.error(f"Error getting work for DOI {doi}: {e}")
                continue

        return results

    async def search_by_author(
        self,
        author_name: str,
        max_results: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search for works by author name

        Args:
            author_name: Name of the author
            max_results: Maximum number of results to return

        Returns:
            List of work metadata dictionaries
        """
        query = f"author:\"{author_name}\""
        return await self.search_works(query, max_results)

    async def search_by_journal(
        self,
        journal_name: str,
        max_results: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search for works in a specific journal

        Args:
            journal_name: Name of the journal
            max_results: Maximum number of results to return

        Returns:
            List of work metadata dictionaries
        """
        query = f"container-title:\"{journal_name}\""
        return await self.search_works(query, max_results)

    async def search_by_date_range(
        self,
        start_date: str,
        end_date: str,
        query: str = "",
        max_results: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search for works within a date range

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            query: Additional search query
            max_results: Maximum number of results to return

        Returns:
            List of work metadata dictionaries
        """
        date_query = f"from-created-date:{start_date},until-created-date:{end_date}"
        if query:
            full_query = f"({query}) AND {date_query}"
        else:
            full_query = date_query

        return await self.search_works(full_query, max_results, "published", "desc")

    async def _parse_works_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse CrossRef works response

        Args:
            data: Raw response data from CrossRef

        Returns:
            List of parsed work dictionaries
        """
        works = []

        try:
            items = data.get('message', {}).get('items', [])

            for item in items:
                work = await self._parse_single_work(item)
                if work:
                    works.append(work)

        except Exception as e:
            self.logger.error(f"Error parsing CrossRef works response: {e}")

        return works

    async def _parse_single_work(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a single work from CrossRef response

        Args:
            item: Single work item from CrossRef

        Returns:
            Parsed work dictionary or None if parsing fails
        """
        try:
            work = {
                'doi': item.get('DOI'),
                'title': self._extract_title(item),
                'authors': self._extract_authors(item),
                'abstract': self._extract_abstract(item),
                'journal': self._extract_journal(item),
                'published_date': self._extract_published_date(item),
                'type': item.get('type'),
                'url': item.get('URL'),
                'subject': item.get('subject', []),
                'language': item.get('language'),
                'issn': item.get('ISSN', []),
                'isbn': item.get('ISBN', []),
                'volume': item.get('volume'),
                'issue': item.get('issue'),
                'page': item.get('page'),
                'publisher': item.get('publisher'),
                'reference_count': item.get('reference-count'),
                'is_referenced_by_count': item.get('is-referenced-by-count'),
                'source': 'crossref'
            }

            return work

        except Exception as e:
            self.logger.error(f"Error parsing single work: {e}")
            return None

    def _extract_title(self, item: Dict[str, Any]) -> str:
        """Extract title from work item"""
        title = item.get('title', [])
        if title and len(title) > 0:
            return title[0]
        return ""

    def _extract_authors(self, item: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract authors from work item"""
        authors = []
        author_list = item.get('author', [])

        for author in author_list:
            author_data = {
                'given': author.get('given', ''),
                'family': author.get('family', ''),
                'name': f"{author.get('given', '')} {author.get('family', '')}".strip()
            }
            authors.append(author_data)

        return authors

    def _extract_abstract(self, item: Dict[str, Any]) -> str:
        """Extract abstract from work item"""
        abstract = item.get('abstract', '')
        if isinstance(abstract, str):
            return abstract
        return ""

    def _extract_journal(self, item: Dict[str, Any]) -> str:
        """Extract journal name from work item"""
        container_title = item.get('container-title', [])
        if container_title and len(container_title) > 0:
            return container_title[0]
        return ""

    def _extract_published_date(self, item: Dict[str, Any]) -> str:
        """Extract published date from work item"""
        date_parts = item.get('published-print', {}).get('date-parts', [])
        if date_parts and len(date_parts) > 0:
            date_part = date_parts[0]
            if len(date_part) >= 3:
                return f"{date_part[0]}-{date_part[1]:02d}-{date_part[2]:02d}"
            elif len(date_part) >= 2:
                return f"{date_part[0]}-{date_part[1]:02d}-01"
            elif len(date_part) >= 1:
                return f"{date_part[0]}-01-01"
        return ""

    async def get_journal_info(self, issn: str) -> Optional[Dict[str, Any]]:
        """
        Get journal information by ISSN

        Args:
            issn: International Standard Serial Number

        Returns:
            Journal information dictionary or None if not found
        """
        try:
            headers = {
                'User-Agent': self.user_agent
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/journals/{issn}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('message', {})
                    else:
                        self.logger.error(f"CrossRef journal lookup failed with status {response.status}")
                        return None

        except Exception as e:
            self.logger.error(f"Error getting journal info for ISSN {issn}: {e}")
            return None
