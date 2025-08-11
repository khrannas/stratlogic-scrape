# Task 08: Government Document Scraper

## Overview
Implement a specialized scraper for Indonesian government documents, including official websites, document repositories, and API integrations.

## Priority: Medium
## Estimated Time: 3-4 days
## Dependencies: Task 01-07 (Infrastructure, Database, Storage, API, Auth, Web Scraper, Paper Scraper)

## Checklist

### 8.1 Indonesian Government Sources
- [ ] Research Indonesian government websites
- [ ] Identify official document repositories
- [ ] Map government agency websites
- [ ] Identify API endpoints
- [ ] Document access patterns and rate limits

### 8.2 Government Website Scraping
- [ ] Implement government website crawler
- [ ] Add document link discovery
- [ ] Implement PDF document extraction
- [ ] Add metadata extraction
- [ ] Implement content validation

### 8.3 Document Processing (LLM Integration)
- [ ] Implement PDF text extraction
- [ ] Add document classification using OpenRouter/Gemini
- [ ] Implement metadata extraction
- [ ] Add content summarization with cost-effective LLM
- [ ] Implement document quality scoring

### 8.4 API Integration
- [ ] Research available government APIs
- [ ] Implement API client wrappers
- [ ] Add authentication handling
- [ ] Implement rate limiting
- [ ] Add error handling and retry logic

### 8.5 Government Scraper Orchestrator
- [ ] Create government scraping job manager
- [ ] Implement source prioritization
- [ ] Add progress tracking
- [ ] Implement result aggregation
- [ ] Add document deduplication

## Key Components

### Government Website Crawler
```python
# src/scrapers/government_scraper/website_crawler.py
from playwright.async_api import Page
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse

class GovernmentWebsiteCrawler:
    def __init__(self, playwright_manager):
        self.playwright_manager = playwright_manager
        self.logger = logging.getLogger(__name__)
        
        # Indonesian government domains
        self.gov_domains = [
            'go.id',
            'kemendagri.go.id',
            'kemendikbud.go.id',
            'kemenkeu.go.id',
            'kemenlu.go.id',
            'kemenkumham.go.id',
            'kemenperin.go.id',
            'kemenkes.go.id',
            'kemenag.go.id',
            'kemenkopmk.go.id',
            'kemenpan.go.id',
            'kemenristek.go.id',
            'kemenparekraf.go.id',
            'kemenkominfo.go.id',
            'kemenko.go.id',
            'setkab.go.id',
            'bappenas.go.id',
            'bkn.go.id',
            'bpkp.go.id',
            'bppt.go.id'
        ]
    
    async def crawl_government_site(
        self,
        base_url: str,
        max_pages: int = 100,
        max_depth: int = 3
    ) -> List[Dict[str, Any]]:
        """Crawl government website for documents"""
        
        if not self._is_government_domain(base_url):
            self.logger.warning(f"Not a government domain: {base_url}")
            return []
        
        documents = []
        visited_urls = set()
        urls_to_visit = [(base_url, 0)]  # (url, depth)
        
        browser = await self.playwright_manager.get_browser()
        
        try:
            while urls_to_visit and len(documents) < max_pages:
                url, depth = urls_to_visit.pop(0)
                
                if url in visited_urls or depth > max_depth:
                    continue
                
                visited_urls.add(url)
                
                try:
                    page = await self.playwright_manager.create_page(browser)
                    
                    # Navigate to page
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    
                    # Extract documents from current page
                    page_documents = await self._extract_documents_from_page(page, url)
                    documents.extend(page_documents)
                    
                    # Find new links if not at max depth
                    if depth < max_depth:
                        new_links = await self._extract_links_from_page(page, base_url)
                        for link in new_links:
                            if link not in visited_urls:
                                urls_to_visit.append((link, depth + 1))
                    
                    await page.close()
                    
                except Exception as e:
                    self.logger.error(f"Failed to crawl {url}: {e}")
                    continue
                
                # Add delay to be respectful
                await asyncio.sleep(2)
        
        finally:
            await self.playwright_manager.return_browser(browser)
        
        return documents
    
    async def _extract_documents_from_page(
        self,
        page: Page,
        page_url: str
    ) -> List[Dict[str, Any]]:
        """Extract documents from a single page"""
        
        documents = []
        
        try:
            # Get page content
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for document links
            document_links = self._find_document_links(soup, page_url)
            
            for link in document_links:
                try:
                    document = await self._extract_document_info(page, link)
                    if document:
                        documents.append(document)
                except Exception as e:
                    self.logger.error(f"Failed to extract document {link}: {e}")
                    continue
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Failed to extract documents from {page_url}: {e}")
            return []
    
    def _find_document_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find document links on the page"""
        
        document_links = []
        
        # Common document file extensions
        doc_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                # Make URL absolute
                absolute_url = urljoin(base_url, href)
                
                # Check if it's a document
                if any(ext in absolute_url.lower() for ext in doc_extensions):
                    document_links.append(absolute_url)
        
        return document_links
    
    async def _extract_document_info(
        self,
        page: Page,
        document_url: str
    ) -> Optional[Dict[str, Any]]:
        """Extract information about a document"""
        
        try:
            # Get document metadata
            response = await page.goto(document_url, wait_until="domcontentloaded")
            
            if response and response.status == 200:
                headers = response.headers
                
                return {
                    'url': document_url,
                    'title': self._extract_document_title(page),
                    'file_size': headers.get('content-length'),
                    'content_type': headers.get('content-type'),
                    'last_modified': headers.get('last-modified'),
                    'extraction_timestamp': datetime.utcnow().isoformat()
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to extract document info from {document_url}: {e}")
            return None
    
    def _is_government_domain(self, url: str) -> bool:
        """Check if URL is from a government domain"""
        domain = urlparse(url).netloc.lower()
        return any(gov_domain in domain for gov_domain in self.gov_domains)
```

