import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from src.scrapers.paper_scraper.paper_scraper import PaperScraper
from src.scrapers.paper_scraper.arxiv_client import ArxivClient
from src.scrapers.paper_scraper.grobid_client import GrobidClient
from src.scrapers.paper_scraper.crossref_client import CrossRefClient
from src.scrapers.paper_scraper.content_analyzer import PaperContentAnalyzer

@pytest.fixture
def sample_arxiv_paper() -> Dict[str, Any]:
    """Sample arXiv paper data for testing"""
    return {
        'arxiv_id': '2401.12345',
        'title': 'Sample Research Paper on Machine Learning',
        'authors': [
            {'name': 'John Doe'},
            {'name': 'Jane Smith'}
        ],
        'summary': 'This is a sample abstract for testing purposes.',
        'categories': ['cs.AI', 'cs.LG'],
        'published_date': '2024-01-15T00:00:00Z',
        'updated_date': '2024-01-15T00:00:00Z',
        'pdf_url': 'https://arxiv.org/pdf/2401.12345.pdf',
        'doi': '10.1234/sample.2024.12345',
        'journal_ref': 'Sample Journal, 2024',
        'primary_category': 'cs.AI',
        'comment': 'Sample comment',
        'links': ['https://arxiv.org/abs/2401.12345'],
        'source': 'arxiv'
    }

@pytest.fixture
def sample_crossref_paper() -> Dict[str, Any]:
    """Sample CrossRef paper data for testing"""
    return {
        'doi': '10.1234/sample.2024.12345',
        'title': 'Sample Research Paper on Machine Learning',
        'authors': [
            {'given': 'John', 'family': 'Doe', 'name': 'John Doe'},
            {'given': 'Jane', 'family': 'Smith', 'name': 'Jane Smith'}
        ],
        'abstract': 'This is a sample abstract for testing purposes.',
        'journal': 'Sample Journal',
        'published_date': '2024-01-15',
        'type': 'journal-article',
        'url': 'https://example.com/paper',
        'subject': ['Computer Science', 'Machine Learning'],
        'language': 'en',
        'issn': ['1234-5678'],
        'volume': '1',
        'issue': '1',
        'page': '1-10',
        'publisher': 'Sample Publisher',
        'reference_count': 20,
        'is_referenced_by_count': 5,
        'source': 'crossref'
    }

@pytest.fixture
def sample_grobid_extraction() -> Dict[str, Any]:
    """Sample Grobid extraction data for testing"""
    return {
        'header': {
            'title': 'Sample Research Paper on Machine Learning',
            'authors': [
                {'name': 'John Doe'},
                {'name': 'Jane Smith'}
            ],
            'abstract': 'This is a sample abstract extracted from PDF.',
            'keywords': ['machine learning', 'artificial intelligence', 'research'],
            'publication_date': '2024-01-15'
        },
        'body_text': 'This is the main body text extracted from the PDF...',
        'citations': [
            {
                'title': 'Cited Paper 1',
                'authors': [{'name': 'Author 1'}],
                'date': '2023'
            },
            {
                'title': 'Cited Paper 2',
                'authors': [{'name': 'Author 2'}],
                'date': '2022'
            }
        ],
        'raw_xml': '<xml>Sample XML content</xml>'
    }

@pytest.fixture
def sample_content_analysis() -> Dict[str, Any]:
    """Sample content analysis data for testing"""
    return {
        'paper_id': '2401.12345',
        'analysis_timestamp': '2024-01-15T12:00:00Z',
        'analysis_version': '1.0',
        'keywords': ['machine learning', 'artificial intelligence', 'neural networks'],
        'summary': {
            'summary_text': 'This paper presents a novel approach to machine learning...',
            'word_count': 150,
            'generated_at': '2024-01-15T12:00:00Z'
        },
        'citation_analysis': {
            'total_citations': 2,
            'citation_years': [2023, 2022],
            'average_citation_year': 2022.5,
            'oldest_citation_year': 2022,
            'newest_citation_year': 2023
        },
        'quality_assessment': {
            'score': 8.5,
            'assessment_text': 'This is a high-quality research paper...',
            'assessed_at': '2024-01-15T12:00:00Z'
        },
        'key_insights': [
            'Novel machine learning approach',
            'Improved performance on benchmark datasets',
            'Potential applications in real-world scenarios'
        ]
    }

@pytest.fixture
def mock_arxiv_client():
    """Mock arXiv client for testing"""
    client = Mock(spec=ArxivClient)
    client.search_papers = AsyncMock()
    client.get_paper_by_id = AsyncMock()
    client.download_paper_pdf = AsyncMock()
    return client

@pytest.fixture
def mock_grobid_client():
    """Mock Grobid client for testing"""
    client = Mock(spec=GrobidClient)
    client.extract_pdf_content = AsyncMock()
    client.extract_header_only = AsyncMock()
    client.check_service_health = AsyncMock()
    return client

@pytest.fixture
def mock_crossref_client():
    """Mock CrossRef client for testing"""
    client = Mock(spec=CrossRefClient)
    client.search_works = AsyncMock()
    client.get_work_by_doi = AsyncMock()
    return client

@pytest.fixture
def mock_content_analyzer():
    """Mock content analyzer for testing"""
    analyzer = Mock(spec=PaperContentAnalyzer)
    analyzer.analyze_paper = AsyncMock()
    analyzer.compare_papers = AsyncMock()
    return analyzer

@pytest.fixture
def paper_scraper_instance(
    mock_arxiv_client,
    mock_grobid_client,
    mock_crossref_client,
    mock_content_analyzer
):
    """Paper scraper instance with mocked dependencies"""
    scraper = PaperScraper()
    scraper.arxiv_client = mock_arxiv_client
    scraper.grobid_client = mock_grobid_client
    scraper.crossref_client = mock_crossref_client
    scraper.content_analyzer = mock_content_analyzer
    return scraper

@pytest.fixture
def sample_job_data() -> Dict[str, Any]:
    """Sample job data for testing"""
    return {
        'id': 'test-job-123',
        'user_id': 'test-user-123',
        'job_type': 'paper_scraping',
        'status': 'pending',
        'progress': 0,
        'parameters': {
            'query': 'machine learning',
            'max_results': 10,
            'sources': ['arxiv'],
            'extract_pdfs': True,
            'analyze_content': True,
            'download_pdfs': True
        },
        'created_at': '2024-01-15T12:00:00Z',
        'updated_at': '2024-01-15T12:00:00Z'
    }
