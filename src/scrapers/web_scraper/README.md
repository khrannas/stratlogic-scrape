# Web Scraper Module

A comprehensive web scraping module for the StratLogic scraping system using Playwright with search engine integration, LLM keyword expansion, and content extraction capabilities.

## Features

- **Multi-Search Engine Support**: Google, Bing, and DuckDuckGo
- **Advanced Content Extraction**: Title, description, text, metadata, images, and links
- **LLM Integration**: OpenRouter and Gemini support for keyword expansion and content analysis
- **Browser Management**: Efficient browser pooling with user agent rotation
- **Rate Limiting**: Configurable delays and request limits
- **Error Handling**: Comprehensive error handling with fallback mechanisms
- **Quality Scoring**: Content quality assessment based on multiple factors

## Quick Start

```python
import asyncio
from src.scrapers.web_scraper import WebScraper, WebScraperSettings

async def main():
    # Create settings
    settings = WebScraperSettings(
        headless=True,
        max_browsers=2,
        max_results_per_keyword=10,
        search_delay=2.0
    )
    
    # Create web scraper
    async with WebScraper(settings) as scraper:
        # Scrape single URL
        result = await scraper.scrape_single_url("https://example.com")
        print(f"Title: {result.get('title')}")
        print(f"Word count: {result.get('word_count')}")
        
        # Scrape multiple keywords
        results = await scraper.scrape_web_content(
            keywords=["python programming", "web scraping"],
            job_id="test-job",
            user_id="test-user"
        )
        print(f"Total results: {results['total_results']}")

asyncio.run(main())
```

## Configuration

### Environment Variables

Set these environment variables to configure the web scraper:

```bash
# Playwright settings
WEB_SCRAPER_HEADLESS=true
WEB_SCRAPER_MAX_BROWSERS=5
WEB_SCRAPER_PAGE_TIMEOUT=30000

# Search settings
WEB_SCRAPER_MAX_RESULTS_PER_KEYWORD=10
WEB_SCRAPER_SEARCH_DELAY=2.0
WEB_SCRAPER_DEFAULT_SEARCH_ENGINES=google,bing

# Content extraction
WEB_SCRAPER_MAX_CONTENT_LENGTH=10000
WEB_SCRAPER_EXTRACT_IMAGES=true
WEB_SCRAPER_EXTRACT_LINKS=true

# Rate limiting
WEB_SCRAPER_REQUESTS_PER_MINUTE=30
WEB_SCRAPER_DELAY_BETWEEN_REQUESTS=2.0

# LLM settings
WEB_SCRAPER_LLM_PROVIDER=openrouter
WEB_SCRAPER_OPENROUTER_API_KEY=your_api_key
WEB_SCRAPER_GEMINI_API_KEY=your_api_key

# Proxy settings
WEB_SCRAPER_USE_PROXY=false
WEB_SCRAPER_PROXY_URL=http://proxy:8080

# User agent settings
WEB_SCRAPER_ROTATE_USER_AGENTS=true
WEB_SCRAPER_CUSTOM_USER_AGENT=your_custom_agent
```

### Settings Class

```python
from src.scrapers.web_scraper import WebScraperSettings

settings = WebScraperSettings(
    headless=True,                    # Run browser in headless mode
    max_browsers=5,                   # Maximum browsers in pool
    page_timeout=30000,               # Page load timeout (ms)
    max_results_per_keyword=10,       # Results per keyword
    search_delay=2.0,                 # Delay between searches
    default_search_engines=['google', 'bing'],  # Search engines to use
    extract_images=True,              # Extract images from pages
    extract_links=True,               # Extract links from pages
    llm_provider="openrouter",        # LLM provider (openrouter/gemini)
    requests_per_minute=30,           # Rate limiting
    delay_between_requests=2.0        # Delay between requests
)
```

## Components

### PlaywrightManager

Manages browser instances and pages with pooling and rotation.

```python
from src.scrapers.web_scraper import PlaywrightManager

async with PlaywrightManager(settings) as manager:
    browser = await manager.get_browser()
    page = await manager.create_page(browser)
    # Use page for scraping
    await manager.return_browser(browser)
```

### SearchEngineScraper

Scrapes search results from multiple search engines.

```python
from src.scrapers.web_scraper import SearchEngineScraper

scraper = SearchEngineScraper(playwright_manager, settings)

# Search single engine
google_results = await scraper.search_google("python programming", 10)

# Search multiple engines
all_results = await scraper.search_multiple_engines(
    "python programming", 
    ['google', 'bing'], 
    10
)
```