### Government API Client
```python
# src/scrapers/government_scraper/api_client.py
import aiohttp
import logging
from typing import List, Dict, Any, Optional
import asyncio

class GovernmentAPIClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_documents(
        self,
        api_endpoint: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for documents using government API"""
        
        try:
            params = {'q': query}
            if filters:
                params.update(filters)
            
            async with self.session.get(api_endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_api_response(data)
                else:
                    self.logger.error(f"API request failed: {response.status}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"API search failed: {e}")
            return []
    
    async def get_document_metadata(
        self,
        api_endpoint: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get document metadata from API"""
        
        try:
            url = f"{api_endpoint}/{document_id}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_document_metadata(data)
                else:
                    self.logger.error(f"Document metadata request failed: {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Document metadata request failed: {e}")
            return None
    
    def _parse_api_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse API response"""
        # Implementation depends on specific API format
        documents = []
        
        if 'results' in data:
            for item in data['results']:
                document = {
                    'id': item.get('id'),
                    'title': item.get('title'),
                    'url': item.get('url'),
                    'description': item.get('description'),
                    'published_date': item.get('published_date'),
                    'source': 'government_api'
                }
                documents.append(document)
        
        return documents
    
    def _parse_document_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse document metadata"""
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
            'category': data.get('category')
        }
```

