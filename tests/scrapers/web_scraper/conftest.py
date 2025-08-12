"""
Shared test fixtures for web scraper tests
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from src.scrapers.web_scraper import (
    PlaywrightManager,
    SearchEngineScraper,
    ContentExtractor,
    WebScraper,
    WebScraperSettings
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def web_scraper_settings():
    """Create WebScraperSettings instance for testing"""
    return WebScraperSettings(
        headless=True,
        max_browsers=2,
        max_results_per_keyword=5,
        search_delay=0.1,  # Fast for testing
        extract_images=True,
        extract_links=True
    )


@pytest.fixture
def mock_playwright_manager():
    """Create a mocked PlaywrightManager"""
    manager = Mock(spec=PlaywrightManager)
    manager.headless = True
    manager.max_browsers = 2
    manager.user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ]

    # Setup async methods
    manager.get_browser = AsyncMock()
    manager.create_page = AsyncMock()
    manager.return_browser = AsyncMock()
    manager.wait_for_load = AsyncMock()
    manager.start = AsyncMock()
    manager.stop = AsyncMock()

    return manager


@pytest.fixture
def mock_search_engine_scraper(mock_playwright_manager):
    """Create a mocked SearchEngineScraper"""
    scraper = Mock(spec=SearchEngineScraper)
    scraper.playwright_manager = mock_playwright_manager
    scraper.min_delay = 0.1

    # Setup async methods
    scraper.search_google = AsyncMock()
    scraper.search_bing = AsyncMock()
    scraper.search_duckduckgo = AsyncMock()
    scraper._rate_limit = AsyncMock()

    return scraper


@pytest.fixture
def mock_content_extractor():
    """Create a mocked ContentExtractor"""
    extractor = Mock(spec=ContentExtractor)
    extractor.noise_patterns = [r'<script[^>]*>.*?</script>']
    extractor.text_cleanup_patterns = [(r'\s+', ' ')]

    # Setup async methods
    extractor.extract_content = AsyncMock()

    # Setup sync methods
    extractor.validate_content = Mock(return_value=True)
    extractor._extract_title = Mock(return_value="Test Title")
    extractor._extract_description = Mock(return_value="Test Description")
    extractor._extract_text = Mock(return_value="Test content")
    extractor._extract_metadata = Mock(return_value={})
    extractor._extract_images = Mock(return_value=[])
    extractor._extract_links = Mock(return_value=[])
    extractor._clean_text = Mock(return_value="Clean text")

    return extractor


@pytest.fixture
def mock_storage_manager():
    """Create a mocked storage manager"""
    storage_manager = Mock()
    storage_manager.create_artifact = AsyncMock(return_value="test-artifact-id")
    storage_manager.upload_artifact = AsyncMock()
    storage_manager.get_artifact = AsyncMock()
    storage_manager.delete_artifact = AsyncMock()

    return storage_manager


@pytest.fixture
def mock_job_manager():
    """Create a mocked job manager"""
    job_manager = Mock()
    job_manager.update_job_status = AsyncMock()
    job_manager.update_job_progress = AsyncMock()
    job_manager.get_job = AsyncMock()
    job_manager.create_job = AsyncMock(return_value="test-job-id")

    return job_manager


@pytest.fixture
def mock_web_scraper(mock_playwright_manager, mock_search_engine_scraper,
                     mock_content_extractor, mock_storage_manager, mock_job_manager):
    """Create a WebScraper instance with mocked dependencies"""
    scraper = WebScraper()
    scraper.playwright_manager = mock_playwright_manager
    scraper.search_engine_scraper = mock_search_engine_scraper
    scraper.content_extractor = mock_content_extractor
    scraper.storage_manager = mock_storage_manager
    scraper.job_manager = mock_job_manager

    return scraper


@pytest.fixture
def sample_search_results():
    """Sample search results for testing"""
    return [
        {
            "title": "Test Result 1",
            "url": "https://example1.com",
            "snippet": "Test snippet 1",
            "position": 1,
            "source": "google"
        },
        {
            "title": "Test Result 2",
            "url": "https://example2.com",
            "snippet": "Test snippet 2",
            "position": 2,
            "source": "google"
        }
    ]


@pytest.fixture
def sample_content():
    """Sample extracted content for testing"""
    return {
        "url": "https://example.com",
        "title": "Test Page",
        "description": "Test description",
        "text_content": "This is test content with enough words to pass validation.",
        "content_hash": "test-hash-123",
        "word_count": 10,
        "metadata": {
            "url": "https://example.com",
            "domain": "example.com",
            "language": "en",
            "author": "Test Author",
            "keywords": ["test", "web", "scraping"]
        },
        "images": [
            {
                "src": "https://example.com/image.jpg",
                "alt": "Test image",
                "width": "100",
                "height": "100"
            }
        ],
        "links": [
            {
                "url": "https://example.com/link",
                "text": "Test link",
                "title": "Link title"
            }
        ],
        "extraction_timestamp": "2023-01-01T00:00:00"
    }


@pytest.fixture
def sample_html():
    """Sample HTML content for testing"""
    return """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
            <meta property="og:title" content="OG Title">
            <meta property="og:description" content="OG Description">
            <meta name="author" content="Test Author">
            <meta name="keywords" content="test, web, scraping">
        </head>
        <body>
            <h1>Main Title</h1>
            <p>This is some content with <a href="https://example.com">a link</a>.</p>
            <img src="https://example.com/image.jpg" alt="Test image" width="100" height="100">
            <img src="/relative/image2.jpg" alt="Relative image">
            <script>console.log('test');</script>
            <style>.test { color: red; }</style>
        </body>
    </html>
    """


@pytest.fixture
def mock_page(sample_html):
    """Create a mocked page with sample HTML content"""
    page = Mock()
    page.content = AsyncMock(return_value=sample_html)
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.evaluate = AsyncMock()
    page.set_extra_http_headers = AsyncMock()
    page.set_viewport_size = AsyncMock()
    page.close = AsyncMock()

    return page


@pytest.fixture
def mock_browser(mock_page):
    """Create a mocked browser"""
    browser = Mock()
    browser.new_page = AsyncMock(return_value=mock_page)
    browser.close = AsyncMock()

    return browser


@pytest.fixture
def test_keywords():
    """Sample keywords for testing"""
    return ["test", "web scraping", "python", "playwright"]


@pytest.fixture
def test_job_data():
    """Sample job data for testing"""
    return {
        "job_id": "test-job-123",
        "user_id": "test-user-456",
        "keywords": ["test", "web scraping"],
        "max_results_per_keyword": 5,
        "search_engines": ["google", "bing"],
        "status": "pending"
    }
