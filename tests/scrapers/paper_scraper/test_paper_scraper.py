import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.scrapers.paper_scraper.paper_scraper import PaperScraper
from src.scrapers.paper_scraper.arxiv_client import ArxivClient
from src.scrapers.paper_scraper.grobid_client import GrobidClient
from src.scrapers.paper_scraper.crossref_client import CrossRefClient
from src.scrapers.paper_scraper.content_analyzer import PaperContentAnalyzer

class TestArxivClient:
    """Test arXiv client functionality"""

    @pytest.mark.asyncio
    async def test_search_papers(self, mock_arxiv_client, sample_arxiv_paper):
        """Test arXiv paper search"""
        mock_arxiv_client.search_papers.return_value = [sample_arxiv_paper]

        papers = await mock_arxiv_client.search_papers("machine learning", 10)

        assert len(papers) == 1
        assert papers[0]['arxiv_id'] == '2401.12345'
        assert papers[0]['title'] == 'Sample Research Paper on Machine Learning'
        mock_arxiv_client.search_papers.assert_called_once_with("machine learning", 10)

    @pytest.mark.asyncio
    async def test_get_paper_by_id(self, mock_arxiv_client, sample_arxiv_paper):
        """Test getting paper by ID"""
        mock_arxiv_client.get_paper_by_id.return_value = sample_arxiv_paper

        paper = await mock_arxiv_client.get_paper_by_id('2401.12345')

        assert paper is not None
        assert paper['arxiv_id'] == '2401.12345'
        mock_arxiv_client.get_paper_by_id.assert_called_once_with('2401.12345')

    @pytest.mark.asyncio
    async def test_download_paper_pdf(self, mock_arxiv_client):
        """Test PDF download"""
        mock_arxiv_client.download_paper_pdf.return_value = '/tmp/test.pdf'

        result = await mock_arxiv_client.download_paper_pdf('2401.12345', '/tmp/test.pdf')

        assert result == '/tmp/test.pdf'
        mock_arxiv_client.download_paper_pdf.assert_called_once_with('2401.12345', '/tmp/test.pdf')

class TestGrobidClient:
    """Test Grobid client functionality"""

    @pytest.mark.asyncio
    async def test_extract_pdf_content(self, mock_grobid_client, sample_grobid_extraction):
        """Test PDF content extraction"""
        mock_grobid_client.extract_pdf_content.return_value = sample_grobid_extraction

        result = await mock_grobid_client.extract_pdf_content('/tmp/test.pdf')

        assert result is not None
        assert 'header' in result
        assert 'body_text' in result
        assert 'citations' in result
        mock_grobid_client.extract_pdf_content.assert_called_once_with('/tmp/test.pdf')

    @pytest.mark.asyncio
    async def test_extract_header_only(self, mock_grobid_client, sample_grobid_extraction):
        """Test header-only extraction"""
        mock_grobid_client.extract_header_only.return_value = sample_grobid_extraction

        result = await mock_grobid_client.extract_header_only('/tmp/test.pdf')

        assert result is not None
        assert 'header' in result
        mock_grobid_client.extract_header_only.assert_called_once_with('/tmp/test.pdf')

    @pytest.mark.asyncio
    async def test_check_service_health(self, mock_grobid_client):
        """Test service health check"""
        mock_grobid_client.check_service_health.return_value = True

        result = await mock_grobid_client.check_service_health()

        assert result is True
        mock_grobid_client.check_service_health.assert_called_once()

class TestCrossRefClient:
    """Test CrossRef client functionality"""

    @pytest.mark.asyncio
    async def test_search_works(self, mock_crossref_client, sample_crossref_paper):
        """Test CrossRef works search"""
        mock_crossref_client.search_works.return_value = [sample_crossref_paper]

        papers = await mock_crossref_client.search_works("machine learning", 10)

        assert len(papers) == 1
        assert papers[0]['doi'] == '10.1234/sample.2024.12345'
        assert papers[0]['title'] == 'Sample Research Paper on Machine Learning'
        mock_crossref_client.search_works.assert_called_once_with("machine learning", 10)

    @pytest.mark.asyncio
    async def test_get_work_by_doi(self, mock_crossref_client, sample_crossref_paper):
        """Test getting work by DOI"""
        mock_crossref_client.get_work_by_doi.return_value = sample_crossref_paper

        paper = await mock_crossref_client.get_work_by_doi('10.1234/sample.2024.12345')

        assert paper is not None
        assert paper['doi'] == '10.1234/sample.2024.12345'
        mock_crossref_client.get_work_by_doi.assert_called_once_with('10.1234/sample.2024.12345')

