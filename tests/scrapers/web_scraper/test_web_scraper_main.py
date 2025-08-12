"""
Tests for main WebScraper orchestrator component
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.scrapers.web_scraper import WebScraper, PlaywrightManager, SearchEngineScraper, ContentExtractor


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

    @pytest.mark.asyncio
    async def test_multiple_keywords(self, web_scraper, mock_dependencies):
        """Test scraping with multiple keywords"""
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

        # Test with multiple keywords
        result = await web_scraper.scrape_web_content(
            keywords=["test", "example", "demo"],
            job_id="test-job",
            user_id="test-user",
            max_results_per_keyword=2
        )

        assert result["keywords_processed"] == 3
        assert result["total_results"] > 0

    @pytest.mark.asyncio
    async def test_multiple_search_engines(self, web_scraper, mock_dependencies):
        """Test scraping with multiple search engines"""
        # Setup different responses for different engines
        mock_dependencies['search_engine_scraper'].search_google.return_value = [
            {"title": "Google Result", "url": "https://google.com", "snippet": "Google", "position": 1, "source": "google"}
        ]
        mock_dependencies['search_engine_scraper'].search_bing.return_value = [
            {"title": "Bing Result", "url": "https://bing.com", "snippet": "Bing", "position": 1, "source": "bing"}
        ]

        mock_dependencies['content_extractor'].extract_content.return_value = {
            "url": "https://example.com",
            "title": "Test Result",
            "text_content": "This is test content",
            "content_hash": "test-hash",
            "word_count": 5
        }

        # Test with multiple search engines
        result = await web_scraper.scrape_web_content(
            keywords=["test"],
            job_id="test-job",
            user_id="test-user",
            search_engines=["duckduckgo"]
        )

        # Verify both engines were called
        mock_dependencies['search_engine_scraper'].search_google.assert_called_once()
        mock_dependencies['search_engine_scraper'].search_bing.assert_called_once()

    @pytest.mark.asyncio
    async def test_job_progress_tracking(self, web_scraper, mock_dependencies):
        """Test job progress tracking"""
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

        # Test scraping with progress tracking
        await web_scraper.scrape_web_content(
            keywords=["test", "example"],
            job_id="test-job",
            user_id="test-user"
        )

        # Verify progress updates were called
        progress_calls = mock_dependencies['job_manager'].update_job_progress.call_args_list
        assert len(progress_calls) > 0

        # Verify final progress was 100%
        final_progress_call = progress_calls[-1]
        assert final_progress_call[0][1] == 100  # Second argument should be 100

    @pytest.mark.asyncio
    async def test_content_extraction_error_handling(self, web_scraper, mock_dependencies):
        """Test error handling during content extraction"""
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

        # Setup content extraction to fail
        mock_dependencies['content_extractor'].extract_content.return_value = {}

        # Test that failed extractions are handled gracefully
        result = await web_scraper.scrape_web_content(
            keywords=["test"],
            job_id="test-job",
            user_id="test-user"
        )

        # Should still complete successfully
        assert result["job_id"] == "test-job"
        assert result["total_results"] == 0  # No successful extractions

    @pytest.mark.asyncio
    async def test_get_scraping_stats(self, web_scraper):
        """Test getting scraping statistics"""
        stats = await web_scraper.get_scraping_stats()

        assert isinstance(stats, dict)
        assert "playwright_pool_status" in stats
        assert "search_stats" in stats
        assert "llm_provider_info" in stats
        assert "timestamp" in stats

    def test_url_filtering(self, web_scraper):
        """Test URL filtering functionality"""
        urls = [
            "https://example.com",
            "http://test.org",
            "ftp://example.com",
            "not-a-url",
            "",
            "https://blocked-site.com"
        ]

        # Test URL validation
        valid_urls = [url for url in urls if web_scraper._validate_url(url)]
        assert len(valid_urls) == 2  # Only https and http URLs should be valid
        assert "https://example.com" in valid_urls
        assert "http://test.org" in valid_urls
