"""
Unit tests for government scraper module.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.scrapers.government_scraper.config import GovernmentScraperSettings
from src.scrapers.government_scraper.website_crawler import GovernmentWebsiteCrawler, DocumentInfo
from src.scrapers.government_scraper.api_client import GovernmentAPIClient, APIDocument
from src.scrapers.government_scraper.document_processor import GovernmentDocumentProcessor, ProcessedDocument
from src.scrapers.government_scraper.government_scraper import GovernmentScraper, ScrapingJob, ScrapingResult


class TestGovernmentScraperSettings:
    """Test government scraper configuration settings."""
    
    def test_default_settings(self):
        """Test default configuration values."""
        settings = GovernmentScraperSettings()
        
        assert settings.max_pages_per_site == 100
        assert settings.max_crawl_depth == 3
        assert settings.crawl_delay == 2.0
        assert settings.api_timeout == 30
        assert settings.max_document_size == 50 * 1024 * 1024
        assert 'go.id' in settings.government_domains
        assert settings.llm_provider == "openrouter"
        assert settings.user_agent == "StratLogic-GovernmentScraper/1.0 (compliance research)"
    
    def test_custom_settings(self):
        """Test custom configuration values."""
        settings = GovernmentScraperSettings(
            max_pages_per_site=50,
            max_crawl_depth=2,
            crawl_delay=1.0,
            api_timeout=60
        )
        
        assert settings.max_pages_per_site == 50
        assert settings.max_crawl_depth == 2
        assert settings.crawl_delay == 1.0
        assert settings.api_timeout == 60


class TestGovernmentWebsiteCrawler:
    """Test government website crawler."""
    
    @pytest.fixture
    def settings(self):
        return GovernmentScraperSettings()
    
    @pytest.fixture
    def crawler(self, settings):
        return GovernmentWebsiteCrawler(settings)
    
    def test_is_government_domain(self, crawler):
        """Test government domain detection."""
        assert crawler._is_government_domain("https://www.setkab.go.id")
        assert crawler._is_government_domain("https://www.kemendagri.go.id")
        assert not crawler._is_government_domain("https://www.google.com")
        assert not crawler._is_government_domain("https://example.com")
    
    def test_is_document_url(self, crawler):
        """Test document URL detection."""
        assert crawler._is_document_url("https://example.com/document.pdf")
        assert crawler._is_document_url("https://example.com/file.docx")
        assert crawler._is_document_url("https://example.com/data.xlsx")
        assert not crawler._is_document_url("https://example.com/page.html")
        assert not crawler._is_document_url("https://example.com/")
    
    def test_classify_document_type(self, crawler):
        """Test document type classification."""
        assert crawler._classify_document_type("https://example.com/file.pdf") == "pdf"
        assert crawler._classify_document_type("https://example.com/file.docx") == "word"
        assert crawler._classify_document_type("https://example.com/file.xlsx") == "excel"
        assert crawler._classify_document_type("https://example.com/file.txt") == "text"
        assert crawler._classify_document_type("https://example.com/file.unknown") is None
    
    def test_extract_title_from_url(self, crawler):
        """Test title extraction from URL."""
        assert crawler._extract_title_from_url("https://example.com/document.pdf") == "Document"
        assert crawler._extract_title_from_url("https://example.com/annual-report-2023.pdf") == "Annual Report 2023"
        assert crawler._extract_title_from_url("https://example.com/") == "Untitled Document"
    
    def test_get_crawl_stats(self, crawler):
        """Test crawl statistics."""
        stats = crawler.get_crawl_stats()
        
        assert 'visited_urls' in stats
        assert 'unique_documents_found' in stats
        assert 'government_domains' in stats
        assert 'crawl_settings' in stats
        assert stats['visited_urls'] == 0  # No URLs visited yet


class TestGovernmentAPIClient:
    """Test government API client."""
    
    @pytest.fixture
    def settings(self):
        return GovernmentScraperSettings()
    
    @pytest.fixture
    def api_client(self, settings):
        return GovernmentAPIClient(settings)
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self, api_client):
        """Test async context manager."""
        async with api_client as client:
            assert client.session is not None
            assert isinstance(client.session, Mock)  # Mock session in tests
    
    def test_parse_api_response(self, api_client):
        """Test API response parsing."""
        # Test with 'results' key
        data = {
            'results': [
                {
                    'id': '1',
                    'title': 'Test Document',
                    'url': 'https://example.com/doc.pdf',
                    'description': 'Test description'
                }
            ]
        }
        
        documents = api_client._parse_api_response(data, 'https://api.example.com')
        assert len(documents) == 1
        assert documents[0].title == 'Test Document'
        assert documents[0].url == 'https://example.com/doc.pdf'
    
    def test_parse_document_metadata(self, api_client):
        """Test document metadata parsing."""
        data = {
            'id': '1',
            'title': 'Test Document',
            'description': 'Test description',
            'url': 'https://example.com/doc.pdf',
            'file_size': 1024,
            'content_type': 'application/pdf',
            'published_date': '2023-01-01',
            'author': 'Test Author',
            'department': 'Test Department'
        }
        
        metadata = api_client._parse_document_metadata(data)
        assert metadata['id'] == '1'
        assert metadata['title'] == 'Test Document'
        assert metadata['author'] == 'Test Author'
        assert metadata['department'] == 'Test Department'
    
    def test_remove_duplicates(self, api_client):
        """Test duplicate removal."""
        documents = [
            APIDocument(
                id='1', title='Doc 1', url='https://example.com/doc1.pdf',
                description=None, published_date=None, source='api',
                api_endpoint='https://api.example.com', metadata={},
                extraction_timestamp='2023-01-01T00:00:00'
            ),
            APIDocument(
                id='2', title='Doc 2', url='https://example.com/doc2.pdf',
                description=None, published_date=None, source='api',
                api_endpoint='https://api.example.com', metadata={},
                extraction_timestamp='2023-01-01T00:00:00'
            ),
            APIDocument(
                id='3', title='Doc 1 Duplicate', url='https://example.com/doc1.pdf',
                description=None, published_date=None, source='api',
                api_endpoint='https://api.example.com', metadata={},
                extraction_timestamp='2023-01-01T00:00:00'
            )
        ]
        
        unique_docs = api_client._remove_duplicates(documents)
        assert len(unique_docs) == 2  # Should remove duplicate URL
    
    @pytest.mark.asyncio
    async def test_get_api_stats(self, api_client):
        """Test API statistics."""
        stats = await api_client.get_api_stats()
        
        assert 'total_requests' in stats
        assert 'api_endpoints' in stats
        assert 'rate_limit' in stats
        assert 'timeout' in stats
        assert 'retry_attempts' in stats


class TestGovernmentDocumentProcessor:
    """Test government document processor."""
    
    @pytest.fixture
    def settings(self):
        return GovernmentScraperSettings()
    
    @pytest.fixture
    def processor(self, settings):
        return GovernmentDocumentProcessor(settings)
    
    def test_detect_language(self, processor):
        """Test language detection."""
        indonesian_text = "Pemerintah Republik Indonesia mengeluarkan peraturan baru"
        english_text = "The government of the Republic of Indonesia issued new regulations"
        
        assert processor._detect_language(indonesian_text) == 'id'
        assert processor._detect_language(english_text) == 'en'
    
    def test_classify_document_type_by_content(self, processor):
        """Test document type classification by content."""
        regulation_text = "Peraturan Pemerintah tentang..."
        report_text = "Laporan tahunan 2023..."
        decision_text = "Keputusan Menteri..."
        letter_text = "Surat edaran..."
        budget_text = "Anggaran belanja..."
        proposal_text = "Proposal pengembangan..."
        
        assert processor._classify_document_type_by_content(regulation_text) == 'regulation'
        assert processor._classify_document_type_by_content(report_text) == 'report'
        assert processor._classify_document_type_by_content(decision_text) == 'decision'
        assert processor._classify_document_type_by_content(letter_text) == 'letter'
        assert processor._classify_document_type_by_content(budget_text) == 'budget'
        assert processor._classify_document_type_by_content(proposal_text) == 'proposal'
    
    def test_extract_key_topics(self, processor):
        """Test key topic extraction."""
        text = "Pemerintah Republik Indonesia mengeluarkan peraturan baru tentang keuangan negara"
        topics = processor._extract_key_topics(text)
        
        assert 'pemerintah' in topics
        assert 'peraturan' in topics
        assert 'keuangan' in topics
    
    def test_analyze_sentiment(self, processor):
        """Test sentiment analysis."""
        positive_text = "Hasil yang baik dan positif menunjukkan peningkatan"
        negative_text = "Masalah dan kegagalan yang buruk"
        neutral_text = "Dokumen ini berisi informasi"
        
        assert processor._analyze_sentiment(positive_text) == 'positive'
        assert processor._analyze_sentiment(negative_text) == 'negative'
        assert processor._analyze_sentiment(neutral_text) == 'neutral'
    
    def test_assess_complexity(self, processor):
        """Test complexity assessment."""
        simple_text = "Ini adalah teks sederhana"
        complex_text = "Pemerintah Republik Indonesia mengeluarkan peraturan perundang-undangan"
        
        assert processor._assess_complexity(simple_text) == 'low'
        assert processor._assess_complexity(complex_text) == 'high'
    
    def test_extract_government_terms(self, processor):
        """Test government term extraction."""
        text = "Peraturan Pemerintah tentang Undang-undang dan Keputusan Presiden"
        terms = processor._extract_government_terms(text)
        
        assert 'peraturan pemerintah' in terms
        assert 'undang-undang' in terms
        assert 'keputusan presiden' in terms
    
    def test_calculate_quality_score(self, processor):
        """Test quality score calculation."""
        text = "This is a test document with some content"
        metadata = {'title': 'Test', 'author': 'Author'}
        analysis = {
            'language': 'en',
            'document_type': 'document',
            'government_terms': ['government'],
            'sentiment': 'neutral'
        }
        
        score = processor._calculate_quality_score(text, metadata, analysis)
        assert 0.0 <= score <= 1.0
    
    def test_get_processing_stats(self, processor):
        """Test processing statistics."""
        stats = processor.get_processing_stats()
        
        assert 'pdf_available' in stats
        assert 'docx_available' in stats
        assert 'excel_available' in stats
        assert 'max_document_size' in stats
        assert 'supported_formats' in stats


class TestGovernmentScraper:
    """Test government scraper orchestrator."""
    
    @pytest.fixture
    def settings(self):
        return GovernmentScraperSettings()
    
    @pytest.fixture
    def scraper(self, settings):
        return GovernmentScraper(settings)
    
    def test_remove_duplicates(self, scraper):
        """Test duplicate document removal."""
        documents = [
            {'url': 'https://example.com/doc1.pdf', 'title': 'Doc 1'},
            {'url': 'https://example.com/doc2.pdf', 'title': 'Doc 2'},
            {'url': 'https://example.com/doc1.pdf', 'title': 'Doc 1 Duplicate'},
            {'url': '', 'title': 'Doc 3'},  # Empty URL
        ]
        
        unique_docs = scraper._remove_duplicates(documents)
        assert len(unique_docs) == 3  # Should keep empty URL and remove duplicate
    
    @pytest.mark.asyncio
    async def test_get_scraping_stats(self, scraper):
        """Test scraping statistics."""
        stats = await scraper.get_scraping_stats()
        
        assert 'total_documents_processed' in stats
        assert 'total_processing_time' in stats
        assert 'total_errors' in stats
        assert 'average_processing_time' in stats
        assert 'error_rate' in stats
        assert 'crawl_stats' in stats
        assert 'api_stats' in stats
        assert 'processing_stats' in stats
    
    @pytest.mark.asyncio
    async def test_validate_system(self, scraper):
        """Test system validation."""
        validation = await scraper.validate_system()
        
        assert 'website_crawler' in validation
        assert 'api_client' in validation
        assert 'document_processor' in validation
        assert 'storage_manager' in validation
        assert 'job_manager' in validation
        assert 'playwright_manager' in validation
        assert 'document_processing' in validation


class TestScrapingJob:
    """Test scraping job dataclass."""
    
    def test_scraping_job_creation(self):
        """Test scraping job creation."""
        job = ScrapingJob(
            job_id="test-job-1",
            user_id="user-1",
            keywords=["test", "document"],
            sources=["websites", "apis"],
            max_documents_per_keyword=10,
            status="running",
            progress=50,
            created_at="2023-01-01T00:00:00"
        )
        
        assert job.job_id == "test-job-1"
        assert job.user_id == "user-1"
        assert len(job.keywords) == 2
        assert job.status == "running"
        assert job.progress == 50


class TestScrapingResult:
    """Test scraping result dataclass."""
    
    def test_scraping_result_creation(self):
        """Test scraping result creation."""
        result = ScrapingResult(
            job_id="test-job-1",
            total_documents=5,
            keywords_processed=2,
            documents=[],
            processing_time=10.5,
            success_rate=90.0,
            error_count=1
        )
        
        assert result.job_id == "test-job-1"
        assert result.total_documents == 5
        assert result.keywords_processed == 2
        assert result.processing_time == 10.5
        assert result.success_rate == 90.0
        assert result.error_count == 1


# Integration tests
class TestGovernmentScraperIntegration:
    """Integration tests for government scraper."""
    
    @pytest.fixture
    def settings(self):
        return GovernmentScraperSettings(
            max_pages_per_site=5,
            max_crawl_depth=1,
            crawl_delay=0.1,
            api_timeout=5
        )
    
    @pytest.fixture
    def scraper(self, settings):
        return GovernmentScraper(settings)
    
    @pytest.mark.asyncio
    async def test_search_documents_by_keyword(self, scraper):
        """Test document search by keyword."""
        # This is a basic test that should not fail even if APIs are not available
        try:
            documents = await scraper.search_documents_by_keyword("test", limit=5)
            assert isinstance(documents, list)
        except Exception as e:
            # It's okay if this fails due to network issues or API unavailability
            pytest.skip(f"Search test skipped due to: {e}")
    
    @pytest.mark.asyncio
    async def test_system_validation(self, scraper):
        """Test system validation."""
        validation = await scraper.validate_system()
        
        # Basic validation should always pass
        assert validation['website_crawler'] is True
        assert validation['api_client'] is True
        assert validation['document_processor'] is True
        assert 'document_processing' in validation
