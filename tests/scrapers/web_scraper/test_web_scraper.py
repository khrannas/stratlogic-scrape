"""
Tests for web scraper components.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from src.scrapers.web_scraper.config import WebScraperSettings
from src.scrapers.web_scraper.playwright_manager import PlaywrightManager
from src.scrapers.web_scraper.content_extractor import ContentExtractor
from src.scrapers.web_scraper.keyword_expander import KeywordExpander


@pytest.fixture
def settings():
    """Create test settings."""
    return WebScraperSettings(
        headless=True,
        max_browsers=2,
        page_timeout=10000,
        max_results_per_keyword=5,
        search_delay=1.0,
        default_search_engines=['google', 'bing'],
        extract_images=False,
        extract_links=False,
        llm_provider="openrouter"
    )


@pytest.fixture
def mock_playwright_manager(settings):
    """Create a mock playwright manager."""
    manager = Mock(spec=PlaywrightManager)
    manager.settings = settings
    manager.get_browser = AsyncMock()
    manager.return_browser = AsyncMock()
    manager.create_page = AsyncMock()
    return manager


class TestWebScraperSettings:
    """Test web scraper configuration."""
    
    def test_default_settings(self):
        """Test default settings values."""
        settings = WebScraperSettings()
        
        assert settings.headless is True
        assert settings.max_browsers == 5
        assert settings.page_timeout == 30000
        assert settings.max_results_per_keyword == 10
        assert settings.search_delay == 2.0
        assert settings.default_search_engines == ['google', 'bing']
        assert settings.extract_images is True
        assert settings.extract_links is True
        assert settings.llm_provider == "openrouter"
    
    def test_custom_settings(self):
        """Test custom settings values."""
        settings = WebScraperSettings(
            headless=False,
            max_browsers=10,
            page_timeout=60000,
            max_results_per_keyword=20,
            search_delay=5.0,
            default_search_engines=['google'],
            extract_images=False,
            extract_links=False,
            llm_provider="gemini"
        )
        
        assert settings.headless is False
        assert settings.max_browsers == 10
        assert settings.page_timeout == 60000
        assert settings.max_results_per_keyword == 20
        assert settings.search_delay == 5.0
        assert settings.default_search_engines == ['google']
        assert settings.extract_images is False
        assert settings.extract_links is False
        assert settings.llm_provider == "gemini"


class TestContentExtractor:
    """Test content extractor functionality."""
    
    def test_content_extractor_initialization(self, settings):
        """Test content extractor initialization."""
        extractor = ContentExtractor(settings)
        assert extractor.settings == settings
        assert extractor.logger is not None
    
    def test_clean_text(self, settings):
        """Test text cleaning functionality."""
        extractor = ContentExtractor(settings)
        
        # Test basic text cleaning
        dirty_text = "  This   is   a   test   text  with   extra   spaces  "
        clean_text = extractor._clean_text(dirty_text)
        assert clean_text == "This is a test text with extra spaces"
        
        # Test with special characters
        special_text = "This is a test with @#$%^&*() special chars"
        clean_text = extractor._clean_text(special_text)
        assert "special chars" in clean_text
        assert "@#$%^&*()" not in clean_text
    
    def test_calculate_content_score(self, settings):
        """Test content score calculation."""
        extractor = ContentExtractor(settings)
        
        # Test with minimal content
        minimal_content = {
            'text_content': 'Short text',
            'title': 'Short title',
            'word_count': 2
        }
        score = extractor.calculate_content_score(minimal_content)
        assert score > 0
        assert score <= 100
        
        # Test with rich content
        rich_content = {
            'text_content': 'This is a much longer text with many words and content',
            'title': 'A comprehensive title for testing',
            'description': 'A detailed description that provides context about the content',
            'word_count': 15,
            'metadata': {
                'author': 'Test Author',
                'published_date': '2024-01-01',
                'keywords': ['test', 'content']
            },
            'images': [{'src': 'test.jpg'}],
            'links': [{'url': 'http://test.com'}]
        }
        score = extractor.calculate_content_score(rich_content)
        assert score > 50
        assert score <= 100


class TestKeywordExpander:
    """Test keyword expander functionality."""
    
    def test_keyword_expander_initialization(self, settings):
        """Test keyword expander initialization."""
        expander = KeywordExpander(settings)
        assert expander.settings == settings
        assert expander.logger is not None
        assert expander.llm_service is not None
    
    @pytest.mark.asyncio
    async def test_expand_keywords_fallback(self, settings):
        """Test keyword expansion fallback when LLM fails."""
        expander = KeywordExpander(settings)
        
        # Test with original keywords when expansion fails
        original_keywords = ['test', 'keyword']
        expanded = await expander.expand_keywords(original_keywords)
        
        # Should return original keywords if LLM fails
        assert len(expanded) >= len(original_keywords)
        assert all(keyword in expanded for keyword in original_keywords)
    
    @pytest.mark.asyncio
    async def test_analyze_content_fallback(self, settings):
        """Test content analysis fallback when LLM fails."""
        expander = KeywordExpander(settings)
        
        # Test content analysis fallback
        content = "This is a test content for analysis"
        analysis = await expander.analyze_content(content)
        
        # Should return fallback analysis
        assert 'topics' in analysis
        assert 'content_type' in analysis
        assert 'language' in analysis
        assert 'quality_score' in analysis
        assert 'entities' in analysis
        assert 'summary' in analysis
    
    @pytest.mark.asyncio
    async def test_classify_content_fallback(self, settings):
        """Test content classification fallback when LLM fails."""
        expander = KeywordExpander(settings)
        
        # Test content classification fallback
        classification = await expander.classify_content(
            title="Test Title",
            description="Test Description",
            text_content="Test content"
        )
        
        # Should return fallback classification
        assert 'category' in classification
        assert 'subcategory' in classification
        assert 'topics' in classification
        assert 'sentiment' in classification
        assert 'relevance_score' in classification
        assert 'content_quality' in classification


class TestPlaywrightManager:
    """Test playwright manager functionality."""
    
    def test_playwright_manager_initialization(self, settings):
        """Test playwright manager initialization."""
        manager = PlaywrightManager(settings)
        assert manager.settings == settings
        assert manager.logger is not None
        assert len(manager.browser_pool) == 0
        assert manager.playwright is None
    
    def test_get_pool_status(self, settings):
        """Test pool status reporting."""
        manager = PlaywrightManager(settings)
        status = manager.get_pool_status()
        
        assert 'pool_size' in status
        assert 'max_browsers' in status
        assert 'headless' in status
        assert 'timeout' in status
        assert status['pool_size'] == 0
        assert status['max_browsers'] == settings.max_browsers
        assert status['headless'] == settings.headless
        assert status['timeout'] == settings.page_timeout


if __name__ == "__main__":
    pytest.main([__file__])
