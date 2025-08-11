# Paper Scraper Module

## Overview

The Paper Scraper module provides comprehensive academic paper scraping capabilities for the StratLogic scraping system. It integrates with multiple academic sources including arXiv, CrossRef, and uses Grobid for PDF processing and LLM-powered content analysis.

## Features

### Core Functionality
- **arXiv Integration**: Search and download papers from arXiv using the official API
- **CrossRef Integration**: Access academic metadata from CrossRef
- **PDF Processing**: Extract text and metadata from PDFs using Grobid
- **Content Analysis**: LLM-powered paper analysis including summarization, keyword extraction, and quality assessment
- **Citation Analysis**: Extract and analyze citations from papers
- **Parallel Processing**: Support for concurrent paper processing
- **Rate Limiting**: Intelligent rate limiting to respect API limits
- **Error Handling**: Robust error handling and retry mechanisms

### Advanced Features
- **Multi-source Search**: Search across multiple academic sources simultaneously
- **Duplicate Detection**: Automatic removal of duplicate papers
- **Content Quality Scoring**: ML-based quality assessment
- **Author Search**: Search for papers by specific authors
- **Paper Recommendations**: Get related paper recommendations
- **Health Monitoring**: Service health checks for all components

## Architecture

### Components

1. **ArxivClient**: Handles arXiv API interactions
2. **GrobidClient**: Manages PDF processing with Grobid
3. **CrossRefClient**: Interfaces with CrossRef API
4. **PaperContentAnalyzer**: Performs LLM-powered content analysis
5. **PaperScraper**: Main orchestrator coordinating all components

### Data Flow

```
User Query → PaperScraper → Multiple Sources → Content Processing → Analysis → Storage
     ↓              ↓              ↓              ↓              ↓         ↓
  Queries    ArxivClient    GrobidClient    ContentAnalyzer   Results   MinIO
             CrossRefClient
```

## Installation

### Prerequisites

1. **Python 3.11+**
2. **Grobid Service**: Running Grobid server for PDF processing
3. **LLM Service**: OpenRouter or Gemini API for content analysis

### Dependencies

```bash
pip install arxiv aiohttp pydantic pydantic-settings
```

### Environment Variables

```bash
# Paper Scraper Configuration
PAPER_SCRAPER_ARXIV_MAX_RESULTS=100
PAPER_SCRAPER_ARXIV_DELAY_SECONDS=3.0
PAPER_SCRAPER_GROBID_URL=http://localhost:8070
PAPER_SCRAPER_EXTRACT_PDFS=true
PAPER_SCRAPER_ANALYZE_CONTENT=true

# LLM Configuration
PAPER_SCRAPER_LLM_PROVIDER=openrouter
PAPER_SCRAPER_OPENROUTER_API_KEY=your_openrouter_key
PAPER_SCRAPER_GEMINI_API_KEY=your_gemini_key

# CrossRef Configuration
PAPER_SCRAPER_CROSSREF_USER_AGENT=StratLogicScraper/1.0
PAPER_SCRAPER_CROSSREF_MAX_RESULTS=100
```

## Quick Start

### Basic Usage

```python
import asyncio
from src.scrapers.paper_scraper import (
    PaperScraperSettings,
    ArxivClient,
    GrobidClient,
    CrossRefClient,
    PaperContentAnalyzer,
    PaperScraper
)

async def main():
    # Initialize configuration
    config = PaperScraperSettings()
    
    # Initialize components
    arxiv_client = ArxivClient(config)
    grobid_client = GrobidClient(config)
    crossref_client = CrossRefClient(config)
    content_analyzer = PaperContentAnalyzer(config, llm_service)
    
    # Initialize main scraper
    scraper = PaperScraper(
        config=config,
        arxiv_client=arxiv_client,
        grobid_client=grobid_client,
        crossref_client=crossref_client,
        content_analyzer=content_analyzer
    )
    
    # Search for papers
    result = await scraper.scrape_papers(
        queries=["machine learning", "artificial intelligence"],
        user_id="user123",
        sources=["arxiv", "crossref"],
        max_results_per_query=10,
        download_pdfs=True,
        analyze_content=True
    )
    
    print(f"Found {result.total_papers_found} papers")
    print(f"Processed {result.papers_processed} papers")

asyncio.run(main())
```