### Document Processor
```python
# src/scrapers/government_scraper/document_processor.py
import PyPDF2
import docx
import logging
from typing import Dict, Any, Optional
import hashlib
from datetime import datetime

class GovernmentDocumentProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def process_document(
        self,
        document_url: str,
        document_data: bytes,
        content_type: str
    ) -> Optional[Dict[str, Any]]:
        """Process government document"""
        
        try:
            # Extract text content
            text_content = await self._extract_text(document_data, content_type)
            
            if not text_content:
                return None
            
            # Extract metadata
            metadata = await self._extract_metadata(document_data, content_type)
            
            # Analyze content
            analysis = await self._analyze_content(text_content)
            
            # Calculate content hash
            content_hash = hashlib.sha256(text_content.encode()).hexdigest()
            
            return {
                'url': document_url,
                'text_content': text_content,
                'metadata': metadata,
                'analysis': analysis,
                'content_hash': content_hash,
                'word_count': len(text_content.split()),
                'processing_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Document processing failed: {e}")
            return None
    
    async def _extract_text(
        self,
        document_data: bytes,
        content_type: str
    ) -> Optional[str]:
        """Extract text from document"""
        
        try:
            if 'pdf' in content_type.lower():
                return self._extract_pdf_text(document_data)
            elif 'word' in content_type.lower() or 'docx' in content_type.lower():
                return self._extract_docx_text(document_data)
            elif 'text' in content_type.lower():
                return document_data.decode('utf-8', errors='ignore')
            else:
                self.logger.warning(f"Unsupported content type: {content_type}")
                return None
                
        except Exception as e:
            self.logger.error(f"Text extraction failed: {e}")
            return None
    
    def _extract_pdf_text(self, pdf_data: bytes) -> str:
        """Extract text from PDF"""
        
        text_content = []
        
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
            
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
            
            return '\n\n'.join(text_content)
            
        except Exception as e:
            self.logger.error(f"PDF text extraction failed: {e}")
            return ""
    
    def _extract_docx_text(self, docx_data: bytes) -> str:
        """Extract text from DOCX"""
        
        try:
            doc = docx.Document(io.BytesIO(docx_data))
            
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text_content.append(paragraph.text)
            
            return '\n\n'.join(text_content)
            
        except Exception as e:
            self.logger.error(f"DOCX text extraction failed: {e}")
            return ""
    
    async def _extract_metadata(
        self,
        document_data: bytes,
        content_type: str
    ) -> Dict[str, Any]:
        """Extract document metadata"""
        
        metadata = {
            'content_type': content_type,
            'file_size': len(document_data),
            'extraction_timestamp': datetime.utcnow().isoformat()
        }
        
        # Add content-type specific metadata
        if 'pdf' in content_type.lower():
            metadata.update(self._extract_pdf_metadata(document_data))
        elif 'word' in content_type.lower() or 'docx' in content_type.lower():
            metadata.update(self._extract_docx_metadata(document_data))
        
        return metadata
    
    async def _analyze_content(self, text_content: str) -> Dict[str, Any]:
        """Analyze document content"""
        
        # Basic content analysis
        analysis = {
            'language': self._detect_language(text_content),
            'document_type': self._classify_document_type(text_content),
            'key_topics': self._extract_key_topics(text_content),
            'entities': self._extract_entities(text_content),
            'summary': await self._generate_summary(text_content)
        }
        
        return analysis
    
    def _detect_language(self, text: str) -> str:
        """Detect document language"""
        # Simple language detection (can be enhanced with proper library)
        indonesian_words = ['yang', 'dan', 'atau', 'dalam', 'untuk', 'dengan', 'oleh']
        english_words = ['the', 'and', 'or', 'in', 'for', 'with', 'by']
        
        text_lower = text.lower()
        indonesian_count = sum(1 for word in indonesian_words if word in text_lower)
        english_count = sum(1 for word in english_words if word in text_lower)
        
        return 'id' if indonesian_count > english_count else 'en'
    
    def _classify_document_type(self, text: str) -> str:
        """Classify document type"""
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['peraturan', 'regulation', 'law', 'undang-undang']):
            return 'regulation'
        elif any(word in text_lower for word in ['laporan', 'report', 'annual']):
            return 'report'
        elif any(word in text_lower for word in ['keputusan', 'decision', 'decree']):
            return 'decision'
        elif any(word in text_lower for word in ['surat', 'letter', 'circular']):
            return 'letter'
        else:
            return 'document'
```

