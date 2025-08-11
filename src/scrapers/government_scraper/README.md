# Government Scraper Module

## Overview

The Government Scraper module provides comprehensive capabilities for scraping, processing, and analyzing Indonesian government documents. This module is designed to handle various document formats, integrate with government APIs, and provide intelligent content analysis.

## Features

### 🏛️ Government Website Crawling
- **Multi-domain Support**: Crawls Indonesian government websites (go.id domains)
- **Intelligent Document Discovery**: Automatically finds PDF, DOCX, Excel, and other document formats
- **Rate Limiting**: Respectful crawling with configurable delays and rate limits
- **Robots.txt Compliance**: Respects website crawling policies
- **Duplicate Detection**: Prevents processing of duplicate documents

### 🔌 Government API Integration
- **Multiple API Support**: Integrates with various Indonesian government APIs
- **Concurrent Processing**: Searches multiple APIs simultaneously
- **Error Handling**: Robust error handling and retry mechanisms
- **Health Monitoring**: API endpoint health checks and validation

### 📄 Document Processing
- **Multi-format Support**: PDF, DOCX, Excel, PowerPoint, and text files
- **Text Extraction**: High-quality text extraction from various document formats
- **Metadata Extraction**: Comprehensive metadata extraction
- **Content Analysis**: Language detection, sentiment analysis, and complexity assessment
- **Quality Scoring**: Intelligent document quality assessment

### 🤖 LLM-Powered Analysis
- **Content Classification**: Automatic document type classification
- **Keyword Extraction**: Government-specific keyword identification
- **Entity Recognition**: Government agency and entity extraction
- **Summarization**: Document summarization capabilities
- **Topic Identification**: Key topic extraction and categorization

### 🔒 Security and Compliance
- **Legal Compliance**: Designed for government data compliance
- **Access Controls**: Proper access control and authentication
- **Audit Logging**: Comprehensive audit trails
- **Data Privacy**: Secure handling of sensitive government data

## Architecture

```
Government Scraper
├── Website Crawler (Playwright/aiohttp)
├── API Client (aiohttp)
├── Document Processor (PyPDF2, python-docx, openpyxl)
├── Content Analyzer (LLM integration)
└── Storage Manager (MinIO integration)
```

## Installation

### Prerequisites

```bash
# Install required Python packages
pip install PyPDF2 python-docx openpyxl aiohttp beautifulsoup4 playwright
```

### Dependencies

The government scraper requires the following dependencies:

- **PyPDF2**: PDF text extraction
- **python-docx**: DOCX document processing
- **openpyxl**: Excel file processing
- **aiohttp**: Async HTTP client
- **beautifulsoup4**: HTML parsing
- **playwright**: Browser automation (optional)

## Quick Start

### Basic Usage

```python
import asyncio
from src.scrapers.government_scraper import (
    GovernmentScraper,
    GovernmentScraperSettings
)

async def main():
    # Initialize settings
    settings = GovernmentScraperSettings(
        max_pages_per_site=50,
        max_crawl_depth=2,
        crawl_delay=2.0
    )
    
    # Initialize scraper
    scraper = GovernmentScraper(settings)
    
    # Search for documents
    documents = await scraper.search_documents_by_keyword("peraturan", limit=10)
    
    for doc in documents:
        print(f"Title: {doc.get('title')}")
        print(f"URL: {doc.get('url')}")
        print(f"Type: {doc.get('document_type')}")
        print("---")

# Run the scraper
asyncio.run(main())
```

### Advanced Usage

```python
import asyncio
from src.scrapers.government_scraper import (
    GovernmentScraper,
    GovernmentScraperSettings,
    GovernmentWebsiteCrawler,
    GovernmentAPIClient,
    GovernmentDocumentProcessor
)

async def advanced_example():
    # Custom settings
    settings = GovernmentScraperSettings(
        max_pages_per_site=100,
        max_crawl_depth=3,
        crawl_delay=1.5,
        api_timeout=30,
        rate_limit_requests_per_minute=30,
        llm_provider="openrouter",
        openrouter_api_key="your-api-key"
    )
    
    # Initialize components
    website_crawler = GovernmentWebsiteCrawler(settings)
    api_client = GovernmentAPIClient(settings)
    document_processor = GovernmentDocumentProcessor(settings)
    
    # Initialize scraper with custom components
    scraper = GovernmentScraper(
        settings=settings,
        website_crawler=website_crawler,
        api_client=api_client,
        document_processor=document_processor
    )
    
    # Validate system
    validation = await scraper.validate_system()
    print(f"System validation: {validation}")
    
    # Search specific government websites
    keywords = ["anggaran", "laporan", "peraturan"]
    
    for keyword in keywords:
        documents = await scraper.search_documents_by_keyword(keyword, limit=20)
        print(f"Found {len(documents)} documents for '{keyword}'")
        
        # Process documents
        for doc in documents[:5]:  # Process first 5
            if doc.get('url'):
                # Download and process document
                processed_doc = await scraper._process_document(
                    doc, 
                    user_id="user-123", 
                    job_id="job-456"
                )
                if processed_doc:
                    print(f"Processed: {processed_doc.get('title')}")
                    print(f"Quality Score: {processed_doc.get('quality_score', 0):.2f}")
                    print(f"Language: {processed_doc.get('language')}")
                    print(f"Document Type: {processed_doc.get('analysis', {}).get('document_type')}")

# Run advanced example
asyncio.run(advanced_example())
```

