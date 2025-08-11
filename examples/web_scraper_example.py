"""
Example usage of the web scraper module.
"""

import asyncio
import logging
from src.scrapers.web_scraper import WebScraper, WebScraperSettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Example web scraping usage."""
    
    # Create settings
    settings = WebScraperSettings(
        headless=True,
        max_browsers=2,
        page_timeout=30000,
        max_results_per_keyword=3,
        search_delay=2.0,
        default_search_engines=['google', 'bing'],
        extract_images=False,
        extract_links=False,
        llm_provider="openrouter"
    )
    
    # Create web scraper
    async with WebScraper(settings) as scraper:
        logger.info("Web scraper initialized")
        
        # Example 1: Scrape single URL
        logger.info("Example 1: Scraping single URL")
        single_result = await scraper.scrape_single_url(
            "https://example.com",
            analyze_content=False
        )
        
        if single_result.get('error'):
            logger.error(f"Single URL scraping failed: {single_result['error']}")
        else:
            logger.info(f"Single URL scraping successful:")
            logger.info(f"  Title: {single_result.get('title', 'N/A')}")
            logger.info(f"  Word count: {single_result.get('word_count', 0)}")
            logger.info(f"  Content score: {single_result.get('content_score', 0)}")
        
        # Example 2: Get scraping statistics
        logger.info("\nExample 2: Getting scraping statistics")
        stats = await scraper.get_scraping_stats()
        logger.info(f"Browser pool status: {stats['browser_pool']}")
        logger.info(f"Settings: {stats['settings']}")
        
        # Example 3: Validate search engines
        logger.info("\nExample 3: Validating search engines")
        engine_status = await scraper.validate_search_engines()
        for engine, status in engine_status.items():
            logger.info(f"  {engine}: {'✅ Working' if status else '❌ Failed'}")


if __name__ == "__main__":
    asyncio.run(main())
