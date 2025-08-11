"""
Tests for search functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.core.models.search import (
    AnalysisType, ContentAnalysis, SearchEmbedding, SearchIndex, SearchQuery, SearchType
)
from src.services.search_service import SearchService
from src.core.models import Artifact, User


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def search_service(mock_db):
    """Create search service with mocked dependencies."""
    return SearchService(mock_db)


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        role="USER"
    )


@pytest.fixture
def sample_artifact():
    """Create a sample artifact for testing."""
    return Artifact(
        id=uuid4(),
        user_id=uuid4(),
        job_id=uuid4(),
        artifact_type="web_page",
        title="Test Document",
        description="A test document for search testing",
        content_text="This is a test document about machine learning and artificial intelligence.",
        keywords=["machine learning", "AI", "testing"],
        tags=["test", "document"],
        language="en"
    )


class TestSearchModels:
    """Test cases for search models."""
    
    def test_search_type_enum(self):
        """Test SearchType enum values."""
        assert SearchType.FULL_TEXT == "full_text"
        assert SearchType.SEMANTIC == "semantic"
        assert SearchType.HYBRID == "hybrid"
    
    def test_analysis_type_enum(self):
        """Test AnalysisType enum values."""
        assert AnalysisType.KEYWORD_EXTRACTION == "keyword_extraction"
        assert AnalysisType.SENTIMENT_ANALYSIS == "sentiment_analysis"
        assert AnalysisType.ENTITY_EXTRACTION == "entity_extraction"
        assert AnalysisType.SUMMARIZATION == "summarization"
    
    def test_search_index_model(self):
        """Test SearchIndex model creation."""
        artifact_id = uuid4()
        search_index = SearchIndex(
            artifact_id=artifact_id,
            content_text="Test content for search",
            search_vector="test vector",
            title="Test Title",
            description="Test description",
            keywords='["keyword1", "keyword2"]',
            tags='["tag1", "tag2"]',
            language="en"
        )
        
        assert search_index.artifact_id == artifact_id
        assert search_index.content_text == "Test content for search"
        assert search_index.title == "Test Title"
        assert search_index.language == "en"
    
    def test_search_embedding_model(self):
        """Test SearchEmbedding model creation."""
        artifact_id = uuid4()
        embedding = SearchEmbedding(
            artifact_id=artifact_id,
            model_name="all-MiniLM-L6-v2",
            embedding_vector="[0.1, 0.2, 0.3]",
            content_hash="abc123"
        )
        
        assert embedding.artifact_id == artifact_id
        assert embedding.model_name == "all-MiniLM-L6-v2"
        assert embedding.embedding_vector == "[0.1, 0.2, 0.3]"
        assert embedding.content_hash == "abc123"
    
    def test_content_analysis_model(self):
        """Test ContentAnalysis model creation."""
        artifact_id = uuid4()
        analysis = ContentAnalysis(
            artifact_id=artifact_id,
            analysis_type=AnalysisType.KEYWORD_EXTRACTION,
            analysis_data='{"keywords": ["test", "analysis"]}',
            confidence_score=0.95,
            model_used="langchain",
            processing_time_ms=150.5
        )
        
        assert analysis.artifact_id == artifact_id
        assert analysis.analysis_type == AnalysisType.KEYWORD_EXTRACTION
        assert analysis.analysis_data == '{"keywords": ["test", "analysis"]}'
        assert analysis.confidence_score == 0.95
        assert analysis.model_used == "langchain"
    
    def test_search_query_model(self):
        """Test SearchQuery model creation."""
        user_id = uuid4()
        search_query = SearchQuery(
            user_id=user_id,
            query_text="test query",
            search_type=SearchType.FULL_TEXT,
            filters='{"filter": "value"}',
            results_count=10,
            processing_time_ms=100.5
        )
        
        assert search_query.user_id == user_id
        assert search_query.query_text == "test query"
        assert search_query.search_type == SearchType.FULL_TEXT
        assert search_query.filters == '{"filter": "value"}'
        assert search_query.results_count == 10


class TestSearchService:
    """Test cases for SearchService."""
    
    @patch('src.services.search_service.SentenceTransformer')
    async def test_sentence_model_lazy_loading(self, mock_transformer, search_service):
        """Test lazy loading of sentence transformer model."""
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_transformer.return_value = mock_model
        
        model = search_service.sentence_model
        assert model == mock_model
        mock_transformer.assert_called_once_with('all-MiniLM-L6-v2')
        
        model2 = search_service.sentence_model
        assert model2 == mock_model
        assert mock_transformer.call_count == 1
    
    async def test_index_artifact_for_search_success(self, search_service, sample_artifact):
        """Test successful artifact indexing."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_artifact
        search_service.db.execute.return_value = mock_result
        
        mock_text_result = MagicMock()
        mock_text_result.scalar.return_value = "test_vector"
        search_service.db.execute.side_effect = [mock_result, mock_text_result]
        
        mock_index_result = MagicMock()
        mock_index_result.scalar_one_or_none.return_value = None
        search_service.db.execute.side_effect = [
            mock_result, mock_text_result, mock_index_result
        ]
        
        success = await search_service.index_artifact_for_search(sample_artifact.id)
        
        assert success is True
        assert search_service.db.commit.called
    
    async def test_index_artifact_for_search_no_content(self, search_service):
        """Test artifact indexing with no content."""
        artifact_no_content = Artifact(
            id=uuid4(),
            user_id=uuid4(),
            job_id=uuid4(),
            artifact_type="web_page",
            title="Test",
            content_text=None
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = artifact_no_content
        search_service.db.execute.return_value = mock_result
        
        success = await search_service.index_artifact_for_search(artifact_no_content.id)
        
        assert success is False
    
    async def test_full_text_search(self, search_service, sample_user):
        """Test full-text search functionality."""
        mock_row = MagicMock()
        mock_row.artifact_id = uuid4()
        mock_row.title = "Test Document"
        mock_row.description = "Test description"
        mock_row.keywords = '["keyword1", "keyword2"]'
        mock_row.tags = '["tag1", "tag2"]'
        mock_row.rank = 0.85
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        search_service.db.execute.return_value = mock_result
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1
        search_service.db.execute.side_effect = [mock_result, mock_count_result]
        
        results, total_count = await search_service.full_text_search(
            query="test query",
            user_id=sample_user.id,
            limit=10,
            offset=0
        )
        
        assert len(results) == 1
        assert total_count == 1
        assert results[0]["title"] == "Test Document"
        assert results[0]["rank"] == 0.85
        assert search_service.db.commit.called
    
    @patch('src.services.search_service.util.cos_sim')
    async def test_semantic_search(self, mock_cos_sim, search_service, sample_user):
        """Test semantic search functionality."""
        mock_embedding = MagicMock()
        mock_embedding.artifact_id = uuid4()
        mock_embedding.embedding_vector = "[0.1, 0.2, 0.3]"
        
        mock_embeddings_result = MagicMock()
        mock_embeddings_result.scalars.return_value.all.return_value = [mock_embedding]
        search_service.db.execute.return_value = mock_embeddings_result
        
        mock_artifact = MagicMock()
        mock_artifact.id = uuid4()
        mock_artifact.title = "Test Document"
        mock_artifact.description = "Test description"
        mock_artifact.keywords = ["keyword1", "keyword2"]
        mock_artifact.tags = ["tag1", "tag2"]
        
        mock_artifact_result = MagicMock()
        mock_artifact_result.scalar_one_or_none.return_value = mock_artifact
        search_service.db.execute.side_effect = [
            mock_embeddings_result, mock_artifact_result
        ]
        
        mock_cos_sim.return_value = 0.75
        
        results, total_count = await search_service.semantic_search(
            query="test query",
            user_id=sample_user.id,
            limit=10,
            offset=0
        )
        
        assert len(results) == 1
        assert total_count == 1
        assert results[0]["title"] == "Test Document"
        assert results[0]["similarity"] == 0.75
        assert search_service.db.commit.called
    
    async def test_semantic_search_no_embeddings(self, search_service, sample_user):
        """Test semantic search with no embeddings."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        search_service.db.execute.return_value = mock_result
        
        results, total_count = await search_service.semantic_search(
            query="test query",
            user_id=sample_user.id
        )
        
        assert len(results) == 0
        assert total_count == 0
    
    async def test_record_search_query(self, search_service, sample_user):
        """Test recording search query."""
        await search_service._record_search_query(
            user_id=sample_user.id,
            query_text="test query",
            search_type=SearchType.FULL_TEXT,
            results_count=5,
            processing_time_ms=100.5
        )
        
        assert search_service.db.add.called
        assert search_service.db.commit.called
        
        added_query = search_service.db.add.call_args[0][0]
        assert isinstance(added_query, SearchQuery)
        assert added_query.user_id == sample_user.id
        assert added_query.query_text == "test query"
        assert added_query.search_type == SearchType.FULL_TEXT
        assert added_query.results_count == 5
        assert added_query.processing_time_ms == 100.5
