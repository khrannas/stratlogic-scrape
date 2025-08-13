import aiohttp
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from .config import government_scraper_settings

class GovernmentAPIClient:
    """
    Client for interacting with Indonesian government APIs
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = government_scraper_settings
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=self.settings.api_timeout)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={'User-Agent': self.settings.user_agent}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def search_documents(
        self,
        api_endpoint: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for documents using government API

        Args:
            api_endpoint: API endpoint URL
            query: Search query
            filters: Additional filters
            max_results: Maximum number of results

        Returns:
            List of document dictionaries
        """
        try:
            params = {
                'q': query,
                'limit': max_results
            }
            if filters:
                params.update(filters)

            self.logger.info(f"Searching government API: {api_endpoint} with query: {query}")

            async with self.session.get(api_endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    documents = self._parse_api_response(data, api_endpoint)
                    self.logger.info(f"Found {len(documents)} documents from {api_endpoint}")
                    return documents
                else:
                    self.logger.error(f"API request failed: {response.status} - {api_endpoint}")
                    return []

        except Exception as e:
            self.logger.error(f"API search failed for {api_endpoint}: {e}")
            return []

    async def get_document_metadata(
        self,
        api_endpoint: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get document metadata from API

        Args:
            api_endpoint: API endpoint URL
            document_id: Document identifier

        Returns:
            Document metadata dictionary or None if failed
        """
        try:
            url = f"{api_endpoint}/{document_id}"

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    metadata = self._parse_document_metadata(data, api_endpoint)
                    return metadata
                else:
                    self.logger.error(f"Document metadata request failed: {response.status} - {url}")
                    return None

        except Exception as e:
            self.logger.error(f"Document metadata request failed for {document_id}: {e}")
            return None

    async def search_government_apis(
        self,
        keywords: List[str],
        max_results_per_api: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search multiple government APIs for documents

        Args:
            keywords: List of keywords to search for
            max_results_per_api: Maximum results per API

        Returns:
            List of documents from all APIs
        """
        all_documents = []

        for api_endpoint in self.settings.government_apis:
            try:
                self.logger.info(f"Searching government API: {api_endpoint}")

                for keyword in keywords:
                    try:
                        documents = await self.search_documents(
                            api_endpoint,
                            keyword,
                            max_results=max_results_per_api
                        )
                        all_documents.extend(documents)

                        # Add delay between requests
                        await asyncio.sleep(self.settings.api_delay_seconds)

                    except Exception as e:
                        self.logger.error(f"Failed to search {api_endpoint} with keyword {keyword}: {e}")
                        continue

                # Add delay between APIs
                await asyncio.sleep(self.settings.api_delay_seconds * 2)

            except Exception as e:
                self.logger.error(f"Failed to search API {api_endpoint}: {e}")
                continue

        return all_documents

    def _parse_api_response(self, data: Dict[str, Any], api_endpoint: str) -> List[Dict[str, Any]]:
        """
        Parse API response into standardized format

        Args:
            data: Raw API response data
            api_endpoint: API endpoint for source identification

        Returns:
            List of standardized document dictionaries
        """
        documents = []

        try:
            # Handle different API response formats
            if isinstance(data, dict):
                # Check for common response patterns
                if 'results' in data:
                    items = data['results']
                elif 'data' in data:
                    items = data['data']
                elif 'items' in data:
                    items = data['items']
                elif 'documents' in data:
                    items = data['documents']
                else:
                    # Assume the data itself is a list of documents
                    items = [data] if not isinstance(data, list) else data
            elif isinstance(data, list):
                items = data
            else:
                self.logger.warning(f"Unexpected API response format from {api_endpoint}")
                return []

            for item in items:
                if isinstance(item, dict):
                    document = self._standardize_document(item, api_endpoint)
                    if document:
                        documents.append(document)

        except Exception as e:
            self.logger.error(f"Failed to parse API response from {api_endpoint}: {e}")

        return documents

    def _standardize_document(self, item: Dict[str, Any], api_endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Standardize document data from API response

        Args:
            item: Raw document data from API
            api_endpoint: API endpoint for source identification

        Returns:
            Standardized document dictionary or None if invalid
        """
        try:
            # Extract common fields with fallbacks
            document = {
                'id': item.get('id') or item.get('document_id') or item.get('uuid'),
                'title': item.get('title') or item.get('name') or item.get('judul'),
                'url': item.get('url') or item.get('link') or item.get('file_url'),
                'description': item.get('description') or item.get('summary') or item.get('deskripsi'),
                'published_date': item.get('published_date') or item.get('created_date') or item.get('tanggal'),
                'author': item.get('author') or item.get('penulis') or item.get('creator'),
                'department': item.get('department') or item.get('kementerian') or item.get('agency'),
                'category': item.get('category') or item.get('kategori') or item.get('type'),
                'file_size': item.get('file_size') or item.get('size'),
                'content_type': item.get('content_type') or item.get('mime_type'),
                'source': 'government_api',
                'api_endpoint': api_endpoint,
                'extraction_timestamp': datetime.utcnow().isoformat()
            }

            # Remove None values
            document = {k: v for k, v in document.items() if v is not None}

            # Ensure required fields
            if not document.get('title') and not document.get('id'):
                return None

            return document

        except Exception as e:
            self.logger.error(f"Failed to standardize document: {e}")
            return None

    def _parse_document_metadata(self, data: Dict[str, Any], api_endpoint: str) -> Dict[str, Any]:
        """
        Parse document metadata from API response

        Args:
            data: Raw metadata from API
            api_endpoint: API endpoint for source identification

        Returns:
            Standardized metadata dictionary
        """
        try:
            metadata = self._standardize_document(data, api_endpoint)
            if metadata:
                metadata['source'] = 'government_api_metadata'
            return metadata or {}

        except Exception as e:
            self.logger.error(f"Failed to parse document metadata: {e}")
            return {}

    async def check_api_health(self, api_endpoint: str) -> bool:
        """
        Check if government API is healthy

        Args:
            api_endpoint: API endpoint to check

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            async with self.session.get(api_endpoint) as response:
                return response.status in [200, 401, 403]  # 401/403 means API exists but needs auth
        except Exception as e:
            self.logger.error(f"API health check failed for {api_endpoint}: {e}")
            return False

    async def check_all_apis_health(self) -> Dict[str, bool]:
        """
        Check health of all government APIs

        Returns:
            Dictionary mapping API endpoints to health status
        """
        health_status = {}

        for api_endpoint in self.settings.government_apis:
            try:
                health_status[api_endpoint] = await self.check_api_health(api_endpoint)
            except Exception as e:
                self.logger.error(f"Health check failed for {api_endpoint}: {e}")
                health_status[api_endpoint] = False

        return health_status
