"""
Unit tests for paper scraper components.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.scrapers.paper_scraper.config import PaperScraperSettings
from src.scrapers.paper_scraper.arxiv_client import ArxivClient
from src.scrapers.paper_scraper.grobid_client import GrobidClient
from src.scrapers.paper_scraper.crossref_client import CrossRefClient
from src.scrapers.paper_scraper.content_analyzer import PaperContentAnalyzer, AnalysisResult
from src.scrapers.paper_scraper.paper_scraper import PaperScraper, ScrapingJob, ScrapingResult


class TestPaperScraperSettings:
    """Test paper scraper configuration settings."""
    
    def test_default_settings(self):
        """Test default configuration values."""
        settings = PaperScraperSettings()
        
        assert settings.arxiv_max_results == 100
        assert settings.arxiv_delay_seconds == 3.0
        assert settings.grobid_url == "http://localhost:8070"
        assert settings.extract_pdfs is True
        assert settings.analyze_content is True
        assert settings.llm_provider == "openrouter"


class TestArxivClient:
    """Test arXiv client functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return PaperScraperSettings(
            arxiv_max_results=10,
            arxiv_delay_seconds=0.1,
            arxiv_max_retries=2
        )
    
    @pytest.fixture
    def client(self, config):
        """Create arXiv client instance."""
        return ArxivClient(config)
    
    @pytest.mark.asyncio
    async def test_search_papers_success(self, client):
        """Test successful paper search."""
        # Mock arxiv client
        mock_result = Mock()
        mock_result.title = "Test Paper"
        mock_result.summary = "Test abstract"
        mock_result.authors = [Mock(name="Test Author")]
        mock_result.entry_id = "http://arxiv.org/abs/2103.12345"
        mock_result.pdf_url = "http://arxiv.org/pdf/2103.12345.pdf"
        mock_result.published = datetime(2021, 3, 15)
        mock_result.updated = datetime(2021, 3, 20)
        mock_result.doi = "10.1234/test.2021"
        mock_result.journal_ref = "Test Journal"
        mock_result.comment = "Test comment"
        mock_result.categories = ["cs.AI", "cs.LG"]
        mock_result.primary_category = "cs.AI"
        
        with patch('src.scrapers.paper_scraper.arxiv_client.arxiv') as mock_arxiv:
            mock_arxiv.Client.return_value.results.return_value = [mock_result]
            
            results = await client.search_papers("machine learning", max_results=5)
            
            assert len(results) == 1
            assert results[0]['title'] == "Test Paper"
            assert results[0]['arxiv_id'] == "2103.12345"
            assert results[0]['authors'] == ["Test Author"]
            assert results[0]['pdf_url'] == "http://arxiv.org/pdf/2103.12345.pdf"
    
    @pytest.mark.asyncio
    async def test_search_papers_failure(self, client):
        """Test paper search failure."""
        with patch('src.scrapers.paper_scraper.arxiv_client.arxiv') as mock_arxiv:
            mock_arxiv.Client.return_value.results.side_effect = Exception("API Error")
            
            results = await client.search_papers("machine learning")
            
            assert results == []


class TestGrobidClient:
    """Test Grobid client functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return PaperScraperSettings(
            grobid_url="http://localhost:8070",
            grobid_timeout=300
        )
    
    @pytest.fixture
    def client(self, config):
        """Create Grobid client instance."""
        return GrobidClient(config)
    
    @pytest.mark.asyncio
    async def test_check_service_health_success(self, client):
        """Test successful health check."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            result = await client.check_service_health()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_service_health_failure(self, client):
        """Test health check failure."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.side_effect = Exception("Connection failed")
            
            result = await client.check_service_health()
            
            assert result is False


class TestCrossRefClient:
    """Test CrossRef client functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return PaperScraperSettings(
            crossref_user_agent="TestAgent/1.0",
            crossref_max_results=10,
            crossref_delay_seconds=0.1
        )
    
    @pytest.fixture
    def client(self, config):
        """Create CrossRef client instance."""
        return CrossRefClient(config)
    
    @pytest.mark.asyncio
    async def test_search_papers_success(self, client):
        """Test successful paper search."""
        mock_response_data = {
            "message": {
                "items": [
                    {
                        "DOI": "10.1234/test.2021",
                        "title": ["Test Paper"],
                        "author": [{"given": "Test", "family": "Author"}],
                        "abstract": "Test abstract",
                        "container-title": ["Test Journal"],
                        "published-print": {"date-parts": [[2021, 3, 15]]},
                        "type": "journal-article",
                        "publisher": "Test Publisher"
                    }
                ]
            }
        }
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            results = await client.search_papers("machine learning", max_results=5)
            
            assert len(results) == 1
            assert results[0]['doi'] == "10.1234/test.2021"
            assert results[0]['title'] == "Test Paper"
            assert len(results[0]['authors']) == 1
            assert results[0]['authors'][0]['given'] == "Test"


