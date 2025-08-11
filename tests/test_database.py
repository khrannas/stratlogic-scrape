"""
Tests for database connection and operations.

This module tests database connectivity and basic operations.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.core.database import check_database_connection, create_tables, get_db
from src.core.config import settings


class TestDatabaseConnection:
    """Test database connection functionality."""
    
    @pytest.mark.unit
    def test_database_connection_success(self):
        """Test successful database connection."""
        with patch('src.core.database.engine') as mock_engine:
            mock_connection = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_connection
            mock_connection.execute.return_value = MagicMock()
            
            result = check_database_connection()
            assert result is True
    
    @pytest.mark.unit
    def test_database_connection_failure(self):
        """Test failed database connection."""
        with patch('src.core.database.engine') as mock_engine:
            mock_engine.connect.side_effect = Exception("Connection failed")
            
            result = check_database_connection()
            assert result is False
    
    @pytest.mark.unit
    def test_create_tables(self):
        """Test table creation."""
        with patch('src.core.database.Base.metadata.create_all') as mock_create:
            create_tables()
            mock_create.assert_called_once()
    
    @pytest.mark.unit
    def test_get_db_generator(self):
        """Test database session generator."""
        with patch('src.core.database.SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            
            db_gen = get_db()
            db = next(db_gen)
            
            assert db == mock_session
            
            # Test cleanup
            db_gen.close()
            mock_session.close.assert_called_once()


class TestDatabaseModels:
    """Test database models."""
    
    @pytest.mark.unit
    def test_user_model_creation(self):
        """Test User model creation."""
        from src.core.models import User, UserRole
        
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            role=UserRole.USER
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.is_verified is False
    
    @pytest.mark.unit
    def test_scraping_job_model_creation(self):
        """Test ScrapingJob model creation."""
        from src.core.models import ScrapingJob, JobStatus
        
        job = ScrapingJob(
            job_type="web",
            title="Test Job",
            description="Test description",
            status=JobStatus.PENDING
        )
        
        assert job.job_type == "web"
        assert job.title == "Test Job"
        assert job.status == JobStatus.PENDING
        assert job.progress == 0
        assert job.total_items == 0
    
    @pytest.mark.unit
    def test_artifact_model_creation(self):
        """Test Artifact model creation."""
        from src.core.models import Artifact, ArtifactType
        
        artifact = Artifact(
            artifact_type=ArtifactType.WEB_PAGE,
            title="Test Artifact",
            source_url="https://example.com",
            content_text="Test content"
        )
        
        assert artifact.artifact_type == ArtifactType.WEB_PAGE
        assert artifact.title == "Test Artifact"
        assert artifact.source_url == "https://example.com"
        assert artifact.content_text == "Test content"
