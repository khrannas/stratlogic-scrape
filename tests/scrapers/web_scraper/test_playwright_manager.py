"""
Tests for PlaywrightManager component
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.scrapers.web_scraper import PlaywrightManager


class TestPlaywrightManager:
    """Test PlaywrightManager functionality"""

    @pytest.fixture
    def playwright_manager(self):
        """Create PlaywrightManager instance for testing"""
        return PlaywrightManager(headless=True, max_browsers=3)

    def test_initialization(self, playwright_manager):
        """Test PlaywrightManager initialization"""
        assert playwright_manager.headless is True
        assert playwright_manager.max_browsers == 3
        assert len(playwright_manager.user_agents) > 0
        assert isinstance(playwright_manager.user_agents[0], str)

    def test_user_agent_rotation(self, playwright_manager):
        """Test user agent rotation"""
        user_agent = playwright_manager.user_agents[0]
        assert isinstance(user_agent, str)
        assert len(user_agent) > 0
        assert "Mozilla" in user_agent

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager"""
        with patch('src.scrapers.web_scraper.playwright_manager.async_playwright') as mock_playwright:
            mock_playwright_instance = Mock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_playwright_instance)
            mock_playwright_instance.stop = AsyncMock()

            async with PlaywrightManager() as manager:
                assert manager is not None
                assert hasattr(manager, 'playwright')

    @pytest.mark.asyncio
    async def test_browser_pool_management(self, playwright_manager):
        """Test browser pool management"""
        # Mock playwright
        mock_playwright = Mock()
        mock_browser = Mock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch('src.scrapers.web_scraper.playwright_manager.async_playwright') as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(return_value=mock_playwright)

            # Test getting browser
            browser = await playwright_manager.get_browser()
            assert browser == mock_browser

    @pytest.mark.asyncio
    async def test_create_page(self, playwright_manager):
        """Test page creation"""
        mock_browser = Mock()
        mock_page = Mock()
        mock_browser.new_page = AsyncMock(return_value=mock_page)

        page = await playwright_manager.create_page(mock_browser)
        assert page == mock_page
        mock_page.set_extra_http_headers.assert_called_once()
        mock_page.set_viewport_size.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_for_load(self, playwright_manager):
        """Test wait for load functionality"""
        mock_page = Mock()

        await playwright_manager.wait_for_load(mock_page)
        mock_page.wait_for_load_state.assert_called_once_with("domcontentloaded")

    @pytest.mark.asyncio
    async def test_return_browser(self, playwright_manager):
        """Test returning browser to pool"""
        mock_browser = Mock()

        # Test returning browser when pool is not full
        await playwright_manager.return_browser(mock_browser)
        assert len(playwright_manager.browser_pool) == 1

        # Test returning browser when pool is full
        for _ in range(playwright_manager.max_browsers):
            await playwright_manager.return_browser(Mock())

        # Should close browser when pool is full
        await playwright_manager.return_browser(mock_browser)
        mock_browser.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_cleanup(self, playwright_manager):
        """Test cleanup on stop"""
        mock_playwright = Mock()
        mock_browser = Mock()
        playwright_manager.playwright = mock_playwright
        playwright_manager.browser_pool = [mock_browser]

        await playwright_manager.stop()

        mock_browser.close.assert_called_once()
        assert len(playwright_manager.browser_pool) == 0
        mock_playwright.stop.assert_called_once()
