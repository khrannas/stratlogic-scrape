import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.scrapers.web_scraper import (
    WebScraper,
    PlaywrightManager,
    SearchEngineScraper,
    ContentExtractor
)

@pytest.fixture
def mock_playwright_manager():
    """Mock PlaywrightManager for testing"""
    manager = Mock(spec=PlaywrightManager)
    manager.get_browser = AsyncMock()
    manager.create_page = AsyncMock()
    manager.return_browser = AsyncMock()
    manager.wait_for_load = AsyncMock()
    return manager

@pytest.fixture
def mock_content_extractor():
    """Mock ContentExtractor for testing"""
    extractor = Mock(spec=ContentExtractor)
    extractor.extract_content = AsyncMock()
    extractor.validate_content = Mock(return_value=True)
    return extractor

@pytest.fixture
def web_scraper_instance(mock_playwright_manager, mock_content_extractor):
    """Create WebScraper instance with mocked dependencies"""
    scraper = WebScraper()
    scraper.playwright_manager = mock_playwright_manager
    scraper.content_extractor = mock_content_extractor
    return scraper

class TestPlaywrightManager:
    """Test PlaywrightManager functionality"""

    @pytest.mark.asyncio
    async def test_playwright_manager_initialization(self):
        """Test PlaywrightManager initialization"""
        manager = PlaywrightManager(headless=True, max_browsers=3)
        assert manager.headless is True
        assert manager.max_browsers == 3
        assert len(manager.user_agents) > 0

    def test_user_agent_rotation(self):
        """Test user agent rotation"""
        manager = PlaywrightManager()
        user_agent = manager.user_agents[0]
        assert isinstance(user_agent, str)
        assert len(user_agent) > 0

class TestSearchEngineScraper:
    """Test SearchEngineScraper functionality"""

    def test_search_engine_scraper_initialization(self, mock_playwright_manager):
        """Test SearchEngineScraper initialization"""
        scraper = SearchEngineScraper(mock_playwright_manager)
        assert scraper.playwright_manager == mock_playwright_manager
        assert scraper.min_delay == 2.0

    def test_url_validation(self, mock_playwright_manager):
        """Test URL validation"""
        scraper = SearchEngineScraper(mock_playwright_manager)

        # Valid URLs
        assert scraper.validate_url("https://example.com") is True
        assert scraper.validate_url("http://test.org/path") is True

        # Invalid URLs
        assert scraper.validate_url("not-a-url") is False
        assert scraper.validate_url("ftp://example.com") is False
        assert scraper.validate_url("") is False

    def test_duplicate_removal(self, mock_playwright_manager):
        """Test duplicate result removal"""
        scraper = SearchEngineScraper(mock_playwright_manager)

        results = [
            {"url": "https://example.com", "title": "Example"},
            {"url": "https://example.com", "title": "Example Duplicate"},
            {"url": "https://test.com", "title": "Test"}
        ]

        unique_results = scraper._remove_duplicates(results)
        assert len(unique_results) == 2
        assert unique_results[0]["url"] == "https://example.com"
        assert unique_results[1]["url"] == "https://test.com"

class TestContentExtractor:
    """Test ContentExtractor functionality"""

    def test_content_extractor_initialization(self):
        """Test ContentExtractor initialization"""
        extractor = ContentExtractor()
        assert len(extractor.noise_patterns) > 0
        assert len(extractor.text_cleanup_patterns) > 0

    def test_content_validation(self):
        """Test content validation"""
        extractor = ContentExtractor()

        # Valid content
        valid_content = {
            "url": "https://example.com",
            "title": "Example Title",
            "text_content": "This is some content with enough words to pass validation."
        }
        assert extractor.validate_content(valid_content) is True

        # Invalid content - missing fields
        invalid_content = {
            "url": "https://example.com",
            "title": "Example Title"
            # Missing text_content
        }
        assert extractor.validate_content(invalid_content) is False

        # Invalid content - too short
        short_content = {
            "url": "https://example.com",
            "title": "Example Title",
            "text_content": "Too short"
        }
        assert extractor.validate_content(short_content) is False

    def test_text_cleaning(self):
        """Test text cleaning functionality"""
        extractor = ContentExtractor()

        dirty_text = "  This   is   dirty   text  \n\n  with   extra   spaces  "
        cleaned_text = extractor._clean_text(dirty_text)

        assert "   " not in cleaned_text  # No multiple spaces
        assert cleaned_text.startswith("This")  # No leading spaces
        assert cleaned_text.endswith("spaces")  # No trailing spaces

class TestWebScraper:
    """Test WebScraper functionality"""

    def test_web_scraper_initialization(self, web_scraper_instance):
        """Test WebScraper initialization"""
        assert web_scraper_instance.playwright_manager is not None
        assert web_scraper_instance.content_extractor is not None

    def test_url_validation(self, web_scraper_instance):
        """Test URL validation in WebScraper"""
        # Valid URLs
        assert web_scraper_instance._validate_url("https://example.com") is True
        assert web_scraper_instance._validate_url("http://test.org") is True

        # Invalid URLs
        assert web_scraper_instance._validate_url("not-a-url") is False
        assert web_scraper_instance._validate_url("") is False
        assert web_scraper_instance._validate_url("ftp://example.com") is False

    def test_duplicate_removal(self, web_scraper_instance):
        """Test duplicate removal in WebScraper"""
        results = [
            {"url": "https://example.com", "title": "Example"},
            {"url": "https://example.com", "title": "Example Duplicate"},
            {"url": "https://test.com", "title": "Test"}
        ]

        unique_results = web_scraper_instance._remove_duplicates(results)
        assert len(unique_results) == 2
        assert unique_results[0]["url"] == "https://example.com"
        assert unique_results[1]["url"] == "https://test.com"

    @pytest.mark.asyncio
    async def test_get_scraping_stats(self, web_scraper_instance):
        """Test getting scraping statistics"""
        stats = await web_scraper_instance.get_scraping_stats()

        assert isinstance(stats, dict)
        assert "playwright_pool_status" in stats
        assert "search_stats" in stats
        assert "llm_provider_info" in stats
        assert "timestamp" in stats

@pytest.mark.asyncio
async def test_async_context_manager():
    """Test PlaywrightManager async context manager"""
    async with PlaywrightManager() as manager:
        assert manager is not None
        assert hasattr(manager, 'playwright')