### Advanced Usage

```python
# Search by author
author_papers = await scraper.search_by_author(
    "Yann LeCun",
    sources=["arxiv", "crossref"],
    max_results=20
)

# Get paper by ID
paper = await scraper.get_paper_by_id("2103.12345", source="arxiv")

# Get paper recommendations
recommendations = await scraper.get_paper_recommendations(
    "2103.12345", 
    source="arxiv",
    max_recommendations=10
)

# Get system statistics
stats = await scraper.get_scraping_stats()
```

## Configuration

### PaperScraperSettings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `arxiv_max_results` | int | 100 | Maximum results from arXiv |
| `arxiv_delay_seconds` | float | 3.0 | Delay between arXiv requests |
| `grobid_url` | str | "http://localhost:8070" | Grobid service URL |
| `extract_pdfs` | bool | True | Extract PDF content using Grobid |
| `analyze_content` | bool | True | Analyze content using LLM |
| `llm_provider` | str | "openrouter" | LLM provider (openrouter/gemini) |
| `parallel_processing` | bool | True | Enable parallel processing |
| `max_concurrent_downloads` | int | 5 | Maximum concurrent PDF downloads |
| `max_concurrent_analysis` | int | 3 | Maximum concurrent LLM analysis |

## API Reference

### PaperScraper

#### `scrape_papers(queries, user_id, **kwargs)`

Main method to scrape papers based on queries.

**Parameters:**
- `queries` (List[str]): List of search queries
- `user_id` (str): User ID for the scraping job
- `sources` (List[str]): Sources to search (arxiv, crossref, semantic_scholar)
- `max_results_per_query` (int): Maximum results per query
- `download_pdfs` (bool): Whether to download PDFs
- `analyze_content` (bool): Whether to analyze content with LLM
- `extract_citations` (bool): Whether to extract citations
- `parallel_processing` (bool): Whether to use parallel processing

**Returns:**
- `ScrapingResult`: Object containing scraping results and statistics

#### `search_by_author(author_name, **kwargs)`

Search for papers by author name.

**Parameters:**
- `author_name` (str): Name of the author
- `sources` (List[str]): Sources to search
- `max_results` (int): Maximum results per source

**Returns:**
- `List[Dict]`: List of papers by the author

#### `get_paper_by_id(paper_id, source)`

Get a specific paper by ID.

**Parameters:**
- `paper_id` (str): Paper ID (arXiv ID or DOI)
- `source` (str): Source of the paper (arxiv or crossref)

**Returns:**
- `Dict`: Paper data or None if not found

### ArxivClient

#### `search_papers(query, **kwargs)`

Search for papers on arXiv.

**Parameters:**
- `query` (str): Search query string
- `max_results` (int): Maximum number of results
- `sort_by` (str): Sort criteria (relevance, lastUpdatedDate, submittedDate)
- `sort_order` (str): Sort order (ascending, descending)

**Returns:**
- `List[Dict]`: List of paper metadata dictionaries

#### `download_paper_pdf(arxiv_id, output_path)`

Download a paper's PDF file.

**Parameters:**
- `arxiv_id` (str): arXiv paper ID
- `output_path` (str): Path to save the PDF (optional)

**Returns:**
- `str`: Path to downloaded PDF file or None if failed

### GrobidClient

#### `extract_pdf_content(pdf_file_path, filename)`

Extract full text and metadata from PDF using Grobid.

**Parameters:**
- `pdf_file_path` (str): Path to the PDF file
- `filename` (str): Optional filename for the PDF