### ContentExtractor

Extracts and processes content from web pages.

```python
from src.scrapers.web_scraper import ContentExtractor

extractor = ContentExtractor(settings)

content = await extractor.extract_content(
    page, 
    "https://example.com",
    extract_images=True,
    extract_links=True
)

# Calculate content quality score
score = extractor.calculate_content_score(content)
```

### KeywordExpander

Expands keywords and analyzes content using LLM.

```python
from src.scrapers.web_scraper import KeywordExpander

expander = KeywordExpander(settings)

# Expand keywords
expanded_keywords = await expander.expand_keywords(
    ["python", "programming"], 
    max_expansions=10
)

# Analyze content
analysis = await expander.analyze_content("content text")

# Classify content
classification = await expander.classify_content(
    title="Title",
    description="Description", 
    text_content="Content"
)
```

### WebScraper

Main orchestrator that coordinates all components.

```python
from src.scrapers.web_scraper import WebScraper

async with WebScraper(settings) as scraper:
    # Scrape web content
    results = await scraper.scrape_web_content(
        keywords=["python", "programming"],
        job_id="job-123",
        user_id="user-456",
        max_results_per_keyword=10,
        search_engines=['google', 'bing'],
        expand_keywords=True,
        analyze_content=True
    )
    
    # Scrape single URL
    result = await scraper.scrape_single_url("https://example.com")
    
    # Get statistics
    stats = await scraper.get_scraping_stats()
    
    # Validate search engines
    engine_status = await scraper.validate_search_engines()
```

## Content Structure

Extracted content includes:

```python
{
    'url': 'https://example.com',
    'title': 'Page Title',
    'description': 'Page description',
    'text_content': 'Main text content',
    'metadata': {
        'domain': 'example.com',
        'language': 'en',
        'author': 'Author Name',
        'published_date': '2024-01-01',
        'keywords': ['keyword1', 'keyword2'],
        'content_type': 'article',
        'canonical_url': 'https://example.com/canonical'
    },
    'images': [
        {
            'src': 'https://example.com/image.jpg',
            'alt': 'Image alt text',
            'title': 'Image title'
        }
    ],
    'links': [
        {
            'url': 'https://example.com/link',
            'text': 'Link text',
            'title': 'Link title'
        }
    ],
    'content_hash': 'sha256_hash',
    'word_count': 1500,
    'content_score': 85.5,
    'extraction_timestamp': '2024-01-01T12:00:00Z',
    'keyword': 'search_keyword',
    'search_position': 1,
    'search_engine': 'google',
    'analysis': {
        'analysis': {...},
        'classification': {...},
        'key_phrases': [...]
    }
}
```

## Error Handling

The web scraper includes comprehensive error handling:

- **Network errors**: Automatic retry with exponential backoff
- **LLM API failures**: Fallback to original keywords/content
- **Browser crashes**: Automatic browser recreation
- **Rate limiting**: Respectful delays and request distribution
- **Invalid content**: Graceful degradation with error reporting

## Testing

Run the test suite:

```bash
python -m pytest tests/scrapers/web_scraper/ -v
```

## Ethical Considerations

The web scraper is designed with ethical scraping practices:

- **Rate limiting**: Configurable delays between requests
- **User agent rotation**: Respectful identification
- **Domain blocking**: Blocks social media and search engine domains
- **Robots.txt framework**: Ready for robots.txt compliance
- **Terms of service**: Framework for ToS compliance checking

## Performance

- **Browser pooling**: Efficient resource management
- **Async operations**: Non-blocking I/O throughout
- **Content caching**: Avoids duplicate content extraction
- **Memory management**: Proper cleanup and resource disposal

## Integration

The web scraper integrates with the existing StratLogic infrastructure:

- **Storage Manager**: Automatic artifact storage in MinIO
- **Job Manager**: Progress tracking and status updates
- **Database**: Metadata storage and job tracking
- **Authentication**: User-based access control

## Troubleshooting

### Common Issues

1. **Playwright not installed**: Run `playwright install`
2. **LLM API errors**: Check API keys and rate limits
3. **Browser crashes**: Reduce `max_browsers` or increase timeouts
4. **Rate limiting**: Increase delays between requests

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

This module is part of the StratLogic scraping system and follows the same licensing terms.
