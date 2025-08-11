"""
Government scraper configuration settings.
"""

from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings
from typing import List, Optional


class GovernmentScraperSettings(BaseSettings):
    """Configuration settings for the government scraper module."""

    # Website crawling settings
    max_pages_per_site: int = Field(default=100, description="Maximum pages to crawl per government site")
    max_crawl_depth: int = Field(default=3, description="Maximum crawl depth for government websites")
    crawl_delay: float = Field(default=2.0, description="Delay between crawl requests in seconds")
    page_timeout: int = Field(default=30000, description="Page load timeout in milliseconds")
    
    # API settings
    api_timeout: int = Field(default=30, description="API request timeout in seconds")
    api_retry_attempts: int = Field(default=3, description="Number of retry attempts for API requests")
    api_delay_seconds: float = Field(default=1.0, description="Delay between API requests")
    
    # Document processing settings
    max_document_size: int = Field(default=50 * 1024 * 1024, description="Maximum document size in bytes (50MB)")
    supported_formats: List[str] = Field(
        default=['pdf', 'docx', 'doc', 'xls', 'xlsx', 'ppt', 'pptx', 'txt'],
        description="Supported document formats"
    )
    extract_text: bool = Field(default=True, description="Extract text from documents")
    extract_metadata: bool = Field(default=True, description="Extract metadata from documents")
    
    # Government domains (Indonesian government)
    government_domains: List[str] = Field(
        default=[
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
            'bumn.go.id'
        ],
        description="List of Indonesian government domains"
    )
    
    # Government API endpoints
    government_apis: List[str] = Field(
        default=[
            'https://api.data.go.id/documents',
            'https://api.peraturan.go.id/search',
            'https://api.jdih.kemenkumham.go.id',
            'https://api.bps.go.id'
        ],
        description="List of government API endpoints"
    )
    
    # Content analysis settings
    analyze_content: bool = Field(default=True, description="Analyze document content using LLM")
    max_content_length: int = Field(default=5000, description="Maximum content length for LLM analysis")
    extract_keywords: bool = Field(default=True, description="Extract keywords from documents")
    classify_documents: bool = Field(default=True, description="Classify document types")
    generate_summaries: bool = Field(default=True, description="Generate document summaries")
    
    # LLM settings
    llm_provider: str = Field(default="openrouter", description="LLM provider to use")
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key")
    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API key")
    
    # Security and compliance settings
    respect_robots_txt: bool = Field(default=True, description="Respect robots.txt files")
    user_agent: str = Field(
        default="StratLogic-GovernmentScraper/1.0 (compliance research)",
        description="User agent string for requests"
    )
    rate_limit_requests_per_minute: int = Field(default=30, description="Rate limit requests per minute")
    enable_proxy: bool = Field(default=False, description="Enable proxy for requests")
    proxy_url: Optional[str] = Field(default=None, description="Proxy URL")
    
    # Storage settings
    government_documents_bucket: str = Field(default="government-documents", description="MinIO bucket for government documents")
    metadata_bucket: str = Field(default="government-metadata", description="MinIO bucket for metadata")
    
    # Quality and filtering settings
    min_document_quality_score: float = Field(default=0.3, description="Minimum quality score for documents")
    filter_duplicates: bool = Field(default=True, description="Filter duplicate documents")
    validate_documents: bool = Field(default=True, description="Validate document integrity")
    
    # Processing settings
    parallel_processing: bool = Field(default=True, description="Enable parallel processing")
    max_concurrent_downloads: int = Field(default=5, description="Maximum concurrent document downloads")
    max_concurrent_analysis: int = Field(default=3, description="Maximum concurrent LLM analysis")
    
    # Error handling settings
    max_retries: int = Field(default=3, description="Maximum retry attempts for failed requests")
    retry_delay: float = Field(default=5.0, description="Delay between retries in seconds")
    exponential_backoff: bool = Field(default=True, description="Use exponential backoff for retries")
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_requests: bool = Field(default=True, description="Log all requests")
    log_document_processing: bool = Field(default=True, description="Log document processing")
    
    model_config = ConfigDict(
        env_prefix="GOVERNMENT_SCRAPER_",
        case_sensitive=False
    )
