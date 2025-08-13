from pydantic_settings import BaseSettings
from typing import List, Optional

class GovernmentScraperSettings(BaseSettings):
    """Configuration settings for government document scraper"""

    # Website crawling settings
    max_pages_per_site: int = 100
    max_crawl_depth: int = 3
    crawl_delay: float = 2.0
    page_timeout: int = 30000

    # API settings
    api_timeout: int = 30
    api_retry_attempts: int = 3
    api_delay_seconds: float = 1.0

    # Document processing settings
    max_document_size: int = 50 * 1024 * 1024  # 50MB
    supported_formats: List[str] = ['pdf', 'docx', 'txt', 'doc']

    # Government domains (Indonesian government)
    government_domains: List[str] = [
        'go.id',
        'kemendagri.go.id',
        'kemendikbud.go.id',
        'kemenkeu.go.id',
        'kemenlu.go.id',
        'kemenkumham.go.id',
        'kemenperin.go.id',
        'kemenkes.go.id',
        'kemenag.go.id',
        'kemenkopmk.go.id',
        'kemenpan.go.id',
        'kemenristek.go.id',
        'kemenparekraf.go.id',
        'kemenkominfo.go.id',
        'kemenko.go.id',
        'setkab.go.id',
        'bappenas.go.id',
        'bkn.go.id',
        'bpkp.go.id',
        'bppt.go.id',
        'bi.go.id',
        'ojk.go.id',
        'bps.go.id',
        'bnpb.go.id',
        'polri.go.id',
        'tni.mil.id'
    ]

    # Government websites to crawl
    government_websites: List[str] = [
        'https://www.setkab.go.id',
        'https://www.kemendagri.go.id',
        'https://www.kemendikbud.go.id',
        'https://www.kemenkeu.go.id',
        'https://www.kemenlu.go.id',
        'https://www.kemenkumham.go.id',
        'https://www.kemenperin.go.id',
        'https://www.kemenkes.go.id',
        'https://www.kemenag.go.id',
        'https://www.kemenkopmk.go.id',
        'https://www.kemenpan.go.id',
        'https://www.kemenristek.go.id',
        'https://www.kemenparekraf.go.id',
        'https://www.kemenkominfo.go.id',
        'https://www.bappenas.go.id',
        'https://www.bps.go.id',
        'https://www.bi.go.id',
        'https://www.ojk.go.id'
    ]

    # Government API endpoints
    government_apis: List[str] = [
        'https://api.data.go.id/documents',
        'https://api.peraturan.go.id/search',
        'https://api.jdih.kemenkeu.go.id/api/v1',
        'https://api.bps.go.id/rest/bridging'
    ]

    # Document file extensions to look for
    document_extensions: List[str] = [
        '.pdf', '.doc', '.docx', '.xls', '.xlsx',
        '.ppt', '.pptx', '.txt', '.rtf'
    ]

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
    document_storage_bucket: str = "government-documents"
    metadata_storage_bucket: str = "government-metadata"

    # Processing settings
    max_concurrent_downloads: int = 5
    max_concurrent_analysis: int = 3
    document_deduplication: bool = True

    # User agent for requests
    user_agent: str = "StratLogicGovernmentScraper/1.0 (mailto:contact@stratlogic.com)"

    # Rate limiting
    requests_per_minute: int = 30
    requests_per_hour: int = 1000

    class Config:
        env_prefix = "GOVERNMENT_SCRAPER_"
        case_sensitive = False

# Global settings instance
government_scraper_settings = GovernmentScraperSettings()
