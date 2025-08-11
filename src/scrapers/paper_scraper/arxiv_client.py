"""
arXiv client for searching and downloading academic papers.
"""

import arxiv
import asyncio
import logging
import aiohttp
import aiofiles
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import os
import tempfile
from urllib.parse import urlparse
import hashlib


class ArxivClient:
    """Client for interacting with arXiv API."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=config.arxiv_delay_seconds,
            num_retries=config.arxiv_max_retries
        )
    
    async def search_papers(
        self,
        query: str,
        max_results: int = None,
        sort_by: str = "relevance",
        sort_order: str = "descending"
    ) -> List[Dict[str, Any]]:
        """
        Search for papers on arXiv.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            sort_by: Sort criteria ('relevance', 'lastUpdatedDate', 'submittedDate')
            sort_order: Sort order ('ascending', 'descending')
            
        Returns:
            List of paper metadata dictionaries
        """
        try:
            if max_results is None:
                max_results = self.config.arxiv_max_results
            
            # Create search object
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=getattr(arxiv.SortCriterion, sort_by.upper()),
                sort_order=getattr(arxiv.SortOrder, sort_order.upper())
            )
            
            self.logger.info(f"Searching arXiv for: {query}")
            
            # Execute search
            results = []
            for result in self.client.results(search):
                paper_data = self._extract_paper_metadata(result)
                results.append(paper_data)
                
                if len(results) >= max_results:
                    break
            
            self.logger.info(f"Found {len(results)} papers for query: {query}")
            return results
            
        except Exception as e:
            self.logger.error(f"arXiv search failed for query '{query}': {e}")
            return []
    
    async def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific paper by arXiv ID.
        
        Args:
            arxiv_id: arXiv paper ID (e.g., '2103.12345')
            
        Returns:
            Paper metadata dictionary or None if not found
        """
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            result = next(self.client.results(search), None)
            
            if result:
                return self._extract_paper_metadata(result)
            else:
                self.logger.warning(f"Paper not found: {arxiv_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get paper {arxiv_id}: {e}")
            return None
    
    async def download_paper_pdf(
        self,
        arxiv_id: str,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Download a paper's PDF file.
        
        Args:
            arxiv_id: arXiv paper ID
            output_path: Path to save the PDF (optional)
            
        Returns:
            Path to downloaded PDF file or None if failed
        """
        try:
            if output_path is None:
                # Create temporary file
                temp_dir = tempfile.gettempdir()
                output_path = os.path.join(temp_dir, f"{arxiv_id}.pdf")
            
            # Get paper metadata first
            paper = await self.get_paper_by_id(arxiv_id)
            if not paper:
                return None
            
            # Download PDF
            search = arxiv.Search(id_list=[arxiv_id])
            result = next(self.client.results(search))
            
            self.logger.info(f"Downloading PDF for {arxiv_id}")
            result.download_pdf(filename=output_path)
            
            # Verify file was downloaded
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                self.logger.info(f"PDF downloaded successfully: {output_path}")
                return output_path
            else:
                self.logger.error(f"PDF download failed for {arxiv_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to download PDF for {arxiv_id}: {e}")
            return None
    
    async def get_paper_recommendations(
        self,
        arxiv_id: str,
        max_recommendations: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get paper recommendations based on a given paper.
        
        Args:
            arxiv_id: arXiv paper ID
            max_recommendations: Maximum number of recommendations
            
        Returns:
            List of recommended paper metadata
        """
        try:
            # Get the original paper
            paper = await self.get_paper_by_id(arxiv_id)
            if not paper:
                return []
            
            # Use title and abstract for recommendation search
            query_parts = []
            if paper.get('title'):
                query_parts.append(paper['title'])
            if paper.get('abstract'):
                # Use first 200 characters of abstract
                abstract_preview = paper['abstract'][:200]
                query_parts.append(abstract_preview)
            
            if not query_parts:
                return []
            
            # Create recommendation query
            recommendation_query = " AND ".join(query_parts)
            
            # Search for similar papers
            recommendations = await self.search_papers(
                recommendation_query,
                max_results=max_recommendations + 1  # +1 to account for original paper
            )
            
            # Filter out the original paper
            filtered_recommendations = [
                rec for rec in recommendations 
                if rec.get('arxiv_id') != arxiv_id
            ]
            
            return filtered_recommendations[:max_recommendations]
            
        except Exception as e:
            self.logger.error(f"Failed to get recommendations for {arxiv_id}: {e}")
            return []
    
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
                max_results = self.config.arxiv_max_results
            
            query = f"au:\"{author_name}\""
            return await self.search_papers(query, max_results)
            
        except Exception as e:
            self.logger.error(f"Failed to search by author {author_name}: {e}")
            return []
    
    async def search_by_category(
        self,
        category: str,
        max_results: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search for papers by arXiv category.
        
        Args:
            category: arXiv category (e.g., 'cs.AI', 'math.CO')
            max_results: Maximum number of results
            
        Returns:
            List of paper metadata
        """
        try:
            if max_results is None:
                max_results = self.config.arxiv_max_results
            
            query = f"cat:{category}"
            return await self.search_papers(query, max_results)
            
        except Exception as e:
            self.logger.error(f"Failed to search by category {category}: {e}")
            return []
    
    def _extract_paper_metadata(self, result) -> Dict[str, Any]:
        """
        Extract metadata from arXiv result object.
        
        Args:
            result: arXiv result object
            
        Returns:
            Dictionary containing paper metadata
        """
        try:
            # Calculate content hash
            content_for_hash = f"{result.title}{result.summary}{result.authors}"
            content_hash = hashlib.sha256(content_for_hash.encode()).hexdigest()
            
            return {
                'arxiv_id': result.entry_id.split('/')[-1],
                'title': result.title,
                'authors': [author.name for author in result.authors],
                'summary': result.summary,
                'categories': result.categories,
                'primary_category': result.primary_category,
                'published_date': result.published.isoformat() if result.published else None,
                'updated_date': result.updated.isoformat() if result.updated else None,
                'pdf_url': result.pdf_url,
                'entry_id': result.entry_id,
                'doi': result.doi,
                'journal_ref': result.journal_ref,
                'comment': result.comment,
                'content_hash': content_hash,
                'word_count': len(result.summary.split()) if result.summary else 0,
                'extraction_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to extract metadata: {e}")
            return {}
    
    async def get_paper_stats(self, arxiv_id: str) -> Dict[str, Any]:
        """
        Get statistics for a paper (citations, downloads, etc.).
        Note: This is a placeholder as arXiv doesn't provide these stats directly.
        
        Args:
            arxiv_id: arXiv paper ID
            
        Returns:
            Dictionary with paper statistics
        """
        try:
            paper = await self.get_paper_by_id(arxiv_id)
            if not paper:
                return {}
            
            # Basic stats that we can calculate
            stats = {
                'arxiv_id': arxiv_id,
                'title_length': len(paper.get('title', '')),
                'abstract_length': len(paper.get('summary', '')),
                'author_count': len(paper.get('authors', [])),
                'category_count': len(paper.get('categories', [])),
                'has_doi': bool(paper.get('doi')),
                'has_journal_ref': bool(paper.get('journal_ref')),
                'has_comment': bool(paper.get('comment')),
                'days_since_published': None,
                'days_since_updated': None
            }
            
            # Calculate days since published/updated
            if paper.get('published_date'):
                try:
                    published_date = datetime.fromisoformat(paper['published_date'].replace('Z', '+00:00'))
                    days_since_published = (datetime.utcnow() - published_date.replace(tzinfo=None)).days
                    stats['days_since_published'] = days_since_published
                except:
                    pass
            
            if paper.get('updated_date'):
                try:
                    updated_date = datetime.fromisoformat(paper['updated_date'].replace('Z', '+00:00'))
                    days_since_updated = (datetime.utcnow() - updated_date.replace(tzinfo=None)).days
                    stats['days_since_updated'] = days_since_updated
                except:
                    pass
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get stats for {arxiv_id}: {e}")
            return {}
