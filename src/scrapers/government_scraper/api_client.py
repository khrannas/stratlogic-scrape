"""
Government API client for Indonesian government document APIs.
"""

import aiohttp
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from .config import GovernmentScraperSettings


@dataclass
class APIDocument:
    """Document information from government API."""
    id: str
    title: str
    url: str
    description: Optional[str]
    published_date: Optional[str]
    source: str
    api_endpoint: str
    metadata: Dict[str, Any]
    extraction_timestamp: str


class GovernmentAPIClient:
    """Client for interacting with government APIs."""
    
    def __init__(self, settings: GovernmentScraperSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.session = None
        
        # Rate limiting
        self.last_request_time = 0.0
        self.request_count = 0
    
    async def __aenter__(self):
        """Async context manager entry."""
        timeout = aiohttp.ClientTimeout(total=self.settings.api_timeout)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={'User-Agent': self.settings.user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def search_documents(
        self,
        api_endpoint: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        max_results: Optional[int] = None
    ) -> List[APIDocument]:
        """Search for documents using government API."""
        
        try:
            # Rate limiting
            await self._respect_rate_limit()
            
            params = {'q': query}
            if filters:
                params.update(filters)
            if max_results:
                params['limit'] = max_results
            
            self.logger.info(f"Searching API {api_endpoint} for query: {query}")
            
            async with self.session.get(api_endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    documents = self._parse_api_response(data, api_endpoint)
                    self.logger.info(f"Found {len(documents)} documents from {api_endpoint}")
                    return documents
                else:
                    self.logger.error(f"API request failed: {response.status} - {response.reason}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"API search failed for {api_endpoint}: {e}")
            return []
    
    async def get_document_metadata(
        self,
        api_endpoint: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get document metadata from API."""
        
        try:
            # Rate limiting
            await self._respect_rate_limit()
            
            url = f"{api_endpoint}/{document_id}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    metadata = self._parse_document_metadata(data)
                    self.logger.info(f"Retrieved metadata for document {document_id}")
                    return metadata
                else:
                    self.logger.error(f"Document metadata request failed: {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Document metadata request failed: {e}")
            return None
    
    async def search_by_agency(
        self,
        api_endpoint: str,
        agency: str,
        max_results: Optional[int] = None
    ) -> List[APIDocument]:
        """Search for documents by government agency."""
        
        filters = {'agency': agency}
        return await self.search_documents(api_endpoint, "", filters, max_results)
    
    async def search_by_date_range(
        self,
        api_endpoint: str,
        start_date: str,
        end_date: str,
        max_results: Optional[int] = None
    ) -> List[APIDocument]:
        """Search for documents by date range."""
        
        filters = {
            'start_date': start_date,
            'end_date': end_date
        }
        return await self.search_documents(api_endpoint, "", filters, max_results)
    
    async def search_by_document_type(
        self,
        api_endpoint: str,
        document_type: str,
        max_results: Optional[int] = None
    ) -> List[APIDocument]:
        """Search for documents by type."""
        
        filters = {'document_type': document_type}
        return await self.search_documents(api_endpoint, "", filters, max_results)
    
    async def get_api_health(self, api_endpoint: str) -> Dict[str, Any]:
        """Check API health and status."""
        
        try:
            # Rate limiting
            await self._respect_rate_limit()
            
            health_url = urljoin(api_endpoint, "health")
            
            async with self.session.get(health_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'status': 'healthy',
                        'endpoint': api_endpoint,
                        'response_time': response.headers.get('x-response-time'),
                        'data': data
                    }
                else:
                    return {
                        'status': 'unhealthy',
                        'endpoint': api_endpoint,
                        'status_code': response.status,
                        'reason': response.reason
                    }
                    
        except Exception as e:
            return {
                'status': 'error',
                'endpoint': api_endpoint,
                'error': str(e)
            }
    
    async def search_multiple_apis(
        self,
        query: str,
        api_endpoints: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        max_results_per_api: Optional[int] = None
    ) -> List[APIDocument]:
        """Search multiple government APIs simultaneously."""
        
        if api_endpoints is None:
            api_endpoints = self.settings.government_apis
        
        self.logger.info(f"Searching {len(api_endpoints)} APIs for query: {query}")
        
        # Create tasks for concurrent API searches
        tasks = []
        for endpoint in api_endpoints:
            task = self.search_documents(endpoint, query, filters, max_results_per_api)
            tasks.append(task)
        
        # Execute all searches concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        all_documents = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"API search failed for {api_endpoints[i]}: {result}")
            else:
                all_documents.extend(result)
        
        # Remove duplicates based on URL
        unique_documents = self._remove_duplicates(all_documents)
        
        self.logger.info(f"Found {len(unique_documents)} unique documents from {len(api_endpoints)} APIs")
        return unique_documents
    
    def _parse_api_response(self, data: Dict[str, Any], api_endpoint: str) -> List[APIDocument]:
        """Parse API response into standardized format."""
        
        documents = []
        
        try:
            # Handle different API response formats
            if 'results' in data:
                items = data['results']
            elif 'data' in data:
                items = data['data']
            elif 'documents' in data:
                items = data['documents']
            elif isinstance(data, list):
                items = data
            else:
                self.logger.warning(f"Unknown API response format for {api_endpoint}")
                return []
            
            for item in items:
                try:
                    document = APIDocument(
                        id=item.get('id', ''),
                        title=item.get('title', 'Untitled'),
                        url=item.get('url', ''),
                        description=item.get('description'),
                        published_date=item.get('published_date'),
                        source='government_api',
                        api_endpoint=api_endpoint,
                        metadata=item,
                        extraction_timestamp=datetime.utcnow().isoformat()
                    )
                    documents.append(document)
                except Exception as e:
                    self.logger.error(f"Failed to parse API item: {e}")
                    continue
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Failed to parse API response: {e}")
            return []
    
    def _parse_document_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse document metadata."""
        
        return {
            'id': data.get('id'),
            'title': data.get('title'),
            'description': data.get('description'),
            'url': data.get('url'),
            'file_size': data.get('file_size'),
            'content_type': data.get('content_type'),
            'published_date': data.get('published_date'),
            'author': data.get('author'),
            'department': data.get('department'),
            'agency': data.get('agency'),
            'category': data.get('category'),
            'document_type': data.get('document_type'),
            'keywords': data.get('keywords', []),
            'language': data.get('language'),
            'version': data.get('version'),
            'checksum': data.get('checksum'),
            'access_level': data.get('access_level'),
            'classification': data.get('classification')
        }
    
    def _remove_duplicates(self, documents: List[APIDocument]) -> List[APIDocument]:
        """Remove duplicate documents based on URL."""
        
        seen_urls = set()
        unique_documents = []
        
        for doc in documents:
            if doc.url and doc.url not in seen_urls:
                seen_urls.add(doc.url)
                unique_documents.append(doc)
        
        return unique_documents
    
    async def _respect_rate_limit(self):
        """Respect rate limiting."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        
        min_interval = 60.0 / self.settings.rate_limit_requests_per_minute
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        self.last_request_time = asyncio.get_event_loop().time()
        self.request_count += 1
    
    async def get_api_stats(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        
        return {
            'total_requests': self.request_count,
            'api_endpoints': self.settings.government_apis,
            'rate_limit': self.settings.rate_limit_requests_per_minute,
            'timeout': self.settings.api_timeout,
            'retry_attempts': self.settings.api_retry_attempts
        }
    
    async def validate_api_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Validate all configured API endpoints."""
        
        results = {}
        
        for endpoint in self.settings.government_apis:
            try:
                health = await self.get_api_health(endpoint)
                results[endpoint] = health
            except Exception as e:
                results[endpoint] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
