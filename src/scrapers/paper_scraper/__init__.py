"""
Paper scraper module for StratLogic scraping system.

This module provides comprehensive academic paper scraping capabilities using
arXiv API, Grobid PDF processing, CrossRef integration, and LLM-powered analysis.
"""

from .arxiv_client import ArxivClient
from .grobid_client import GrobidClient
from .crossref_client import CrossRefClient
from .content_analyzer import PaperContentAnalyzer, AnalysisResult
from .paper_scraper import PaperScraper, ScrapingJob, ScrapingResult
from .config import PaperScraperSettings

__all__ = [
    "ArxivClient",
    "GrobidClient", 
    "CrossRefClient",
    "PaperContentAnalyzer",
    "AnalysisResult",
    "PaperScraper",
    "ScrapingJob",
    "ScrapingResult",
    "PaperScraperSettings"
]

__version__ = "1.0.0"
__author__ = "StratLogic Team"