## Configuration

### Environment Variables

The government scraper can be configured using environment variables:

```bash
# Website crawling
GOVERNMENT_SCRAPER_MAX_PAGES_PER_SITE=100
GOVERNMENT_SCRAPER_MAX_CRAWL_DEPTH=3
GOVERNMENT_SCRAPER_CRAWL_DELAY=2.0

# API settings
GOVERNMENT_SCRAPER_API_TIMEOUT=30
GOVERNMENT_SCRAPER_API_RETRY_ATTEMPTS=3

# Document processing
GOVERNMENT_SCRAPER_MAX_DOCUMENT_SIZE=52428800  # 50MB
GOVERNMENT_SCRAPER_EXTRACT_TEXT=true
GOVERNMENT_SCRAPER_EXTRACT_METADATA=true

# LLM settings
GOVERNMENT_SCRAPER_LLM_PROVIDER=openrouter
GOVERNMENT_SCRAPER_OPENROUTER_API_KEY=your-api-key
GOVERNMENT_SCRAPER_GEMINI_API_KEY=your-gemini-key

# Security and compliance
GOVERNMENT_SCRAPER_RESPECT_ROBOTS_TXT=true
GOVERNMENT_SCRAPER_RATE_LIMIT_REQUESTS_PER_MINUTE=30
GOVERNMENT_SCRAPER_USER_AGENT="StratLogic-GovernmentScraper/1.0 (compliance research)"
```

### Configuration Class

```python
from src.scrapers.government_scraper import GovernmentScraperSettings

# Default settings
settings = GovernmentScraperSettings()

# Custom settings
settings = GovernmentScraperSettings(
    max_pages_per_site=50,
    max_crawl_depth=2,
    crawl_delay=1.0,
    api_timeout=15,
    llm_provider="gemini",
    gemini_api_key="your-key"
)
```

## API Reference

### GovernmentScraper

Main orchestrator class for government document scraping.

#### Methods

- `scrape_government_documents(keywords, job_id, user_id, sources, max_documents_per_keyword)`: Main scraping orchestration
- `search_documents_by_keyword(keyword, limit)`: Search for documents by keyword
- `get_document_by_id(document_id)`: Retrieve document by ID
- `get_scraping_stats()`: Get scraping statistics
- `validate_system()`: Validate system components

### GovernmentWebsiteCrawler

Crawls Indonesian government websites for documents.

#### Methods

- `crawl_government_site(base_url, max_pages, max_depth)`: Crawl government website
- `get_crawl_stats()`: Get crawling statistics

### GovernmentAPIClient

Interfaces with government APIs.

#### Methods

- `search_documents(api_endpoint, query, filters, max_results)`: Search API for documents
- `search_multiple_apis(query, api_endpoints, filters, max_results_per_api)`: Search multiple APIs
- `get_api_health(api_endpoint)`: Check API health
- `validate_api_endpoints()`: Validate all configured endpoints

### GovernmentDocumentProcessor

Processes and analyzes government documents.

#### Methods

- `process_document(document_url, document_data, content_type)`: Process document
- `get_processing_stats()`: Get processing statistics

## Data Structures

### DocumentInfo

```python
@dataclass
class DocumentInfo:
    url: str
    title: str
    file_size: Optional[int]
    content_type: Optional[str]
    last_modified: Optional[str]
    extraction_timestamp: str
    domain: str
    document_type: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
```

### APIDocument

```python
@dataclass
class APIDocument:
    id: str
    title: str
    url: str
    description: Optional[str]
    published_date: Optional[str]
    source: str
    api_endpoint: str
    metadata: Dict[str, Any]
    extraction_timestamp: str
```

### ProcessedDocument

```python
@dataclass
class ProcessedDocument:
    url: str
    text_content: str
    metadata: Dict[str, Any]
    analysis: Dict[str, Any]
    content_hash: str
    word_count: int
    processing_timestamp: str
    document_type: str
    language: Optional[str] = None
    quality_score: float = 0.0
```

### ScrapingJob

```python
@dataclass
class ScrapingJob:
    job_id: str
    user_id: str
    keywords: List[str]
    sources: List[str]
    max_documents_per_keyword: int
    status: str
    progress: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
```

### ScrapingResult

```python
@dataclass
class ScrapingResult:
    job_id: str
    total_documents: int
    keywords_processed: int
    documents: List[Dict[str, Any]]
    processing_time: float
    success_rate: float
    error_count: int
```

## Error Handling

The government scraper implements comprehensive error handling:

