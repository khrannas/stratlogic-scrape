from pydantic_settings import BaseSettings
from typing import List, Optional

class PaperScraperSettings(BaseSettings):
    """Configuration settings for paper scraper"""

    # arXiv settings
    arxiv_max_results: int = 100
    arxiv_delay_seconds: float = 3.0
    arxiv_max_retries: int = 3

    # Grobid settings
    grobid_url: str = "http://localhost:8070"
    grobid_timeout: int = 300
    grobid_max_retries: int = 3

    # CrossRef settings
    crossref_user_agent: str = "StratLogicScraper/1.0 (mailto:contact@stratlogic.com)"
    crossref_max_results: int = 100
    crossref_delay_seconds: float = 1.0

    # Semantic Scholar settings
    semantic_scholar_api_key: Optional[str] = None
    semantic_scholar_max_results: int = 100
    semantic_scholar_delay_seconds: float = 1.0

    # PubMed settings
    pubmed_max_results: int = 100
    pubmed_delay_seconds: float = 1.0

    # Content processing settings
    extract_pdfs: bool = True
    analyze_content: bool = True
    extract_citations: bool = True
    extract_figures: bool = True

    # LLM settings for content analysis
    llm_provider: str = "openrouter"  # "openrouter", "openai", or "gemini"
    openrouter_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    # Content analysis settings
    max_summary_length: int = 500
    keyword_extraction_count: int = 10
    content_quality_threshold: float = 0.7

    # Storage settings
    pdf_storage_bucket: str = "papers"
    metadata_storage_bucket: str = "paper-metadata"

    # Processing settings
    max_concurrent_downloads: int = 5
    max_concurrent_analysis: int = 3
    paper_deduplication: bool = True

    class Config:
        env_prefix = "PAPER_SCRAPER_"
        case_sensitive = False

# Global settings instance
paper_scraper_settings = PaperScraperSettings()