### Government Scraper Orchestrator
```python
# src/scrapers/government_scraper/government_scraper.py
from typing import List, Dict, Any
import asyncio
import logging
from datetime import datetime

class GovernmentScraper:
    def __init__(
        self,
        website_crawler: GovernmentWebsiteCrawler,
        api_client: GovernmentAPIClient,
        document_processor: GovernmentDocumentProcessor,
        storage_manager,
        job_manager
    ):
        self.website_crawler = website_crawler
        self.api_client = api_client
        self.document_processor = document_processor
        self.storage_manager = storage_manager
        self.job_manager = job_manager
        self.logger = logging.getLogger(__name__)
    
    async def scrape_government_documents(
        self,
        keywords: List[str],
        job_id: str,
        user_id: str,
        sources: List[str] = ['websites', 'apis'],
        max_documents_per_keyword: int = 20
    ) -> Dict[str, Any]:
        """Main government document scraping orchestration"""
        
        try:
            # Update job status
            await self.job_manager.update_job_status(job_id, 'running')
            
            all_documents = []
            total_keywords = len(keywords)
            
            for i, keyword in enumerate(keywords):
                self.logger.info(f"Processing keyword {i+1}/{total_keywords}: {keyword}")
                
                # Update progress
                progress = int((i / total_keywords) * 100)
                await self.job_manager.update_job_progress(job_id, progress)
                
                documents = []
                
                # Search websites
                if 'websites' in sources:
                    website_docs = await self._search_government_websites(keyword)
                    documents.extend(website_docs)
                
                # Search APIs
                if 'apis' in sources:
                    api_docs = await self._search_government_apis(keyword)
                    documents.extend(api_docs)
                
                # Remove duplicates
                unique_documents = self._remove_duplicates(documents)
                
                # Process documents
                for doc in unique_documents[:max_documents_per_keyword]:
                    try:
                        processed_doc = await self._process_document(doc, user_id, job_id)
                        if processed_doc:
                            processed_doc['keyword'] = keyword
                            all_documents.append(processed_doc)
                    
                    except Exception as e:
                        self.logger.error(f"Failed to process document: {e}")
                        continue
                
                # Add delay between keywords
                await asyncio.sleep(3)
            
            # Update job completion
            await self.job_manager.update_job_status(job_id, 'completed')
            await self.job_manager.update_job_progress(job_id, 100)
            
            return {
                'job_id': job_id,
                'total_documents': len(all_documents),
                'keywords_processed': len(keywords),
                'documents': all_documents
            }
            
        except Exception as e:
            self.logger.error(f"Government document scraping failed: {e}")
            await self.job_manager.update_job_status(job_id, 'failed', str(e))
            raise
    
    async def _search_government_websites(self, keyword: str) -> List[Dict[str, Any]]:
        """Search government websites for documents"""
        
        documents = []
        
        # List of government websites to search
        government_sites = [
            'https://www.setkab.go.id',
            'https://www.kemendagri.go.id',
            'https://www.kemendikbud.go.id',
            'https://www.kemenkeu.go.id',
            # Add more government sites
        ]
        
        for site in government_sites:
            try:
                site_documents = await self.website_crawler.crawl_government_site(site)
                # Filter by keyword
                filtered_docs = [
                    doc for doc in site_documents 
                    if keyword.lower() in doc.get('title', '').lower()
                ]
                documents.extend(filtered_docs)
                
            except Exception as e:
                self.logger.error(f"Failed to search {site}: {e}")
                continue
        
        return documents
    
    async def _search_government_apis(self, keyword: str) -> List[Dict[str, Any]]:
        """Search government APIs for documents"""
        
        documents = []
        
        # List of government APIs
        api_endpoints = [
            'https://api.data.go.id/documents',
            'https://api.peraturan.go.id/search',
            # Add more API endpoints
        ]
        
        async with self.api_client as client:
            for endpoint in api_endpoints:
                try:
                    api_documents = await client.search_documents(endpoint, keyword)
                    documents.extend(api_documents)
                    
                except Exception as e:
                    self.logger.error(f"Failed to search API {endpoint}: {e}")
                    continue
        
        return documents
    
    async def _process_document(
        self,
        document: Dict[str, Any],
        user_id: str,
        job_id: str
    ) -> Optional[Dict[str, Any]]:
        """Process individual document"""
        
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
                        document.update(processed_doc)
            
            # Store document as artifact
            artifact_id = await self._store_document(document, user_id, job_id)
            document['artifact_id'] = artifact_id
            
            return document
            
        except Exception as e:
            self.logger.error(f"Document processing failed: {e}")
            return None
    
    async def _download_document(self, url: str) -> Optional[Dict[str, Any]]:
        """Download document from URL"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
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
        """Store document as artifact"""
        
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
                'source': 'government'
            },
            user_id=user_id
        )
        
        return artifact_id
    
    def _remove_duplicates(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate documents"""
        seen_urls = set()
        unique_documents = []
        
        for doc in documents:
            url = doc.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_documents.append(doc)
        
        return unique_documents
```

## Files to Create

1. `src/scrapers/government_scraper/__init__.py`
2. `src/scrapers/government_scraper/website_crawler.py`
3. `src/scrapers/government_scraper/api_client.py`
4. `src/scrapers/government_scraper/document_processor.py`
5. `src/scrapers/government_scraper/government_scraper.py`
6. `src/scrapers/government_scraper/config.py`
7. `tests/scrapers/government_scraper/`

## Configuration

