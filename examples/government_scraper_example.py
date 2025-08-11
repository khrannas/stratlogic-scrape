"""
Example usage of the government scraper module.

This script demonstrates how to use the government scraper to search for and process
Indonesian government documents.
"""

import asyncio
import logging
from datetime import datetime
from typing import List

from src.scrapers.government_scraper import (
    GovernmentScraper,
    GovernmentScraperSettings,
    GovernmentWebsiteCrawler,
    GovernmentAPIClient,
    GovernmentDocumentProcessor
)


async def main():
    """Main example function."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Government Scraper Example")
    
    # Initialize settings
    settings = GovernmentScraperSettings(
        max_pages_per_site=10,  # Limit for demo
        max_crawl_depth=2,
        crawl_delay=1.0,  # Faster for demo
        api_timeout=10,
        rate_limit_requests_per_minute=60
    )
    
    # Initialize components
    website_crawler = GovernmentWebsiteCrawler(settings)
    api_client = GovernmentAPIClient(settings)
    document_processor = GovernmentDocumentProcessor(settings)
    
    # Initialize main scraper
    scraper = GovernmentScraper(
        settings=settings,
        website_crawler=website_crawler,
        api_client=api_client,
        document_processor=document_processor
    )
    
    try:
        # Example 1: Validate system
        logger.info("Validating system...")
        validation = await scraper.validate_system()
        logger.info(f"System validation: {validation}")
        
        # Example 2: Search for documents by keyword
        logger.info("Searching for documents by keyword...")
        keywords = ["peraturan", "laporan", "anggaran"]
        
        for keyword in keywords:
            logger.info(f"Searching for: {keyword}")
            try:
                documents = await scraper.search_documents_by_keyword(keyword, limit=5)
                logger.info(f"Found {len(documents)} documents for keyword '{keyword}'")
                
                for i, doc in enumerate(documents[:3]):  # Show first 3
                    logger.info(f"  {i+1}. {doc.get('title', 'Untitled')} - {doc.get('url', 'No URL')}")
                    
            except Exception as e:
                logger.warning(f"Search failed for keyword '{keyword}': {e}")
        
        # Example 3: Get scraping statistics
        logger.info("Getting scraping statistics...")
        stats = await scraper.get_scraping_stats()
        logger.info(f"Total documents processed: {stats['total_documents_processed']}")
        logger.info(f"Total processing time: {stats['total_processing_time']:.2f} seconds")
        logger.info(f"Total errors: {stats['total_errors']}")
        
        # Example 4: Test website crawler
        logger.info("Testing website crawler...")
        try:
            # Test with a government website
            test_url = "https://www.setkab.go.id"
            documents = await website_crawler.crawl_government_site(
                test_url,
                max_pages=5,
                max_depth=1
            )
            logger.info(f"Found {len(documents)} documents from {test_url}")
            
            # Show crawl statistics
            crawl_stats = website_crawler.get_crawl_stats()
            logger.info(f"Crawl stats: {crawl_stats}")
            
        except Exception as e:
            logger.warning(f"Website crawling test failed: {e}")
        
        # Example 5: Test API client
        logger.info("Testing API client...")
        try:
            async with api_client as client:
                # Test API health
                for endpoint in settings.government_apis[:2]:  # Test first 2 endpoints
                    health = await client.get_api_health(endpoint)
                    logger.info(f"API health for {endpoint}: {health['status']}")
                
                # Get API statistics
                api_stats = await client.get_api_stats()
                logger.info(f"API stats: {api_stats}")
                
        except Exception as e:
            logger.warning(f"API client test failed: {e}")
        
        # Example 6: Test document processor
        logger.info("Testing document processor...")
        try:
            # Test with sample text
            sample_text = """
            Peraturan Pemerintah Republik Indonesia
            Nomor 123 Tahun 2023
            Tentang Pengelolaan Keuangan Negara
            
            Pemerintah Republik Indonesia mengeluarkan peraturan baru tentang 
            pengelolaan keuangan negara yang bertujuan untuk meningkatkan 
            transparansi dan akuntabilitas dalam pengelolaan anggaran.
            """
            
            # Test language detection
            language = document_processor._detect_language(sample_text)
            logger.info(f"Detected language: {language}")
            
            # Test document type classification
            doc_type = document_processor._classify_document_type_by_content(sample_text)
            logger.info(f"Document type: {doc_type}")
            
            # Test key topic extraction
            topics = document_processor._extract_key_topics(sample_text)
            logger.info(f"Key topics: {topics}")
            
            # Test sentiment analysis
            sentiment = document_processor._analyze_sentiment(sample_text)
            logger.info(f"Sentiment: {sentiment}")
            
            # Test complexity assessment
            complexity = document_processor._assess_complexity(sample_text)
            logger.info(f"Complexity: {complexity}")
            
            # Test government terms extraction
            gov_terms = document_processor._extract_government_terms(sample_text)
            logger.info(f"Government terms: {gov_terms}")
            
            # Get processing statistics
            proc_stats = document_processor.get_processing_stats()
            logger.info(f"Processing stats: {proc_stats}")
            
        except Exception as e:
            logger.warning(f"Document processor test failed: {e}")
        
        # Example 7: Full scraping job simulation
        logger.info("Simulating full scraping job...")
        try:
            # Create a mock job
            job_id = f"demo-job-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            user_id = "demo-user"
            test_keywords = ["peraturan", "laporan"]
            
            logger.info(f"Starting job {job_id} with keywords: {test_keywords}")
            
            # Note: This would require storage_manager and job_manager to be properly configured
            # For demo purposes, we'll just show the structure
            logger.info("Job simulation completed (storage and job managers not configured)")
            
        except Exception as e:
            logger.warning(f"Job simulation failed: {e}")
        
        logger.info("Government Scraper Example completed successfully!")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise
    
    finally:
        # Cleanup
        logger.info("Cleaning up...")


async def test_individual_components():
    """Test individual components separately."""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    settings = GovernmentScraperSettings(
        max_pages_per_site=5,
        max_crawl_depth=1,
        crawl_delay=0.5,
        api_timeout=5
    )
    
    # Test website crawler
    logger.info("Testing Website Crawler Component")
    crawler = GovernmentWebsiteCrawler(settings)
    
    # Test domain detection
    test_domains = [
        "https://www.setkab.go.id",
        "https://www.kemendagri.go.id",
        "https://www.google.com",
        "https://example.com"
    ]
    
    for domain in test_domains:
        is_gov = crawler._is_government_domain(domain)
        logger.info(f"Domain {domain}: {'Government' if is_gov else 'Not Government'}")
    
    # Test document URL detection
    test_urls = [
        "https://example.com/document.pdf",
        "https://example.com/file.docx",
        "https://example.com/data.xlsx",
        "https://example.com/page.html"
    ]
    
    for url in test_urls:
        is_doc = crawler._is_document_url(url)
        logger.info(f"URL {url}: {'Document' if is_doc else 'Not Document'}")
    
    # Test API client
    logger.info("Testing API Client Component")
    api_client = GovernmentAPIClient(settings)
    
    # Test API response parsing
    sample_response = {
        'results': [
            {
                'id': '1',
                'title': 'Test Document',
                'url': 'https://example.com/test.pdf',
                'description': 'Test description'
            }
        ]
    }
    
    documents = api_client._parse_api_response(sample_response, 'https://api.example.com')
    logger.info(f"Parsed {len(documents)} documents from API response")
    
    # Test document processor
    logger.info("Testing Document Processor Component")
    processor = GovernmentDocumentProcessor(settings)
    
    # Test language detection
    test_texts = [
        "Pemerintah Republik Indonesia mengeluarkan peraturan baru",
        "The government of Indonesia issued new regulations",
        "Ini adalah dokumen dalam bahasa Indonesia",
        "This is a document in English"
    ]
    
    for text in test_texts:
        language = processor._detect_language(text)
        logger.info(f"Text: '{text[:30]}...' -> Language: {language}")


if __name__ == "__main__":
    # Run the main example
    asyncio.run(main())
    
    # Run individual component tests
    print("\n" + "="*50)
    print("Testing Individual Components")
    print("="*50)
    asyncio.run(test_individual_components())
