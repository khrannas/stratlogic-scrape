"""
Tests for SearchEngineScraper component
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from src.scrapers.web_scraper import SearchEngineScraper, PlaywrightManager


class TestSearchEngineScraper:
    """Test SearchEngineScraper functionality"""

    @pytest.fixture
    def mock_playwright_manager(self):
        """Mock PlaywrightManager for testing"""
        manager = Mock(spec=PlaywrightManager)
        manager.get_browser = AsyncMock()
        manager.create_page = AsyncMock()
        manager.return_browser = AsyncMock()
        manager.wait_for_load = AsyncMock()
        return manager

    @pytest.fixture
    def search_engine_scraper(self, mock_playwright_manager):
        """Create SearchEngineScraper instance"""
        return SearchEngineScraper(mock_playwright_manager)

    def test_initialization(self, search_engine_scraper, mock_playwright_manager):
        """Test SearchEngineScraper initialization"""
        assert search_engine_scraper.playwright_manager == mock_playwright_manager
        assert search_engine_scraper.min_delay == 2.0

    @pytest.mark.asyncio
    async def test_rate_limiting(self, search_engine_scraper):
        """Test rate limiting functionality"""
        start_time = datetime.now()

        await search_engine_scraper._rate_limit(0.1)  # Small delay for testing

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        assert elapsed >= 0.1

    @pytest.mark.asyncio
    async def test_google_search(self, search_engine_scraper, mock_playwright_manager):
        """Test Google search functionality"""
        mock_browser = Mock()
        mock_page = Mock()
        mock_playwright_manager.get_browser.return_value = mock_browser
        mock_playwright_manager.create_page.return_value = mock_page

        # Mock page evaluation results
        mock_results = [
            {
                "title": "Test Result",
                "url": "https://example.com",
                "snippet": "Test snippet",
                "position": 1,
                "source": "google"
            }
        ]
        mock_page.evaluate = AsyncMock(return_value=mock_results)

        results = await search_engine_scraper.search_google("test query", max_results=5)

        assert len(results) == 1
        assert results[0]["title"] == "Test Result"
        assert results[0]["url"] == "https://example.com"
        mock_page.goto.assert_called_once()

    @pytest.mark.asyncio
    async def test_bing_search(self, search_engine_scraper, mock_playwright_manager):
        """Test Bing search functionality"""
        mock_browser = Mock()
        mock_page = Mock()
        mock_playwright_manager.get_browser.return_value = mock_browser
        mock_playwright_manager.create_page.return_value = mock_page

        mock_results = [
            {
                "title": "Bing Result",
                "url": "https://bing-example.com",
                "snippet": "Bing snippet",
                "position": 1,
                "source": "bing"
            }
        ]
        mock_page.evaluate = AsyncMock(return_value=mock_results)

        results = await search_engine_scraper.search_bing("test query", max_results=5)

        assert len(results) == 1
        assert results[0]["title"] == "Bing Result"
        assert results[0]["source"] == "bing"

    @pytest.mark.asyncio
    async def test_duckduckgo_search(self, search_engine_scraper, mock_playwright_manager):
        """Test DuckDuckGo search functionality"""
        mock_browser = Mock()
        mock_page = Mock()
        mock_playwright_manager.get_browser.return_value = mock_browser
        mock_playwright_manager.create_page.return_value = mock_page

        mock_results = [
            {
                "title": "DDG Result",
                "url": "https://ddg-example.com",
                "snippet": "DDG snippet",
                "position": 1,
                "source": "duckduckgo"
            }
        ]
        mock_page.evaluate = AsyncMock(return_value=mock_results)

        results = await search_engine_scraper.search_duckduckgo("test query", max_results=5)

        assert len(results) == 1
        assert results[0]["title"] == "DDG Result"
        assert results[0]["source"] == "duckduckgo"

    @pytest.mark.asyncio
    async def test_search_error_handling(self, search_engine_scraper, mock_playwright_manager):
        """Test error handling in search methods"""
        mock_playwright_manager.get_browser.side_effect = Exception("Browser error")

        results = await search_engine_scraper.search_google("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_with_empty_results(self, search_engine_scraper, mock_playwright_manager):
        """Test search with empty results"""
        mock_browser = Mock()
        mock_page = Mock()
        mock_playwright_manager.get_browser.return_value = mock_browser
        mock_playwright_manager.create_page.return_value = mock_page

        mock_page.evaluate = AsyncMock(return_value=[])

        results = await search_engine_scraper.search_google("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_max_results_limit(self, search_engine_scraper, mock_playwright_manager):
        """Test that max_results limit is respected"""
        mock_browser = Mock()
        mock_page = Mock()
        mock_playwright_manager.get_browser.return_value = mock_browser
        mock_playwright_manager.create_page.return_value = mock_page

        # Return more results than requested
        mock_results = [
            {"title": f"Result {i}", "url": f"https://example{i}.com", "snippet": f"Snippet {i}", "position": i, "source": "google"}
            for i in range(1, 11)
        ]
        mock_page.evaluate = AsyncMock(return_value=mock_results)

        results = await search_engine_scraper.search_google("test query", max_results=5)
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_search_delay_respect(self, search_engine_scraper, mock_playwright_manager):
        """Test that search delay is respected"""
        mock_browser = Mock()
        mock_page = Mock()
        mock_playwright_manager.get_browser.return_value = mock_browser
        mock_playwright_manager.create_page.return_value = mock_page

        mock_page.evaluate = AsyncMock(return_value=[])

        start_time = datetime.now()
        await search_engine_scraper.search_google("test query", delay=0.1)
        end_time = datetime.now()

        elapsed = (end_time - start_time).total_seconds()
        assert elapsed >= 0.1

    @pytest.mark.asyncio
    async def test_multiple_search_engines(self, search_engine_scraper, mock_playwright_manager):
        """Test searching multiple engines"""
        mock_browser = Mock()
        mock_page = Mock()
        mock_playwright_manager.get_browser.return_value = mock_browser
        mock_playwright_manager.create_page.return_value = mock_page

        # Different results for different engines
        google_results = [{"title": "Google Result", "url": "https://google.com", "snippet": "Google", "position": 1, "source": "google"}]
        bing_results = [{"title": "Bing Result", "url": "https://bing.com", "snippet": "Bing", "position": 1, "source": "bing"}]

        mock_page.evaluate = AsyncMock(side_effect=[google_results, bing_results])

        # Test Google
        google_search = await search_engine_scraper.search_google("test")
        assert len(google_search) == 1
        assert google_search[0]["source"] == "google"

        # Test Bing
        bing_search = await search_engine_scraper.search_bing("test")
        assert len(bing_search) == 1
        assert bing_search[0]["source"] == "bing"