```python
# src/scrapers/government_scraper/config.py
class GovernmentScraperSettings(BaseSettings):
    # Website crawling
    max_pages_per_site: int = 100
    max_crawl_depth: int = 3
    crawl_delay: float = 2.0
    
    # API settings
    api_timeout: int = 30
    api_retry_attempts: int = 3
    
    # Document processing
    max_document_size: int = 50 * 1024 * 1024  # 50MB
    supported_formats: List[str] = ['pdf', 'docx', 'txt']
    
    # Government domains
    government_domains: List[str] = [
        'go.id',
        'kemendagri.go.id',
        'kemendikbud.go.id',
        # Add more domains
    ]
    
    # LLM settings
    llm_provider: str = "openrouter"  # "openrouter" or "gemini"
    openrouter_api_key: str = ""
    gemini_api_key: str = ""
    
    class Config:
        env_prefix = "GOVERNMENT_SCRAPER_"
```

## Testing

### Unit Tests
- [ ] Test website crawler
- [ ] Test API client
- [ ] Test document processor
- [ ] Test government scraper orchestration

### Integration Tests
- [ ] Test with actual government websites
- [ ] Test document download and processing
- [ ] Test API integration
- [ ] Test content storage

## Documentation

- [ ] Create government scraper setup guide
- [ ] Document government website patterns
- [ ] Create API integration guide
- [ ] Document document processing features

## Risk Assessment and Mitigation

### High Risk Items

#### 1. Legal Compliance and Government Regulations
**Risk**: Government data collection must comply with strict legal and regulatory requirements.

**Mitigation Strategies**:
- **Legal Framework**: Comprehensive legal compliance documentation and procedures
- **Government Permissions**: Obtain necessary permissions and authorizations
- **Data Classification**: Implement government data classification and handling
- **Access Controls**: Strict access controls for government data
- **Audit Trail**: Comprehensive audit logging for all government data access
- **Compliance Monitoring**: Regular compliance audits and monitoring
- **Legal Review**: Regular legal review of government data practices
- **Transparency**: Clear documentation of data collection and usage practices

#### 2. Data Security and National Security
**Risk**: Government documents may contain sensitive or classified information.

**Mitigation Strategies**:
- **Security Clearance**: Implement security clearance requirements for data access
- **Data Encryption**: Encrypt all government data at rest and in transit
- **Access Logging**: Comprehensive logging of all data access and modifications
- **Data Masking**: Mask sensitive information in non-production environments
- **Secure Storage**: Use government-approved secure storage solutions
- **Incident Response**: Implement security incident response procedures
- **Regular Audits**: Regular security audits and penetration testing
- **Compliance Reporting**: Regular compliance reporting to authorities

### Medium Risk Items

#### 1. API Reliability and Rate Limits
**Risk**: Government APIs may have strict rate limits or become unavailable.

**Mitigation Strategies**:
- **Rate Limiting**: Implement intelligent rate limiting and backoff strategies
- **API Monitoring**: Real-time monitoring of government API availability
- **Fallback Mechanisms**: Implement fallback data collection methods
- **Request Queuing**: Implement priority-based request queuing
- **Service Health Checks**: Regular health checks of government services
- **Graceful Degradation**: Continue operation when some services are unavailable
- **Alternative Sources**: Maintain alternative government data sources

#### 2. Data Quality and Accuracy
**Risk**: Government documents may be outdated, incomplete, or contain errors.

**Mitigation Strategies**:
- **Data Validation**: Comprehensive validation of government document data
- **Source Verification**: Cross-reference data across multiple government sources
- **Quality Scoring**: Implement quality assessment for government documents
- **Version Control**: Implement document versioning and change tracking
- **Freshness Validation**: Check document publication dates and relevance
- **Expert Review**: Implement mechanisms for expert content review
- **Quality Metrics**: Track and monitor data quality KPIs

## Notes

- Respect government website robots.txt and rate limits
- Implement proper error handling for government APIs
- Consider implementing document versioning
- Add support for multiple Indonesian government domains
- Implement document classification by government agency
- Consider adding support for official government APIs
- Implement comprehensive security and compliance measures
- Set up automated compliance monitoring
- Use secure and ethical government data practices
- Implement proper error handling and logging

## Next Steps

After completing this task, proceed to:
- Task 09: Advanced Features and Optimization
- Task 10: System Integration and Testing
- Task 11: Deployment and Production Setup

## Completion Criteria

- [ ] Government website crawling works
- [ ] API integration is functional
- [ ] Document processing is implemented
- [ ] Content storage and retrieval work
- [ ] All tests are passing
- [ ] Documentation is complete
- [ ] Error handling is robust
- [ ] Rate limiting is implemented