**Returns:**
- `Dict`: Dictionary containing extracted content and metadata

#### `extract_citations(pdf_file_path, filename)`

Extract citations from PDF.

**Parameters:**
- `pdf_file_path` (str): Path to the PDF file
- `filename` (str): Optional filename for the PDF

**Returns:**
- `List[Dict]`: List of citation dictionaries

### PaperContentAnalyzer

#### `analyze_paper(paper_data, **kwargs)`

Perform comprehensive analysis of a paper.

**Parameters:**
- `paper_data` (Dict): Paper metadata and content
- `include_citations` (bool): Whether to analyze citations
- `include_recommendations` (bool): Whether to generate recommendations

**Returns:**
- `AnalysisResult`: Object containing analysis data

## Data Structures

### ScrapingResult

```python
@dataclass
class ScrapingResult:
    job_id: str
    total_papers_found: int
    papers_processed: int
    papers_analyzed: int
    papers_downloaded: int
    total_processing_time: float
    results: List[Dict[str, Any]]
    errors: List[str]
    created_at: datetime
```

### AnalysisResult

```python
@dataclass
class AnalysisResult:
    summary: str
    keywords: List[str]
    topics: List[str]
    quality_score: float
    language: str
    content_type: str
    key_phrases: List[str]
    entities: List[Dict[str, Any]]
    sentiment: str
    complexity_score: float
    citation_analysis: Dict[str, Any]
    recommendations: List[str]
```

## Error Handling

The module includes comprehensive error handling:

- **API Failures**: Graceful handling of API timeouts and errors
- **Rate Limiting**: Automatic retry with exponential backoff
- **PDF Processing**: Fallback mechanisms for PDF extraction failures
- **LLM Failures**: Fallback analysis methods when LLM service is unavailable
- **Network Issues**: Connection retry logic for network failures

## Performance Considerations

### Rate Limiting
- arXiv: 3-second delay between requests (configurable)
- CrossRef: 1-second delay between requests (configurable)
- Grobid: Configurable timeout and retry settings

### Parallel Processing
- Configurable concurrency limits for downloads and analysis
- Semaphore-based rate limiting to prevent overwhelming services
- Async/await patterns for non-blocking operations

### Memory Management
- Streaming PDF processing to handle large files
- Content truncation for LLM analysis to stay within token limits
- Automatic cleanup of temporary files

## Testing

Run the test suite:

```bash
# Run all paper scraper tests
pytest tests/scrapers/paper_scraper/

# Run specific test file
pytest tests/scrapers/paper_scraper/test_paper_scraper.py

# Run with coverage
pytest tests/scrapers/paper_scraper/ --cov=src.scrapers.paper_scraper
```

## Examples

See `examples/paper_scraper_example.py` for a complete usage example.

## Troubleshooting

### Common Issues

1. **Grobid Service Not Available**
   - Ensure Grobid is running on the configured URL
   - Check firewall settings and network connectivity
   - Verify Grobid service health with `check_service_health()`

2. **arXiv API Rate Limiting**
   - Increase delay between requests in configuration
   - Implement exponential backoff for retries
   - Monitor rate limit usage

3. **LLM Service Failures**
   - Verify API keys are correctly configured
   - Check service availability and quotas
   - Use fallback analysis methods when LLM is unavailable

4. **PDF Download Failures**
   - Check network connectivity
   - Verify arXiv paper IDs are valid
   - Ensure sufficient disk space for downloads

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check service health:

```python
# Check all services
stats = await scraper.get_scraping_stats()
print(f"arXiv Health: {stats['arxiv_health']}")
print(f"Grobid Health: {stats['grobid_health']}")
print(f"CrossRef Health: {stats['crossref_health']}")
```

## Contributing

1. Follow the existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure all tests pass before submitting

## License

This module is part of the StratLogic scraping system and follows the same licensing terms.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the test examples
3. Check service health and configuration
4. Enable debug logging for detailed error information