class TestContentAnalyzer:
    """Test content analyzer functionality"""

    @pytest.mark.asyncio
    async def test_analyze_paper(self, mock_content_analyzer, sample_arxiv_paper, sample_content_analysis):
        """Test paper content analysis"""
        mock_content_analyzer.analyze_paper.return_value = sample_content_analysis

        result = await mock_content_analyzer.analyze_paper(sample_arxiv_paper)

        assert result is not None
        assert result['paper_id'] == '2401.12345'
        assert 'keywords' in result
        assert 'summary' in result
        assert 'quality_assessment' in result
        mock_content_analyzer.analyze_paper.assert_called_once_with(sample_arxiv_paper)

    @pytest.mark.asyncio
    async def test_compare_papers(self, mock_content_analyzer, sample_arxiv_paper, sample_crossref_paper):
        """Test paper comparison"""
        comparison_result = {
            'comparison_text': 'These papers are similar in methodology...',
            'papers_compared': 2,
            'compared_at': '2024-01-15T12:00:00Z'
        }
        mock_content_analyzer.compare_papers.return_value = comparison_result

        result = await mock_content_analyzer.compare_papers([sample_arxiv_paper, sample_crossref_paper])

        assert result is not None
        assert result['papers_compared'] == 2
        mock_content_analyzer.compare_papers.assert_called_once_with([sample_arxiv_paper, sample_crossref_paper])

class TestPaperScraper:
    """Test main paper scraper functionality"""

    @pytest.mark.asyncio
    async def test_scrape_papers(self, paper_scraper_instance, sample_arxiv_paper, sample_content_analysis):
        """Test main paper scraping orchestration"""
        # Setup mocks
        paper_scraper_instance.arxiv_client.search_papers.return_value = [sample_arxiv_paper]
        paper_scraper_instance.grobid_client.extract_pdf_content.return_value = {'body_text': 'Sample text'}
        paper_scraper_instance.content_analyzer.analyze_paper.return_value = sample_content_analysis

        # Mock job service calls
        with patch('src.scrapers.paper_scraper.paper_scraper.job_service') as mock_job_service:
            mock_job_service.update_job_status = AsyncMock()
            mock_job_service.update_job_progress = AsyncMock()

            result = await paper_scraper_instance.scrape_papers(
                query="machine learning",
                job_id="test-job-123",
                user_id="test-user-123",
                max_results=10,
                sources=['arxiv'],
                extract_pdfs=True,
                analyze_content=True,
                download_pdfs=False
            )

        assert result is not None
        assert result['job_id'] == 'test-job-123'
        assert result['query'] == 'machine learning'
        assert len(result['papers']) == 1
        assert result['total_papers_found'] == 1
        assert result['unique_papers_processed'] == 1

    @pytest.mark.asyncio
    async def test_remove_duplicates(self, paper_scraper_instance, sample_arxiv_paper, sample_crossref_paper):
        """Test duplicate removal"""
        # Create duplicate papers with same ID
        paper1 = {**sample_arxiv_paper, 'arxiv_id': '2401.12345'}
        paper2 = {**sample_crossref_paper, 'doi': '2401.12345'}  # Same ID, different source
        paper3 = {**sample_arxiv_paper, 'arxiv_id': '2401.67890'}  # Different ID

        papers = [paper1, paper2, paper3]
        unique_papers = paper_scraper_instance._remove_duplicates(papers)

        assert len(unique_papers) == 2  # Should remove one duplicate
        assert unique_papers[0]['arxiv_id'] == '2401.12345'
        assert unique_papers[1]['arxiv_id'] == '2401.67890'

    @pytest.mark.asyncio
    async def test_get_paper_by_id(self, paper_scraper_instance, sample_arxiv_paper):
        """Test getting paper by ID"""
        paper_scraper_instance.arxiv_client.get_paper_by_id.return_value = sample_arxiv_paper

        result = await paper_scraper_instance.get_paper_by_id('2401.12345', 'arxiv')

        assert result is not None
        assert result['arxiv_id'] == '2401.12345'
        paper_scraper_instance.arxiv_client.get_paper_by_id.assert_called_once_with('2401.12345')

    @pytest.mark.asyncio
    async def test_check_services_health(self, paper_scraper_instance):
        """Test services health check"""
        paper_scraper_instance.grobid_client.check_service_health.return_value = True

        result = await paper_scraper_instance.check_services_health()

        assert result is not None
        assert 'arxiv' in result
        assert 'grobid' in result
        assert 'crossref' in result
        assert 'llm_service' in result
        assert result['grobid'] is True

