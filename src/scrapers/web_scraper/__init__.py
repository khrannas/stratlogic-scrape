"""
Web scraper module for StratLogic scraping system.

This module provides comprehensive web scraping capabilities using Playwright
with search engine integration, content extraction, and LLM-powered analysis.
"""

from .playwright_manager import PlaywrightManager
from .search_engines import SearchEngineScraper
from .content_extractor import ContentExtractor
from .keyword_expander import KeywordExpander
from .web_scraper import WebScraper
from .config import WebScraperSettings

__all__ = [
    "PlaywrightManager",
    "SearchEngineScraper", 
    "ContentExtractor",
    "KeywordExpander",
    "WebScraper",
    "WebScraperSettings"
]

__version__ = "1.0.0"
