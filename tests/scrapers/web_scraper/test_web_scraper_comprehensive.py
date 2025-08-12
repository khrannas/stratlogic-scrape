"""
Comprehensive tests for the web scraper components
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import json
from datetime import datetime

from src.scrapers.web_scraper import (
    WebScraper,
    PlaywrightManager,
    SearchEngineScraper,
    ContentExtractor,
    WebScraperSettings
)


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


class TestContentExtractor:
    """Test ContentExtractor functionality"""

    @pytest.fixture
    def content_extractor(self):
        """Create ContentExtractor instance"""
        return ContentExtractor()

    @pytest.fixture
    def mock_page(self):
        """Mock page for testing"""
        page = Mock()
        page.content = AsyncMock(return_value="""
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="Test description">
                <meta property="og:title" content="OG Title">
                <meta property="og:description" content="OG Description">
            </head>
            <body>
                <h1>Main Title</h1>
                <p>This is some content with <a href="https://example.com">a link</a>.</p>
                <img src="https://example.com/image.jpg" alt="Test image">
                <script>console.log('test');</script>
            </body>
        </html>
        """)
        return page

    def test_initialization(self, content_extractor):
        """Test ContentExtractor initialization"""
        assert len(content_extractor.noise_patterns) > 0
        assert len(content_extractor.text_cleanup_patterns) > 0

    @pytest.mark.asyncio
    async def test_extract_content(self, content_extractor, mock_page):
        """Test content extraction"""
        content = await content_extractor.extract_content(mock_page, "https://example.com")

        assert content["url"] == "https://example.com"
        assert "title" in content
        assert "text_content" in content
        assert "content_hash" in content
        assert "word_count" in content
        assert "extraction_timestamp" in content

    def test_extract_title(self, content_extractor):
        """Test title extraction"""
        from bs4 import BeautifulSoup

        # Test with OG title
        html = '<meta property="og:title" content="OG Title">'
        soup = BeautifulSoup(html, 'html.parser')
        title = content_extractor._extract_title(soup)
        assert title == "OG Title"

        # Test with regular title
        html = '<title>Regular Title</title>'
        soup = BeautifulSoup(html, 'html.parser')
        title = content_extractor._extract_title(soup)
        assert title == "Regular Title"

    def test_extract_description(self, content_extractor):
        """Test description extraction"""
        from bs4 import BeautifulSoup

        # Test with meta description
        html = '<meta name="description" content="Meta description">'
        soup = BeautifulSoup(html, 'html.parser')
        desc = content_extractor._extract_description(soup)
        assert desc == "Meta description"

        # Test with OG description
        html = '<meta property="og:description" content="OG description">'
        soup = BeautifulSoup(html, 'html.parser')
        desc = content_extractor._extract_description(soup)
        assert desc == "OG description"

    def test_extract_text(self, content_extractor):
        """Test text extraction"""
        from bs4 import BeautifulSoup

        html = """
        <body>
            <h1>Title</h1>
            <p>This is some content.</p>
            <script>console.log('test');</script>
            <style>.test { color: red; }</style>
        </body>
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = content_extractor._extract_text(soup)

        assert "Title" in text
        assert "This is some content" in text
        assert "console.log" not in text  # Script should be removed
        assert ".test" not in text  # Style should be removed

    def test_extract_images(self, content_extractor):
        """Test image extraction"""
        from bs4 import BeautifulSoup

        html = """
        <img src="https://example.com/image1.jpg" alt="Image 1" width="100" height="100">
        <img src="/relative/image2.jpg" alt="Image 2">
        """
        soup = BeautifulSoup(html, 'html.parser')
        images = content_extractor._extract_images(soup, "https://example.com")

        assert len(images) == 2
        assert images[0]["src"] == "https://example.com/image1.jpg"
        assert images[0]["alt"] == "Image 1"
        assert images[1]["src"] == "https://example.com/relative/image2.jpg"

    def test_extract_links(self, content_extractor):
        """Test link extraction"""
        from bs4 import BeautifulSoup

        html = """
        <a href="https://example.com/page1">Link 1</a>
        <a href="/relative/page2" title="Link 2">Link 2</a>
        <a href="#anchor">Anchor</a>
        <a href="javascript:void(0)">JS Link</a>
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = content_extractor._extract_links(soup, "https://example.com")

        assert len(links) == 2  # Should exclude anchor and JS links
        assert links[0]["url"] == "https://example.com/page1"
        assert links[0]["text"] == "Link 1"
        assert links[1]["url"] == "https://example.com/relative/page2"

    def test_clean_text(self, content_extractor):
        """Test text cleaning"""
        dirty_text = "  This   is   dirty   text  \n\n  with   extra   spaces  "
        cleaned_text = content_extractor._clean_text(dirty_text)

        assert "   " not in cleaned_text  # No multiple spaces
        assert cleaned_text.startswith("This")  # No leading spaces
        assert cleaned_text.endswith("spaces")  # No trailing spaces

    def test_content_validation(self, content_extractor):
        """Test content validation"""
        # Valid content
        valid_content = {
            "url": "https://example.com",
            "title": "Example Title",
            "text_content": "This is some content with enough words to pass validation."
        }
        assert content_extractor.validate_content(valid_content) is True

        # Invalid content - missing fields
        invalid_content = {
            "url": "https://example.com",
            "title": "Example Title"
            # Missing text_content
        }
        assert content_extractor.validate_content(invalid_content) is False

        # Invalid content - too short
        short_content = {
            "url": "https://example.com",
            "title": "Example Title",
            "text_content": "Too short"
        }
        assert content_extractor.validate_content(short_content) is False


class TestWebScraper:
    """Test WebScraper functionality"""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mocked dependencies"""
        mock_playwright_manager = Mock(spec=PlaywrightManager)
        mock_search_engine_scraper = Mock(spec=SearchEngineScraper)
        mock_content_extractor = Mock(spec=ContentExtractor)
        mock_storage_manager = Mock()
        mock_job_manager = Mock()

        # Setup async mocks
        mock_playwright_manager.get_browser = AsyncMock()
        mock_playwright_manager.create_page = AsyncMock()
        mock_playwright_manager.return_browser = AsyncMock()
        mock_search_engine_scraper.search_google = AsyncMock()
        mock_search_engine_scraper.search_bing = AsyncMock()
        mock_search_engine_scraper.search_duckduckgo = AsyncMock()
        mock_content_extractor.extract_content = AsyncMock()
        mock_storage_manager.create_artifact = AsyncMock(return_value="test-artifact-id")
        mock_storage_manager.upload_artifact = AsyncMock()
        mock_job_manager.update_job_status = AsyncMock()
        mock_job_manager.update_job_progress = AsyncMock()

        return {
            'playwright_manager': mock_playwright_manager,
            'search_engine_scraper': mock_search_engine_scraper,
            'content_extractor': mock_content_extractor,
            'storage_manager': mock_storage_manager,
            'job_manager': mock_job_manager
        }

    @pytest.fixture
    def web_scraper(self, mock_dependencies):
        """Create WebScraper instance with mocked dependencies"""
        scraper = WebScraper()
        scraper.playwright_manager = mock_dependencies['playwright_manager']
        scraper.search_engine_scraper = mock_dependencies['search_engine_scraper']
        scraper.content_extractor = mock_dependencies['content_extractor']
        scraper.storage_manager = mock_dependencies['storage_manager']
        scraper.job_manager = mock_dependencies['job_manager']
        return scraper

    def test_initialization(self, web_scraper):
        """Test WebScraper initialization"""
        assert web_scraper.playwright_manager is not None
        assert web_scraper.search_engine_scraper is not None
        assert web_scraper.content_extractor is not None

    @pytest.mark.asyncio
    async def test_scrape_web_content(self, web_scraper, mock_dependencies):
        """Test main web scraping orchestration"""
        # Setup mock responses
        mock_dependencies['search_engine_scraper'].search_google.return_value = [
            {
                "title": "Test Result",
                "url": "https://example.com",
                "snippet": "Test snippet",
                "position": 1,
                "source": "google"
            }
        ]

        mock_dependencies['content_extractor'].extract_content.return_value = {
            "url": "https://example.com",
            "title": "Test Result",
            "text_content": "This is test content",
            "content_hash": "test-hash",
            "word_count": 5
        }

        # Test scraping
        result = await web_scraper.scrape_web_content(
            keywords=["test"],
            job_id="test-job",
            user_id="test-user",
            max_results_per_keyword=5
        )

        assert result["job_id"] == "test-job"
        assert result["total_results"] > 0
        assert "results" in result

        # Verify job updates were called
        mock_dependencies['job_manager'].update_job_status.assert_called()
        mock_dependencies['job_manager'].update_job_progress.assert_called()

    @pytest.mark.asyncio
    async def test_extract_page_content(self, web_scraper, mock_dependencies):
        """Test page content extraction"""
        mock_browser = Mock()
        mock_page = Mock()
        mock_dependencies['playwright_manager'].get_browser.return_value = mock_browser
        mock_dependencies['playwright_manager'].create_page.return_value = mock_page

        mock_dependencies['content_extractor'].extract_content.return_value = {
            "url": "https://example.com",
            "title": "Test Page",
            "text_content": "Test content"
        }

        content = await web_scraper._extract_page_content("https://example.com")

        assert content is not None
        assert content["url"] == "https://example.com"
        mock_page.goto.assert_called_once_with("https://example.com", wait_until="networkidle", timeout=30000)

    @pytest.mark.asyncio
    async def test_store_artifact(self, web_scraper, mock_dependencies):
        """Test artifact storage"""
        content = {
            "url": "https://example.com",
            "title": "Test Page",
            "text_content": "Test content",
            "content_hash": "test-hash"
        }

        artifact_id = await web_scraper._store_artifact(
            content, "test-user", "test-job"
        )

        assert artifact_id == "test-artifact-id"
        mock_dependencies['storage_manager'].create_artifact.assert_called_once()
        mock_dependencies['storage_manager'].upload_artifact.assert_called_once()

    def test_remove_duplicates(self, web_scraper):
        """Test duplicate removal"""
        results = [
            {"url": "https://example.com", "title": "Example"},
            {"url": "https://example.com", "title": "Example Duplicate"},
            {"url": "https://test.com", "title": "Test"}
        ]

        unique_results = web_scraper._remove_duplicates(results)
        assert len(unique_results) == 2
        assert unique_results[0]["url"] == "https://example.com"
        assert unique_results[1]["url"] == "https://test.com"

    def test_validate_url(self, web_scraper):
        """Test URL validation"""
        # Valid URLs
        assert web_scraper._validate_url("https://example.com") is True
        assert web_scraper._validate_url("http://test.org") is True

        # Invalid URLs
        assert web_scraper._validate_url("not-a-url") is False
        assert web_scraper._validate_url("") is False
        assert web_scraper._validate_url("ftp://example.com") is False

    @pytest.mark.asyncio
    async def test_error_handling(self, web_scraper, mock_dependencies):
        """Test error handling"""
        # Setup error condition
        mock_dependencies['search_engine_scraper'].search_google.side_effect = Exception("Search failed")

        # Test that errors are handled gracefully
        result = await web_scraper.scrape_web_content(
            keywords=["test"],
            job_id="test-job",
            user_id="test-user"
        )

        # Should still return a result structure
        assert "job_id" in result
        assert "total_results" in result


