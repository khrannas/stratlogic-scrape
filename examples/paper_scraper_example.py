"""
Example script demonstrating paper scraper usage.
"""

import asyncio
import logging
from src.scrapers.paper_scraper import (
    PaperScraperSettings,
    ArxivClient,
    GrobidClient,
    CrossRefClient,
    PaperContentAnalyzer,
    PaperScraper
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main example function."""
    try:
        # Initialize configuration
        config = PaperScraperSettings(
            arxiv_max_results=5,
            arxiv_delay_seconds=1.0,
            extract_pdfs=False,  # Set to False for demo
            analyze_content=True,
            parallel_processing=False
        )
        
        logger.info("Initializing paper scraper components...")
        
        # Initialize clients (with mock LLM service for demo)
        arxiv_client = ArxivClient(config)
        grobid_client = GrobidClient(config)
        crossref_client = CrossRefClient(config)
        
        # Initialize content analyzer (without LLM service for demo)
        content_analyzer = PaperContentAnalyzer(config, None)
        
        # Initialize main scraper
        scraper = PaperScraper(
            config=config,
            arxiv_client=arxiv_client,
            grobid_client=grobid_client,
            crossref_client=crossref_client,
            content_analyzer=content_analyzer
        )
        
        logger.info("Paper scraper initialized successfully")
        
        # Example 1: Search for papers
        logger.info("Example 1: Searching for papers...")
        queries = ["machine learning", "artificial intelligence"]
        
        result = await scraper.scrape_papers(
            queries=queries,
            user_id="demo_user",
            sources=["arxiv", "crossref"],
            max_results_per_query=3,
            download_pdfs=False,
            analyze_content=True
        )
        
        logger.info(f"Found {result.total_papers_found} papers")
        logger.info(f"Processed {result.papers_processed} papers")
        logger.info(f"Analyzed {result.papers_analyzed} papers")
        logger.info(f"Processing time: {result.total_processing_time:.2f} seconds")
        
        # Display some results
        for i, paper in enumerate(result.results[:3]):
            logger.info(f"\nPaper {i+1}:")
            logger.info(f"  Title: {paper.get('title', 'N/A')}")
            logger.info(f"  Authors: {paper.get('authors', 'N/A')}")
            logger.info(f"  Source: {paper.get('source', 'N/A')}")
            if paper.get('analysis'):
                analysis = paper['analysis']
                logger.info(f"  Summary: {analysis.get('summary', 'N/A')[:100]}...")
                logger.info(f"  Quality Score: {analysis.get('quality_score', 'N/A')}")
                logger.info(f"  Topics: {analysis.get('topics', 'N/A')}")
        
        # Example 2: Get paper by ID
        logger.info("\nExample 2: Getting paper by ID...")
        if result.results:
            first_paper = result.results[0]
            if first_paper.get('arxiv_id'):
                paper = await scraper.get_paper_by_id(
                    first_paper['arxiv_id'], 
                    source='arxiv'
                )
                if paper:
                    logger.info(f"Retrieved paper: {paper.get('title', 'N/A')}")
        
        # Example 3: Search by author
        logger.info("\nExample 3: Searching by author...")
        author_papers = await scraper.search_by_author(
            "Yann LeCun",
            sources=["arxiv"],
            max_results=3
        )
        logger.info(f"Found {len(author_papers)} papers by Yann LeCun")
        
        # Example 4: Get system statistics
        logger.info("\nExample 4: Getting system statistics...")
        stats = await scraper.get_scraping_stats()
        logger.info(f"arXiv Health: {stats.get('arxiv_health', 'Unknown')}")
        logger.info(f"Grobid Health: {stats.get('grobid_health', 'Unknown')}")
        logger.info(f"CrossRef Health: {stats.get('crossref_health', 'Unknown')}")
        
        logger.info("\nPaper scraper example completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in paper scraper example: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
