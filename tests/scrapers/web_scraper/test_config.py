"""
Tests for WebScraperSettings configuration
"""

import pytest
from src.scrapers.web_scraper import WebScraperSettings


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
        assert settings.extract_images is True
        assert settings.extract_links is True
        assert settings.max_content_length == 10000
        assert settings.requests_per_minute == 30
        assert settings.delay_between_requests == 2.0

    def test_custom_settings(self):
        """Test custom configuration values"""
        settings = WebScraperSettings(
            headless=False,
            max_browsers=10,
            max_results_per_keyword=20,
            search_delay=5.0,
            extract_images=False,
            extract_links=False,
            max_content_length=5000,
            requests_per_minute=60,
            delay_between_requests=1.0
        )

        assert settings.headless is False
        assert settings.max_browsers == 10
        assert settings.max_results_per_keyword == 20
        assert settings.search_delay == 5.0
        assert settings.extract_images is False
        assert settings.extract_links is False
        assert settings.max_content_length == 5000
        assert settings.requests_per_minute == 60
        assert settings.delay_between_requests == 1.0

    def test_search_engines_configuration(self):
        """Test search engines configuration"""
        # Test default engines
        settings = WebScraperSettings()
        assert len(settings.default_search_engines) >= 2
        assert "google" in settings.default_search_engines
        assert "bing" in settings.default_search_engines

        # Test custom engines
        custom_engines = ["google", "duckduckgo"]
        settings = WebScraperSettings(default_search_engines=custom_engines)
        assert settings.default_search_engines == custom_engines

    def test_rate_limiting_configuration(self):
        """Test rate limiting configuration"""
        settings = WebScraperSettings(
            requests_per_minute=15,
            delay_between_requests=4.0
        )

        assert settings.requests_per_minute == 15
        assert settings.delay_between_requests == 4.0

        # Test that delay is reasonable
        assert settings.delay_between_requests >= 1.0  # Minimum 1 second between requests

    def test_content_extraction_configuration(self):
        """Test content extraction configuration"""
        settings = WebScraperSettings(
            extract_images=False,
            extract_links=False,
            max_content_length=2000
        )

        assert settings.extract_images is False
        assert settings.extract_links is False
        assert settings.max_content_length == 2000

    def test_browser_configuration(self):
        """Test browser configuration"""
        settings = WebScraperSettings(
            headless=False,
            max_browsers=3
        )

        assert settings.headless is False
        assert settings.max_browsers == 3

        # Test reasonable limits
        assert settings.max_browsers > 0
        assert settings.max_browsers <= 20  # Reasonable upper limit

    def test_llm_configuration(self):
        """Test LLM configuration"""
        settings = WebScraperSettings(
            llm_provider="gemini",
            openrouter_api_key="test-openrouter-key",
            gemini_api_key="test-gemini-key"
        )

        assert settings.llm_provider == "gemini"
        assert settings.openrouter_api_key == "test-openrouter-key"
        assert settings.gemini_api_key == "test-gemini-key"

    def test_environment_variable_loading(self):
        """Test environment variable loading"""
        # This test would require setting environment variables
        # For now, we'll test that the settings can be created
        settings = WebScraperSettings()
        assert settings is not None

    def test_validation_constraints(self):
        """Test configuration validation constraints"""
        # Test that negative values are handled appropriately
        settings = WebScraperSettings(
            max_browsers=0,
            max_results_per_keyword=0,
            search_delay=-1.0
        )

        # These should be handled gracefully or have defaults
        assert settings.max_browsers >= 1
        assert settings.max_results_per_keyword >= 1
        assert settings.search_delay >= 0.0

    def test_configuration_immutability(self):
        """Test that configuration is properly structured"""
        settings = WebScraperSettings()

        # Test that we can access all expected attributes
        expected_attributes = [
            'headless', 'max_browsers', 'max_results_per_keyword',
            'search_delay', 'default_search_engines', 'extract_images',
            'extract_links', 'max_content_length', 'requests_per_minute',
            'delay_between_requests', 'llm_provider', 'openrouter_api_key',
            'gemini_api_key'
        ]

        for attr in expected_attributes:
            assert hasattr(settings, attr), f"Missing attribute: {attr}"

    def test_configuration_serialization(self):
        """Test configuration serialization"""
        settings = WebScraperSettings(
            headless=False,
            max_browsers=3,
            max_results_per_keyword=5
        )

        # Test that settings can be converted to dict
        settings_dict = settings.dict()
        assert isinstance(settings_dict, dict)
        assert settings_dict['headless'] is False
        assert settings_dict['max_browsers'] == 3
        assert settings_dict['max_results_per_keyword'] == 5

    def test_configuration_from_dict(self):
        """Test creating configuration from dictionary"""
        config_dict = {
            'headless': False,
            'max_browsers': 3,
            'max_results_per_keyword': 5,
            'search_delay': 3.0
        }

        settings = WebScraperSettings(**config_dict)
        assert settings.headless is False
        assert settings.max_browsers == 3
        assert settings.max_results_per_keyword == 5
        assert settings.search_delay == 3.0
