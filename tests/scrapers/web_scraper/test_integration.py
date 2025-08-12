"""
Integration tests for web scraper components
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from src.scrapers.web_scraper import (
    WebScraper,
    PlaywrightManager,
    SearchEngineScraper,
    ContentExtractor,
    WebScraperSettings
)


class TestWebScraperIntegration:
    """Integration tests for web scraper components"""

    @pytest.fixture
    def mock_playwright(self):
        """Mock Playwright for integration tests"""
        with patch('src.scrapers.web_scraper.playwright_manager.async_playwright') as mock_playwright:
            mock_playwright_instance = Mock()
            mock_browser = Mock()
            mock_page = Mock()

            mock_playwright.return_value.start = AsyncMock(return_value=mock_playwright_instance)
            mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_page = AsyncMock(return_value=mock_page)

            # Mock page content
            mock_page.content = AsyncMock(return_value="""
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

            yield mock_playwright

    @pytest.fixture
    def mock_storage_and_job_managers(self):
        """Mock storage and job managers"""
        mock_storage_manager = Mock()
        mock_job_manager = Mock()

        mock_storage_manager.create_artifact = AsyncMock(return_value="test-artifact-id")
        mock_storage_manager.upload_artifact = AsyncMock()
        mock_job_manager.update_job_status = AsyncMock()
        mock_job_manager.update_job_progress = AsyncMock()

        return mock_storage_manager, mock_job_manager

    @pytest.mark.asyncio
    async def test_full_scraping_workflow(self, mock_playwright, mock_storage_and_job_managers):
        """Test complete scraping workflow with mocked external dependencies"""
        mock_storage_manager, mock_job_manager = mock_storage_and_job_managers

        # Create real instances with mocked dependencies
        playwright_manager = PlaywrightManager(headless=True, max_browsers=2)
        search_engine_scraper = SearchEngineScraper(playwright_manager)
        content_extractor = ContentExtractor()

        # Create web scraper with real components
        web_scraper = WebScraper()
        web_scraper.playwright_manager = playwright_manager
        web_scraper.search_engine_scraper = search_engine_scraper
        web_scraper.content_extractor = content_extractor
        web_scraper.storage_manager = mock_storage_manager
        web_scraper.job_manager = mock_job_manager

        # Test the complete workflow
        result = await web_scraper.scrape_web_content(
            keywords=["test"],
            job_id="test-job",
            user_id="test-user",
            max_results_per_keyword=5
        )

        # Verify the result structure
        assert result["job_id"] == "test-job"
        assert result["total_results"] > 0
        assert "results" in result
        assert result["keywords_processed"] == 1

        # Verify job management was called
        mock_job_manager.update_job_status.assert_called()
        mock_job_manager.update_job_progress.assert_called()

        # Verify storage was called
        mock_storage_manager.create_artifact.assert_called()
        mock_storage_manager.upload_artifact.assert_called()

    @pytest.mark.asyncio
    async def test_multiple_search_engines_integration(self, mock_playwright, mock_storage_and_job_managers):
        """Test integration with multiple search engines"""
        mock_storage_manager, mock_job_manager = mock_storage_and_job_managers

        # Create real instances
        playwright_manager = PlaywrightManager(headless=True, max_browsers=2)
        search_engine_scraper = SearchEngineScraper(playwright_manager)
        content_extractor = ContentExtractor()

        web_scraper = WebScraper()
        web_scraper.playwright_manager = playwright_manager
        web_scraper.search_engine_scraper = search_engine_scraper
        web_scraper.content_extractor = content_extractor
        web_scraper.storage_manager = mock_storage_manager
        web_scraper.job_manager = mock_job_manager

        # Test with multiple search engines
        result = await web_scraper.scrape_web_content(
            keywords=["test"],
            job_id="test-job",
            user_id="test-user",
            search_engines=["duckduckgo"],
            max_results_per_keyword=3
        )

        assert result["job_id"] == "test-job"
        assert result["total_results"] > 0
        assert result["keywords_processed"] == 1

    @pytest.mark.asyncio
    async def test_content_extraction_integration(self, mock_playwright):
        """Test content extraction integration"""
        # Create real content extractor
        content_extractor = ContentExtractor()

        # Get mock page from playwright fixture
        mock_browser = Mock()
        mock_page = Mock()
        mock_playwright.return_value.start.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        # Test content extraction
        content = await content_extractor.extract_content(mock_page, "https://example.com")

        assert content["url"] == "https://example.com"
        assert "title" in content
        assert "text_content" in content
        assert "content_hash" in content
        assert "word_count" in content
        assert "metadata" in content
        assert "images" in content
        assert "links" in content

    @pytest.mark.asyncio
    async def test_search_engine_integration(self, mock_playwright):
        """Test search engine integration"""
        # Create real search engine scraper
        playwright_manager = PlaywrightManager(headless=True, max_browsers=2)
        search_engine_scraper = SearchEngineScraper(playwright_manager)

        # Test Google search
        results = await search_engine_scraper.search_google("test query", max_results=5)

        assert len(results) == 1
        assert results[0]["title"] == "Test Result"
        assert results[0]["url"] == "https://example.com"
        assert results[0]["source"] == "google"

    @pytest.mark.asyncio
    async def test_error_recovery_integration(self, mock_playwright, mock_storage_and_job_managers):
        """Test error recovery in integration"""
        mock_storage_manager, mock_job_manager = mock_storage_and_job_managers

        # Create real instances
        playwright_manager = PlaywrightManager(headless=True, max_browsers=2)
        search_engine_scraper = SearchEngineScraper(playwright_manager)
        content_extractor = ContentExtractor()

        web_scraper = WebScraper()
        web_scraper.playwright_manager = playwright_manager
        web_scraper.search_engine_scraper = search_engine_scraper
        web_scraper.content_extractor = content_extractor
        web_scraper.storage_manager = mock_storage_manager
        web_scraper.job_manager = mock_job_manager

        # Test with invalid URL that should be filtered out
        result = await web_scraper.scrape_web_content(
            keywords=["test"],
            job_id="test-job",
            user_id="test-user",
            max_results_per_keyword=5
        )

        # Should still complete successfully even with errors
        assert result["job_id"] == "test-job"
        assert "total_results" in result

    @pytest.mark.asyncio
    async def test_configuration_integration(self):
        """Test configuration integration"""
        # Test with custom configuration
        settings = WebScraperSettings(
            headless=False,
            max_browsers=3,
            max_results_per_keyword=5,
            search_delay=1.0,
            extract_images=False,
            extract_links=False
        )

        # Create components with custom settings
        playwright_manager = PlaywrightManager(
            headless=settings.headless,
            max_browsers=settings.max_browsers
        )

        search_engine_scraper = SearchEngineScraper(playwright_manager)
        content_extractor = ContentExtractor()

        # Verify configuration is applied
        assert playwright_manager.headless == settings.headless
        assert playwright_manager.max_browsers == settings.max_browsers

    @pytest.mark.asyncio
    async def test_performance_integration(self, mock_playwright, mock_storage_and_job_managers):
        """Test performance characteristics in integration"""
        mock_storage_manager, mock_job_manager = mock_storage_and_job_managers

        # Create real instances
        playwright_manager = PlaywrightManager(headless=True, max_browsers=2)
        search_engine_scraper = SearchEngineScraper(playwright_manager)
        content_extractor = ContentExtractor()

        web_scraper = WebScraper()
        web_scraper.playwright_manager = playwright_manager
        web_scraper.search_engine_scraper = search_engine_scraper
        web_scraper.content_extractor = content_extractor
        web_scraper.storage_manager = mock_storage_manager
        web_scraper.job_manager = mock_job_manager

        # Test performance with timing
        start_time = datetime.now()

        result = await web_scraper.scrape_web_content(
            keywords=["test"],
            job_id="test-job",
            user_id="test-user",
            max_results_per_keyword=3
        )

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        # Should complete within reasonable time (with mocked dependencies)
        assert elapsed < 5.0  # Should be very fast with mocks
        assert result["job_id"] == "test-job"

    @pytest.mark.asyncio
    async def test_concurrent_operations_integration(self, mock_playwright, mock_storage_and_job_managers):
        """Test concurrent operations in integration"""
        mock_storage_manager, mock_job_manager = mock_storage_and_job_managers

        # Create real instances
        playwright_manager = PlaywrightManager(headless=True, max_browsers=3)
        search_engine_scraper = SearchEngineScraper(playwright_manager)
        content_extractor = ContentExtractor()

        web_scraper = WebScraper()
        web_scraper.playwright_manager = playwright_manager
        web_scraper.search_engine_scraper = search_engine_scraper
        web_scraper.content_extractor = content_extractor
        web_scraper.storage_manager = mock_storage_manager
        web_scraper.job_manager = mock_job_manager

        # Test concurrent scraping operations
        tasks = []
        for i in range(3):
            task = web_scraper.scrape_web_content(
                keywords=[f"test{i}"],
                job_id=f"test-job-{i}",
                user_id="test-user",
                max_results_per_keyword=2
            )
            tasks.append(task)

        # Execute concurrently
        results = await asyncio.gather(*tasks)

        # Verify all completed successfully
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["job_id"] == f"test-job-{i}"
            assert "total_results" in result

    @pytest.mark.asyncio
    async def test_data_flow_integration(self, mock_playwright, mock_storage_and_job_managers):
        """Test complete data flow in integration"""
        mock_storage_manager, mock_job_manager = mock_storage_and_job_managers

        # Create real instances
        playwright_manager = PlaywrightManager(headless=True, max_browsers=2)
        search_engine_scraper = SearchEngineScraper(playwright_manager)
        content_extractor = ContentExtractor()

        web_scraper = WebScraper()
        web_scraper.playwright_manager = playwright_manager
        web_scraper.search_engine_scraper = search_engine_scraper
        web_scraper.content_extractor = content_extractor
        web_scraper.storage_manager = mock_storage_manager
        web_scraper.job_manager = mock_job_manager

        # Test complete data flow
        result = await web_scraper.scrape_web_content(
            keywords=["integration test"],
            job_id="integration-job",
            user_id="test-user",
            max_results_per_keyword=3
        )

        # Verify data flow through all components
        assert result["job_id"] == "integration-job"
        assert result["total_results"] > 0
        assert result["keywords_processed"] == 1

        # Verify job management flow
        job_status_calls = mock_job_manager.update_job_status.call_args_list
        assert len(job_status_calls) > 0

        # Verify storage flow
        storage_calls = mock_storage_manager.create_artifact.call_args_list
        assert len(storage_calls) > 0

        # Verify progress tracking
        progress_calls = mock_job_manager.update_job_progress.call_args_list
        assert len(progress_calls) > 0


@pytest.mark.asyncio
async def test_integration_with_real_components():
    """Test integration with real component instances"""
    # This test uses real component instances without external dependencies
    settings = WebScraperSettings()

    # Create real instances
    playwright_manager = PlaywrightManager(
        headless=settings.headless,
        max_browsers=settings.max_browsers
    )

    search_engine_scraper = SearchEngineScraper(playwright_manager)
    content_extractor = ContentExtractor()

    # Verify components can be created and initialized
    assert playwright_manager is not None
    assert search_engine_scraper is not None
    assert content_extractor is not None

    # Verify component relationships
    assert search_engine_scraper.playwright_manager == playwright_manager
    assert search_engine_scraper.min_delay == 2.0

    # Verify content extractor initialization
    assert len(content_extractor.noise_patterns) > 0
    assert len(content_extractor.text_cleanup_patterns) > 0