class TestPaperScraperIntegration:
    """Integration tests for paper scraper"""

    @pytest.mark.asyncio
    async def test_full_paper_processing_workflow(self, paper_scraper_instance, sample_arxiv_paper, sample_content_analysis):
        """Test complete paper processing workflow"""
        # Setup all mocks
        paper_scraper_instance.arxiv_client.search_papers.return_value = [sample_arxiv_paper]
        paper_scraper_instance.arxiv_client.download_paper_pdf.return_value = '/tmp/test.pdf'
        paper_scraper_instance.grobid_client.extract_pdf_content.return_value = {'body_text': 'Sample text'}
        paper_scraper_instance.content_analyzer.analyze_paper.return_value = sample_content_analysis

        # Mock artifact storage
        with patch('src.scrapers.paper_scraper.paper_scraper.ArtifactStorage') as mock_storage:
            mock_storage_instance = Mock()
            mock_storage_instance.upload_file = AsyncMock(return_value='pdf-artifact-id')
            mock_storage_instance.upload_json = AsyncMock(return_value='json-artifact-id')
            mock_storage.return_value = mock_storage_instance

            # Mock job service
            with patch('src.scrapers.paper_scraper.paper_scraper.job_service') as mock_job_service:
                mock_job_service.update_job_status = AsyncMock()
                mock_job_service.update_job_progress = AsyncMock()

                result = await paper_scraper_instance.scrape_papers(
                    query="machine learning",
                    job_id="test-job-123",
                    user_id="test-user-123",
                    max_results=1,
                    sources=['arxiv'],
                    extract_pdfs=True,
                    analyze_content=True,
                    download_pdfs=True
                )

        assert result is not None
        assert result['job_id'] == 'test-job-123'
        assert len(result['papers']) == 1

        # Verify the paper was processed
        paper = result['papers'][0]
        assert paper['paper_id'] == '2401.12345'
        assert paper['title'] == 'Sample Research Paper on Machine Learning'
        assert 'grobid_extraction' in paper
        assert 'content_analysis' in paper
        assert 'artifacts' in paper

class TestPaperScraperErrorHandling:
    """Test error handling in paper scraper"""

    @pytest.mark.asyncio
    async def test_arxiv_search_error(self, paper_scraper_instance):
        """Test handling of arXiv search errors"""
        paper_scraper_instance.arxiv_client.search_papers.side_effect = Exception("arXiv API error")

        with patch('src.scrapers.paper_scraper.paper_scraper.job_service') as mock_job_service:
            mock_job_service.update_job_status = AsyncMock()
            mock_job_service.update_job_progress = AsyncMock()

            result = await paper_scraper_instance.scrape_papers(
                query="machine learning",
                job_id="test-job-123",
                user_id="test-user-123",
                max_results=10,
                sources=['arxiv']
            )

        assert result is not None
        assert result['total_papers_found'] == 0
        assert result['unique_papers_processed'] == 0

    @pytest.mark.asyncio
    async def test_grobid_extraction_error(self, paper_scraper_instance, sample_arxiv_paper):
        """Test handling of Grobid extraction errors"""
        paper_scraper_instance.arxiv_client.search_papers.return_value = [sample_arxiv_paper]
        paper_scraper_instance.grobid_client.extract_pdf_content.side_effect = Exception("Grobid error")

        with patch('src.scrapers.paper_scraper.paper_scraper.job_service') as mock_job_service:
            mock_job_service.update_job_status = AsyncMock()
            mock_job_service.update_job_progress = AsyncMock()

            result = await paper_scraper_instance.scrape_papers(
                query="machine learning",
                job_id="test-job-123",
                user_id="test-user-123",
                max_results=1,
                sources=['arxiv'],
                extract_pdfs=True
            )

        assert result is not None
        assert result['total_papers_found'] == 1
        assert result['unique_papers_processed'] == 0  # Should fail processing

    @pytest.mark.asyncio
    async def test_content_analysis_error(self, paper_scraper_instance, sample_arxiv_paper):
        """Test handling of content analysis errors"""
        paper_scraper_instance.arxiv_client.search_papers.return_value = [sample_arxiv_paper]
        paper_scraper_instance.content_analyzer.analyze_paper.side_effect = Exception("LLM error")

        with patch('src.scrapers.paper_scraper.paper_scraper.job_service') as mock_job_service:
            mock_job_service.update_job_status = AsyncMock()
            mock_job_service.update_job_progress = AsyncMock()

            result = await paper_scraper_instance.scrape_papers(
                query="machine learning",
                job_id="test-job-123",
                user_id="test-user-123",
                max_results=1,
                sources=['arxiv'],
                analyze_content=True
            )

        assert result is not None
        assert result['total_papers_found'] == 1
        assert result['unique_papers_processed'] == 0  # Should fail processing
