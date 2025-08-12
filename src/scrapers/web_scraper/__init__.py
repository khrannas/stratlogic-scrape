"""
Web Scraper Package

This package provides comprehensive web scraping capabilities using Playwright,
with support for multiple search engines, content extraction, and LLM integration.
"""

from .web_scraper import WebScraper, web_scraper
from .playwright_manager import PlaywrightManager
from .search_engines import SearchEngineScraper
from .content_extractor import ContentExtractor
from .config import WebScraperSettings, web_scraper_settings

__all__ = [
    'WebScraper',
    'web_scraper',
    'PlaywrightManager',
    'SearchEngineScraper',
    'ContentExtractor',
    'WebScraperSettings',
    'web_scraper_settings'
]

__version__ = "1.0.0"
