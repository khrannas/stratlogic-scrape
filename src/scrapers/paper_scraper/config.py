"""
Paper scraper configuration settings.
"""

from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings
from typing import List, Optional


class PaperScraperSettings(BaseSettings):
    """Configuration settings for the paper scraper module."""

    # arXiv settings
    arxiv_max_results: int = Field(default=100, description="Maximum results from arXiv")
    arxiv_delay_seconds: float = Field(default=3.0, description="Delay between arXiv requests")
    arxiv_max_retries: int = Field(default=3, description="Maximum retries for arXiv requests")
    
    # Grobid settings
    grobid_url: str = Field(default="http://localhost:8070", description="Grobid service URL")
    grobid_timeout: int = Field(default=300, description="Grobid request timeout in seconds")
    extract_pdfs: bool = Field(default=True, description="Extract PDF content using Grobid")
    
    # CrossRef settings
    crossref_user_agent: str = Field(default="StratLogicScraper/1.0", description="User agent for CrossRef")
    crossref_max_results: int = Field(default=100, description="Maximum results from CrossRef")
    crossref_delay_seconds: float = Field(default=1.0, description="Delay between CrossRef requests")
    
    # Semantic Scholar settings
    semantic_scholar_api_key: Optional[str] = Field(default=None, description="Semantic Scholar API key")
    semantic_scholar_max_results: int = Field(default=100, description="Maximum results from Semantic Scholar")
    
    # PubMed settings
    pubmed_max_results: int = Field(default=100, description="Maximum results from PubMed")
    pubmed_delay_seconds: float = Field(default=1.0, description="Delay between PubMed requests")
    
    # Content analysis
    analyze_content: bool = Field(default=True, description="Analyze paper content using LLM")
    max_content_length: int = Field(default=5000, description="Maximum content length for LLM analysis")
    extract_citations: bool = Field(default=True, description="Extract citations from papers")
    extract_figures: bool = Field(default=True, description="Extract figures and tables")
    
    # LLM settings
    llm_provider: str = Field(default="openrouter", description="LLM provider to use")
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key")
    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API key")
    
    # Processing settings
    parallel_processing: bool = Field(default=True, description="Enable parallel processing")
    max_concurrent_downloads: int = Field(default=5, description="Maximum concurrent PDF downloads")
    max_concurrent_analysis: int = Field(default=3, description="Maximum concurrent LLM analysis")
    
    # Storage settings
    pdf_storage_bucket: str = Field(default="papers", description="MinIO bucket for PDF storage")
    metadata_storage_bucket: str = Field(default="paper-metadata", description="MinIO bucket for metadata")
    
    # Quality settings
    min_paper_quality_score: float = Field(default=0.5, description="Minimum quality score for papers")
    filter_duplicates: bool = Field(default=True, description="Filter duplicate papers")
    
    model_config = ConfigDict(
        env_prefix="PAPER_SCRAPER_",
        case_sensitive=False
    )
