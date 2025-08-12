from pydantic_settings import BaseSettings
from typing import List, Optional

class WebScraperSettings(BaseSettings):
    """Web scraper configuration settings"""

    # Playwright settings
    headless: bool = True
    max_browsers: int = 5
    page_timeout: int = 30000
    proxy: Optional[str] = None

    # Search settings
    max_results_per_keyword: int = 10
    search_delay: float = 2.0
    default_search_engines: List[str] = ['google', 'bing']

    # Content extraction
    max_content_length: int = 10000
    extract_images: bool = True
    extract_links: bool = True
    min_content_length: int = 50

    # Rate limiting
    requests_per_minute: int = 30
    delay_between_requests: float = 2.0
    max_concurrent_requests: int = 5

    # LLM settings
    llm_provider: str = "openai"  # "openai" or "gemini"
    expand_keywords: bool = True
    analyze_content: bool = True
    max_keyword_expansions: int = 10

    # Storage settings
    store_artifacts: bool = True
    compress_content: bool = False

    # Error handling
    max_retries: int = 3
    retry_delay: float = 5.0

    # User agents for rotation
    user_agents: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0"
    ]

    # Blocked domains
    blocked_domains: List[str] = [
        'google.com', 'bing.com', 'duckduckgo.com', 'youtube.com',
        'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com'
    ]

    # Content filtering
    min_word_count: int = 50
    max_word_count: int = 50000
    allowed_mime_types: List[str] = ['text/html', 'text/plain']

    class Config:
        env_prefix = "WEB_SCRAPER_"

# Create settings instance
web_scraper_settings = WebScraperSettings()
