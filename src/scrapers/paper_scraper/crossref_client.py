"""
CrossRef client for searching academic papers and metadata.
"""

import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
from urllib.parse import quote_plus


class CrossRefClient:
    """Client for interacting with CrossRef API."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.crossref.org"
        self.headers = {
            "User-Agent": config.crossref_user_agent,
            "Accept": "application/json"
        }
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def search_papers(
        self,
        query: str,
        max_results: int = None,
        offset: int = 0,
        sort: str = "relevance",
        order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using CrossRef API.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            offset: Offset for pagination
            sort: Sort criteria ('relevance', 'published', 'updated', 'is-referenced-by-count')
            order: Sort order ('asc', 'desc')
            
        Returns:
            List of paper metadata dictionaries
        """
        try:
            if max_results is None:
                max_results = self.config.crossref_max_results
            
            # Build query parameters
            params = {
                "query": query,
                "rows": min(max_results, 1000),  # CrossRef max is 1000
                "offset": offset,
                "sort": sort,
                "order": order
            }
            
            self.logger.info(f"Searching CrossRef for: {query}")
            
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.get(f"{self.base_url}/works", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_search_results(data, max_results)
                    else:
                        self.logger.error(f"CrossRef search failed: {response.status}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"CrossRef search failed for query '{query}': {e}")
            return []
    
    async def get_paper_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific paper by DOI.
        
        Args:
            doi: Digital Object Identifier
            
        Returns:
            Paper metadata dictionary or None if not found
        """
        try:
            encoded_doi = quote_plus(doi)
            
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.get(f"{self.base_url}/works/{encoded_doi}") as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_work_data(data.get("message", {}))
                    else:
                        self.logger.warning(f"Paper not found: {doi}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Failed to get paper {doi}: {e}")
            return None
    
    async def search_by_author(
        self,
        author_name: str,
        max_results: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search for papers by author name.
        
        Args:
            author_name: Name of the author
            max_results: Maximum number of results
            
        Returns:
            List of paper metadata
        """
        try:
            if max_results is None:
                max_results = self.config.crossref_max_results
            
            query = f"author:\"{author_name}\""
            return await self.search_papers(query, max_results)
            
        except Exception as e:
            self.logger.error(f"Failed to search by author {author_name}: {e}")
            return []
    
    async def search_by_journal(
        self,
        journal_name: str,
        max_results: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search for papers by journal name.
        
        Args:
            journal_name: Name of the journal
            max_results: Maximum number of results
            
        Returns:
            List of paper metadata
        """
        try:
            if max_results is None:
                max_results = self.config.crossref_max_results
            
            query = f"container-title:\"{journal_name}\""
            return await self.search_papers(query, max_results)
            
        except Exception as e:
            self.logger.error(f"Failed to search by journal {journal_name}: {e}")
            return []
    
    async def search_by_year(
        self,
        year: int,
        max_results: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search for papers published in a specific year.
        
        Args:
            year: Publication year
            max_results: Maximum number of results
            
        Returns:
            List of paper metadata
        """
        try:
            if max_results is None:
                max_results = self.config.crossref_max_results
            
            query = f"from-pub-date:{year}-01-01&until-pub-date:{year}-12-31"
            return await self.search_papers(query, max_results)
            
        except Exception as e:
            self.logger.error(f"Failed to search by year {year}: {e}")
            return []
    
    async def get_citations(self, doi: str) -> List[Dict[str, Any]]:
        """
        Get papers that cite a specific paper.
        
        Args:
            doi: DOI of the paper to find citations for
            
        Returns:
            List of citing papers
        """
        try:
            encoded_doi = quote_plus(doi)
            
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.get(f"{self.base_url}/works/{encoded_doi}") as response:
                    if response.status == 200:
                        data = await response.json()
                        work_data = data.get("message", {})
                        
                        # Get the number of citations
                        is_referenced_by_count = work_data.get("is-referenced-by-count", 0)
                        
                        if is_referenced_by_count > 0:
                            # Get the actual citations
                            citations_url = f"{self.base_url}/works/{encoded_doi}/references"
                            async with session.get(citations_url) as citations_response:
                                if citations_response.status == 200:
                                    citations_data = await citations_response.json()
                                    return self._parse_citations(citations_data.get("message", {}))
                        
                        return []
                    else:
                        return []
                        
        except Exception as e:
            self.logger.error(f"Failed to get citations for {doi}: {e}")
            return []
    
    async def get_references(self, doi: str) -> List[Dict[str, Any]]:
        """
        Get papers that are referenced by a specific paper.
        
        Args:
            doi: DOI of the paper to find references for
            
        Returns:
            List of referenced papers
        """
        try:
            encoded_doi = quote_plus(doi)
            
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.get(f"{self.base_url}/works/{encoded_doi}/references") as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_references(data.get("message", {}))
                    else:
                        return []
                        
        except Exception as e:
            self.logger.error(f"Failed to get references for {doi}: {e}")
            return []
    
    def _parse_search_results(self, data: Dict[str, Any], max_results: int) -> List[Dict[str, Any]]:
        """
        Parse CrossRef search results.
        
        Args:
            data: Response data from CrossRef
            max_results: Maximum number of results to return
            
        Returns:
            List of parsed paper metadata
        """
        try:
            items = data.get("message", {}).get("items", [])
            results = []
            
            for item in items[:max_results]:
                paper_data = self._parse_work_data(item)
                if paper_data:
                    results.append(paper_data)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to parse search results: {e}")
            return []
    
    def _parse_work_data(self, work: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse individual work data from CrossRef.
        
        Args:
            work: Work data from CrossRef
            
        Returns:
            Parsed paper metadata
        """
        try:
            # Calculate content hash
            content_for_hash = f"{work.get('title', [''])[0] if work.get('title') else ''}{work.get('abstract', '')}{work.get('author', [])}"
            content_hash = hashlib.sha256(str(content_for_hash).encode()).hexdigest()
            
            # Extract authors
            authors = []
            for author in work.get("author", []):
                author_data = {}
                if author.get("given"):
                    author_data["given"] = author["given"]
                if author.get("family"):
                    author_data["family"] = author["family"]
                if author_data:
                    authors.append(author_data)
            
            # Extract title
            title = work.get("title", [""])[0] if work.get("title") else ""
            
            # Extract container title (journal)
            container_title = work.get("container-title", [""])[0] if work.get("container-title") else ""
            
            # Extract publication date
            published_date = None
            if work.get("published-print") and work["published-print"].get("date-parts"):
                date_parts = work["published-print"]["date-parts"][0]
                if len(date_parts) >= 3:
                    published_date = f"{date_parts[0]}-{date_parts[1]:02d}-{date_parts[2]:02d}"
                elif len(date_parts) >= 2:
                    published_date = f"{date_parts[0]}-{date_parts[1]:02d}-01"
                elif len(date_parts) >= 1:
                    published_date = f"{date_parts[0]}-01-01"
            
            return {
                "doi": work.get("DOI", ""),
                "title": title,
                "authors": authors,
                "abstract": work.get("abstract", ""),
                "container_title": container_title,
                "published_date": published_date,
                "type": work.get("type", ""),
                "publisher": work.get("publisher", ""),
                "issn": work.get("ISSN", []),
                "isbn": work.get("ISBN", []),
                "subject": work.get("subject", []),
                "language": work.get("language", ""),
                "page": work.get("page", ""),
                "volume": work.get("volume", ""),
                "issue": work.get("issue", ""),
                "is_referenced_by_count": work.get("is-referenced-by-count", 0),
                "reference_count": work.get("reference-count", 0),
                "content_hash": content_hash,
                "word_count": len(work.get("abstract", "").split()),
                "extraction_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse work data: {e}")
            return None
    
    def _parse_citations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse citations data from CrossRef.
        
        Args:
            data: Citations data from CrossRef
            
        Returns:
            List of citing papers
        """
        try:
            items = data.get("items", [])
            citations = []
            
            for item in items:
                citation = self._parse_work_data(item)
                if citation:
                    citations.append(citation)
            
            return citations
            
        except Exception as e:
            self.logger.error(f"Failed to parse citations: {e}")
            return []
    
    def _parse_references(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse references data from CrossRef.
        
        Args:
            data: References data from CrossRef
            
        Returns:
            List of referenced papers
        """
        try:
            items = data.get("items", [])
            references = []
            
            for item in items:
                reference = {
                    "doi": item.get("DOI", ""),
                    "title": item.get("title", [""])[0] if item.get("title") else "",
                    "authors": [
                        {
                            "given": author.get("given", ""),
                            "family": author.get("family", "")
                        }
                        for author in item.get("author", [])
                    ],
                    "container_title": item.get("container-title", [""])[0] if item.get("container-title") else "",
                    "type": item.get("type", ""),
                    "publisher": item.get("publisher", ""),
                    "year": item.get("year"),
                    "volume": item.get("volume", ""),
                    "issue": item.get("issue", ""),
                    "page": item.get("page", "")
                }
                references.append(reference)
            
            return references
            
        except Exception as e:
            self.logger.error(f"Failed to parse references: {e}")
            return []
    
    async def check_service_health(self) -> bool:
        """
        Check if CrossRef service is healthy and responding.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10), headers=self.headers) as session:
                async with session.get(f"{self.base_url}/works") as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"CrossRef health check failed: {e}")
            return False