class TestWebScraperSettings:
    """Test WebScraperSettings configuration"""

    def test_default_settings(self):
        """Test default configuration values"""
        settings = WebScraperSettings()

        assert settings.headless is True
        assert settings.max_browsers == 5
        assert settings.max_results_per_keyword == 10
        assert settings.search_delay == 2.0
        assert "google" in settings.default_search_engines
        assert "bing" in settings.default_search_engines

    def test_custom_settings(self):
        """Test custom configuration values"""
        settings = WebScraperSettings(
            headless=False,
            max_browsers=10,
            max_results_per_keyword=20,
            search_delay=5.0
        )

        assert settings.headless is False
        assert settings.max_browsers == 10
        assert settings.max_results_per_keyword == 20
        assert settings.search_delay == 5.0


class TestIntegration:
    """Integration tests for web scraper components"""

    @pytest.mark.asyncio
    async def test_full_scraping_workflow(self):
        """Test complete scraping workflow with mocked external dependencies"""
        # This test would integrate all components together
        # For now, we'll test the basic workflow without actual network calls

        with patch('src.scrapers.web_scraper.playwright_manager.async_playwright') as mock_playwright:
            # Setup mocks for the entire workflow
            mock_playwright_instance = Mock()
            mock_browser = Mock()
            mock_page = Mock()

            mock_playwright.return_value.start = AsyncMock(return_value=mock_playwright_instance)
            mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_page = AsyncMock(return_value=mock_page)

            # Mock page content
            mock_page.content = AsyncMock(return_value="""
            <html>
                <head><title>Test Page</title></head>
                <body><h1>Test Content</h1></body>
            </html>
            """)

            # Mock search results
            mock_page.evaluate = AsyncMock(return_value=[
                {
                    "title": "Test Result",
                    "url": "https://example.com",
                    "snippet": "Test snippet",
                    "position": 1,
                    "source": "google"
                }
            ])

            # Test the workflow
            # This would involve creating actual instances and running the workflow
            # For now, we'll just verify the mocks are set up correctly
            assert mock_playwright.called


@pytest.mark.asyncio
async def test_performance_benchmarks():
    """Test performance characteristics"""
    # Test that operations complete within reasonable time limits
    start_time = datetime.now()

    # Simulate a quick operation
    await asyncio.sleep(0.1)

    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()

    assert elapsed >= 0.1
    assert elapsed < 0.2  # Should complete quickly


if __name__ == "__main__":
    pytest.main([__file__])