class TestPaperContentAnalyzer:
    """Test paper content analyzer functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return PaperScraperSettings(
            max_content_length=5000,
            analyze_content=True
        )
    
    @pytest.fixture
    def llm_service(self):
        """Create mock LLM service."""
        service = Mock()
        service.generate_text = AsyncMock(return_value="Test response")
        return service
    
    @pytest.fixture
    def analyzer(self, config, llm_service):
        """Create content analyzer instance."""
        return PaperContentAnalyzer(config, llm_service)
    
    @pytest.mark.asyncio
    async def test_analyze_paper_success(self, analyzer):
        """Test successful paper analysis."""
        paper_data = {
            'title': 'Test Paper',
            'abstract': 'This is a test abstract about machine learning.',
            'body': {'text': 'This is the main content of the paper.'},
            'keywords': ['machine learning', 'artificial intelligence']
        }
        
        result = await analyzer.analyze_paper(paper_data)
        
        assert result is not None
        assert isinstance(result, AnalysisResult)
        assert result.summary
        assert result.keywords
        assert result.topics
        assert 0.0 <= result.quality_score <= 1.0
        assert result.language == "en"
        assert result.content_type == "research_paper"
    
    def test_fallback_methods(self, config):
        """Test fallback methods when LLM service is not available."""
        analyzer = PaperContentAnalyzer(config, None)
        
        content = "This is a test content for analysis."
        
        # Test fallback summary
        summary = analyzer._fallback_summary(content)
        assert summary
        
        # Test fallback quality score
        score = analyzer._fallback_quality_score(content)
        assert 0.0 <= score <= 1.0
        
        # Test fallback language detection
        language = analyzer._fallback_language_detection(content)
        assert language == "en"


class TestPaperScraper:
    """Test main paper scraper functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return PaperScraperSettings(
            arxiv_max_results=10,
            arxiv_delay_seconds=0.1,
            extract_pdfs=True,
            analyze_content=True,
            parallel_processing=True
        )
    
    @pytest.fixture
    def mock_clients(self):
        """Create mock clients."""
        arxiv_client = Mock()
        grobid_client = Mock()
        crossref_client = Mock()
        content_analyzer = Mock()
        storage_manager = Mock()
        job_manager = Mock()
        
        return {
            'arxiv_client': arxiv_client,
            'grobid_client': grobid_client,
            'crossref_client': crossref_client,
            'content_analyzer': content_analyzer,
            'storage_manager': storage_manager,
            'job_manager': job_manager
        }
    
    @pytest.fixture
    def scraper(self, config, mock_clients):
        """Create paper scraper instance."""
        return PaperScraper(
            config=config,
            arxiv_client=mock_clients['arxiv_client'],
            grobid_client=mock_clients['grobid_client'],
            crossref_client=mock_clients['crossref_client'],
            content_analyzer=mock_clients['content_analyzer'],
            storage_manager=mock_clients['storage_manager'],
            job_manager=mock_clients['job_manager']
        )
    
    def test_remove_duplicates(self, scraper):
        """Test duplicate removal functionality."""
        papers = [
            {'title': 'Paper 1', 'content_hash': 'hash1'},
            {'title': 'Paper 2', 'content_hash': 'hash1'},  # Duplicate hash
            {'title': 'Paper 3', 'content_hash': 'hash2'},
            {'title': 'Paper 4'},  # No hash
            {'title': 'Paper 4'},  # Duplicate title
        ]
        
        unique_papers = scraper._remove_duplicates(papers)
        
        assert len(unique_papers) == 3  # Should remove 2 duplicates
        assert unique_papers[0]['title'] == 'Paper 1'
        assert unique_papers[1]['title'] == 'Paper 3'
        assert unique_papers[2]['title'] == 'Paper 4'
    
    @pytest.mark.asyncio
    async def test_get_scraping_stats(self, scraper, mock_clients):
        """Test getting scraping statistics."""
        mock_clients['arxiv_client'].check_service_health = AsyncMock(return_value=True)
        mock_clients['grobid_client'].check_service_health = AsyncMock(return_value=True)
        mock_clients['crossref_client'].check_service_health = AsyncMock(return_value=True)
        
        stats = await scraper.get_scraping_stats()
        
        assert stats['arxiv_health'] is True
        assert stats['grobid_health'] is True
        assert stats['crossref_health'] is True
        assert 'config' in stats


if __name__ == "__main__":
    pytest.main([__file__])
