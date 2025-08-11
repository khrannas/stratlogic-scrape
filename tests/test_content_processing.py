"""
Tests for content processing functionality.

This module contains basic tests for content enrichment,
document processing, analytics, and export services.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.core.models.content_processing import (
    ContentEnrichment, ContentType, QualityLevel, ProcessingStatus,
    ExportFormat, ReportType
)
from src.core.models import Artifact
from src.services.content_enrichment import ContentEnrichmentService
from src.services.analytics_service import AnalyticsService
from src.services.export_service import ExportService
from src.core.exceptions import ContentProcessingError


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.add = AsyncMock()
    return db


@pytest.fixture
def mock_minio_client():
    """Mock MinIO client."""
    client = AsyncMock()
    client.download_file = AsyncMock(return_value=b"test file content")
    client.upload_file = AsyncMock()
    return client


@pytest.fixture
def sample_artifact():
    """Sample artifact for testing."""
    return Artifact(
        id=uuid4(),
        title="Test Document",
        description="A test document for content processing",
        content_text="This is a test document with some content for processing.",
        artifact_type="document",
        mime_type="text/plain",
        keywords=["test", "document"],
        tags=["test", "sample"]
    )


class TestContentEnrichmentService:
    """Tests for ContentEnrichmentService."""
    
    async def test_enrich_artifact_success(self, mock_db, sample_artifact):
        """Test successful artifact enrichment."""
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            sample_artifact,  # get_artifact
            None,  # get_existing_enrichment
        ]
        
        service = ContentEnrichmentService(mock_db)
        enrichment = await service.enrich_artifact(sample_artifact.id)
        
        assert enrichment is not None
        assert enrichment.artifact_id == sample_artifact.id
        assert enrichment.content_type == ContentType.TEXT
        assert enrichment.processing_status == ProcessingStatus.COMPLETED
    
    async def test_determine_content_type(self, mock_db):
        """Test content type determination."""
        service = ContentEnrichmentService(mock_db)
        
        artifact_pdf = Artifact(mime_type="application/pdf")
        artifact_image = Artifact(mime_type="image/jpeg")
        
        assert service._determine_content_type(artifact_pdf) == ContentType.PDF
        assert service._determine_content_type(artifact_image) == ContentType.IMAGE
    
    async def test_calculate_readability(self, mock_db):
        """Test readability calculation."""
        service = ContentEnrichmentService(mock_db)
        
        text = "This is a simple test sentence. It has multiple sentences."
        readability = await service._calculate_readability(text)
        
        assert 0.0 <= readability <= 1.0


class TestAnalyticsService:
    """Tests for AnalyticsService."""
    
    async def test_create_content_analytics_success(self, mock_db):
        """Test successful analytics creation."""
        content_enrichment = ContentEnrichment(
            id=uuid4(),
            content_type=ContentType.DOCUMENT,
            quality_score=0.8,
            word_count=1000
        )
        
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            None,  # get_existing_analytics
            content_enrichment,  # get_content_enrichment
        ]
        
        service = AnalyticsService(mock_db)
        analytics = await service.create_content_analytics(content_enrichment.id)
        
        assert analytics is not None
        assert analytics.content_id == content_enrichment.id
        assert analytics.impact_score is not None
    
    async def test_record_content_view(self, mock_db):
        """Test recording content view."""
        analytics = ContentAnalytics(
            id=uuid4(),
            content_id=uuid4(),
            view_count=5
        )
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = analytics
        
        service = AnalyticsService(mock_db)
        await service.record_content_view(uuid4())
        
        assert analytics.view_count == 6


class TestExportService:
    """Tests for ExportService."""
    
    async def test_create_export_job_success(self, mock_db, mock_minio_client):
        """Test successful export job creation."""
        service = ExportService(mock_db, mock_minio_client)
        export_job = await service.create_export_job(
            uuid4(),
            ExportFormat.CSV,
            {"type": "content"}
        )
        
        assert export_job is not None
        assert export_job.export_format == ExportFormat.CSV
        assert export_job.status == ProcessingStatus.COMPLETED
    
    async def test_create_report_success(self, mock_db, mock_minio_client):
        """Test successful report creation."""
        service = ExportService(mock_db, mock_minio_client)
        report = await service.create_report(
            uuid4(),
            ReportType.CONTENT_ANALYSIS,
            "Test Report"
        )
        
        assert report is not None
        assert report.report_type == ReportType.CONTENT_ANALYSIS
        assert report.report_title == "Test Report"