### Network Errors
- Automatic retry with exponential backoff
- Graceful degradation when services are unavailable
- Detailed error logging and reporting

### Document Processing Errors
- Fallback mechanisms for unsupported formats
- Partial processing when full processing fails
- Error recovery and continuation

### API Errors
- Rate limit handling
- Authentication error recovery
- Service unavailability handling

## Performance Considerations

### Optimization Strategies
- **Concurrent Processing**: Parallel API requests and document processing
- **Connection Pooling**: Efficient HTTP connection management
- **Caching**: Intelligent caching of frequently accessed data
- **Rate Limiting**: Respectful rate limiting to avoid service disruption

### Resource Management
- **Memory Management**: Efficient memory usage for large documents
- **Connection Limits**: Configurable connection pool sizes
- **Timeout Handling**: Proper timeout management for all operations

## Security and Compliance

### Legal Compliance
- **Government Data Handling**: Proper handling of government data
- **Access Controls**: Role-based access control
- **Audit Logging**: Comprehensive audit trails
- **Data Classification**: Proper data classification and handling

### Security Measures
- **Authentication**: Secure authentication mechanisms
- **Encryption**: Data encryption in transit and at rest
- **Input Validation**: Strict input validation
- **Error Handling**: Secure error handling without information leakage

## Testing

### Unit Tests

```bash
# Run unit tests
pytest tests/scrapers/government_scraper/test_government_scraper.py -v
```

### Integration Tests

```bash
# Run integration tests
pytest tests/scrapers/government_scraper/test_government_scraper.py::TestGovernmentScraperIntegration -v
```

### Test Coverage

```bash
# Run with coverage
pytest tests/scrapers/government_scraper/test_government_scraper.py --cov=src.scrapers.government_scraper --cov-report=html
```

## Examples

### Example 1: Basic Document Search

```python
import asyncio
from src.scrapers.government_scraper import GovernmentScraper, GovernmentScraperSettings

async def search_documents():
    settings = GovernmentScraperSettings()
    scraper = GovernmentScraper(settings)
    
    # Search for budget documents
    documents = await scraper.search_documents_by_keyword("anggaran", limit=10)
    
    for doc in documents:
        print(f"Found: {doc.get('title')} - {doc.get('url')}")

asyncio.run(search_documents())
```

### Example 2: Website Crawling

```python
import asyncio
from src.scrapers.government_scraper import GovernmentWebsiteCrawler, GovernmentScraperSettings

async def crawl_website():
    settings = GovernmentScraperSettings(max_pages_per_site=20)
    crawler = GovernmentWebsiteCrawler(settings)
    
    # Crawl government website
    documents = await crawler.crawl_government_site("https://www.setkab.go.id")
    
    print(f"Found {len(documents)} documents")
    for doc in documents[:5]:
        print(f"- {doc.title} ({doc.document_type})")

asyncio.run(crawl_website())
```

### Example 3: Document Processing

```python
import asyncio
from src.scrapers.government_scraper import GovernmentDocumentProcessor, GovernmentScraperSettings

async def process_document():
    settings = GovernmentScraperSettings()
    processor = GovernmentDocumentProcessor(settings)
    
    # Sample document data (in practice, this would be downloaded)
    document_data = b"Sample PDF content..."
    content_type = "application/pdf"
    
    processed = await processor.process_document(
        "https://example.com/document.pdf",
        document_data,
        content_type
    )
    
    if processed:
        print(f"Language: {processed.language}")
        print(f"Quality Score: {processed.quality_score}")
        print(f"Document Type: {processed.document_type}")

asyncio.run(process_document())
```

## Troubleshooting

### Common Issues

1. **PDF Processing Errors**
   - Ensure PyPDF2 is installed: `pip install PyPDF2`
   - Check if PDF is password-protected or corrupted

2. **API Connection Errors**
   - Verify API endpoints are accessible
   - Check rate limiting settings
   - Ensure proper authentication

3. **Memory Issues**
   - Reduce `max_document_size` setting
   - Process documents in smaller batches
   - Monitor memory usage

4. **Rate Limiting**
   - Increase `crawl_delay` setting
   - Reduce `rate_limit_requests_per_minute`
   - Implement exponential backoff

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or for specific components
logging.getLogger('src.scrapers.government_scraper').setLevel(logging.DEBUG)
```

## Contributing

### Development Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Install development dependencies: `pip install pytest pytest-asyncio pytest-cov`
4. Run tests: `pytest tests/scrapers/government_scraper/`

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Add comprehensive docstrings
- Write unit tests for new features

### Testing

- Write unit tests for all new functionality
- Ensure test coverage remains above 80%
- Run integration tests before submitting

## License

This module is part of the StratLogic Scraping System and follows the same licensing terms.

## Support

For support and questions:
- Check the troubleshooting section
- Review the examples
- Run the test suite
- Check system validation results

## Changelog

### Version 1.0.0
- Initial release
- Government website crawling
- API integration
- Document processing
- Content analysis
- Security and compliance features
