"""
Web scraper configuration settings.
"""

from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings
from typing import List, Optional


class WebScraperSettings(BaseSettings):
    """Configuration settings for the web scraper module."""
    
    # Playwright settings
    headless: bool = Field(default=True, description="Run browser in headless mode")
    max_browsers: int = Field(default=5, description="Maximum number of browsers in pool")
    page_timeout: int = Field(default=30000, description="Page load timeout in milliseconds")
    
    # Search settings
    max_results_per_keyword: int = Field(default=10, description="Maximum results per keyword")
    search_delay: float = Field(default=2.0, description="Delay between search requests")
    default_search_engines: List[str] = Field(
        default=['google', 'bing'], 
        description="Default search engines to use"
    )
    
    # Content extraction
    max_content_length: int = Field(default=10000, description="Maximum content length to extract")
    extract_images: bool = Field(default=True, description="Extract images from pages")
    extract_links: bool = Field(default=True, description="Extract links from pages")
    
    # Rate limiting
    requests_per_minute: int = Field(default=30, description="Maximum requests per minute")
    delay_between_requests: float = Field(default=2.0, description="Delay between requests")
    
    # LLM settings
    llm_provider: str = Field(default="openrouter", description="LLM provider to use")
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key")
    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API key")
    
    # Proxy settings
    use_proxy: bool = Field(default=False, description="Use proxy for requests")
    proxy_url: Optional[str] = Field(default=None, description="Proxy URL")
    
    # User agent settings
    rotate_user_agents: bool = Field(default=True, description="Rotate user agents")
    custom_user_agent: Optional[str] = Field(default=None, description="Custom user agent")
    
    model_config = ConfigDict(
        env_prefix="WEB_SCRAPER_",
        case_sensitive=False
    )
