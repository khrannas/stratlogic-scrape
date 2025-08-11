"""
Government scraper module for StratLogic scraping system.

This module provides comprehensive Indonesian government document scraping capabilities using
website crawling, API integration, document processing, and LLM-powered analysis.
"""

from .website_crawler import GovernmentWebsiteCrawler, DocumentInfo
from .api_client import GovernmentAPIClient, APIDocument
from .document_processor import GovernmentDocumentProcessor, ProcessedDocument
from .government_scraper import GovernmentScraper, ScrapingJob, ScrapingResult
from .config import GovernmentScraperSettings

__all__ = [
    "GovernmentWebsiteCrawler",
    "DocumentInfo",
    "GovernmentAPIClient",
    "APIDocument",
    "GovernmentDocumentProcessor",
    "ProcessedDocument",
    "GovernmentScraper",
    "ScrapingJob",
    "ScrapingResult",
    "GovernmentScraperSettings"
]

__version__ = "1.0.0"
__author__ = "StratLogic Team"
