"""
Tests for SQLAlchemy models.

This module tests all database models and their relationships.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from src.core.models import (
    User, UserRole, UserSession, ScrapingJob, JobStatus, JobConfiguration,
    Artifact, ArtifactType, MetadataTag, ContentExtraction, SystemConfig,
    APIRateLimit, AuditLog, APIKey
)


class TestUserModel:
    """Test User model."""
    
    @pytest.mark.unit
    def test_user_creation(self):
        """Test user creation with all fields."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            role=UserRole.USER,
            is_active=True,
            is_verified=False
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password"
        assert user.full_name == "Test User"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.is_verified is False
        assert user.id is not None
    
    @pytest.mark.unit
    def test_user_defaults(self):
        """Test user creation with default values."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.is_verified is False
        assert user.full_name is None
    
    @pytest.mark.unit
    def test_user_properties(self):
        """Test user properties."""
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password="hash",
            role=UserRole.ADMIN
        )
        
        viewer_user = User(
            username="viewer",
            email="viewer@example.com",
            hashed_password="hash",
            role=UserRole.VIEWER
        )
        
        assert admin_user.is_admin is True
        assert viewer_user.is_viewer is True
        assert admin_user.is_viewer is False
    
    @pytest.mark.unit
    def test_user_repr(self):
        """Test user string representation."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hash"
        )
        
        repr_str = repr(user)
        assert "User" in repr_str
        assert "testuser" in repr_str
        assert "test@example.com" in repr_str


class TestUserSessionModel:
    """Test UserSession model."""
    
    @pytest.mark.unit
    def test_user_session_creation(self):
        """Test user session creation."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        session = UserSession(
            user_id="user-id",
            token_hash="token_hash",
            expires_at=expires_at
        )
        
        assert session.user_id == "user-id"
        assert session.token_hash == "token_hash"
        assert session.expires_at == expires_at
        assert session.is_expired is False
    
    @pytest.mark.unit
    def test_user_session_expired(self):
        """Test user session expiration."""
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        session = UserSession(
            user_id="user-id",
            token_hash="token_hash",
            expires_at=expires_at
        )
        
        assert session.is_expired is True
    
    @pytest.mark.unit
    def test_user_session_repr(self):
        """Test user session string representation."""
        session = UserSession(
            user_id="user-id",
            token_hash="token_hash",
            expires_at=datetime.now(timezone.utc)
        )
        
        repr_str = repr(session)
        assert "UserSession" in repr_str
        assert "user-id" in repr_str


class TestScrapingJobModel:
    """Test ScrapingJob model."""
    
    @pytest.mark.unit
    def test_scraping_job_creation(self):
        """Test scraping job creation."""
        job = ScrapingJob(
            user_id="user-id",
            job_type="web",
            title="Test Job",
            description="Test description",
            keywords=["test", "web"],
            status=JobStatus.PENDING
        )
        
        assert job.user_id == "user-id"
        assert job.job_type == "web"
        assert job.title == "Test Job"
        assert job.description == "Test description"
        assert job.keywords == ["test", "web"]
        assert job.status == JobStatus.PENDING
        assert job.progress == 0
        assert job.total_items == 0
        assert job.processed_items == 0
        assert job.failed_items == 0
    
    @pytest.mark.unit
    def test_scraping_job_properties(self):
        """Test scraping job properties."""
        completed_job = ScrapingJob(
            user_id="user-id",
            job_type="web",
            title="Completed Job",
            status=JobStatus.COMPLETED
        )
        
        running_job = ScrapingJob(
            user_id="user-id",
            job_type="web",
            title="Running Job",
            status=JobStatus.RUNNING
        )
        
        assert completed_job.is_completed is True
        assert running_job.is_running is True
        assert completed_job.is_running is False
    
    @pytest.mark.unit
    def test_scraping_job_success_rate(self):
        """Test scraping job success rate calculation."""
        job = ScrapingJob(
            user_id="user-id",
            job_type="web",
            title="Test Job",
            total_items=10,
            processed_items=8,
            failed_items=1
        )
        
        # (8 - 1) / 10 * 100 = 70%
        assert job.success_rate == 70.0
    
    @pytest.mark.unit
    def test_scraping_job_success_rate_zero_total(self):
        """Test success rate with zero total items."""
        job = ScrapingJob(
            user_id="user-id",
            job_type="web",
            title="Test Job",
            total_items=0
        )
        
        assert job.success_rate == 0.0
    
    @pytest.mark.unit
    def test_scraping_job_update_progress(self):
        """Test scraping job progress update."""
        job = ScrapingJob(
            user_id="user-id",
            job_type="web",
            title="Test Job"
        )
        
        job.update_progress(processed=5, total=10, failed=1)
        
        assert job.processed_items == 5
        assert job.total_items == 10
        assert job.failed_items == 1
        assert job.progress == 50  # (5/10) * 100
    
    @pytest.mark.unit
    def test_scraping_job_repr(self):
        """Test scraping job string representation."""
        job = ScrapingJob(
            user_id="user-id",
            job_type="web",
            title="Test Job",
            status=JobStatus.PENDING
        )
        
        repr_str = repr(job)
        assert "ScrapingJob" in repr_str
        assert "Test Job" in repr_str
        assert "pending" in repr_str


class TestJobConfigurationModel:
    """Test JobConfiguration model."""
    
    @pytest.mark.unit
    def test_job_configuration_creation(self):
        """Test job configuration creation."""
        config = JobConfiguration(
            job_id="job-id",
            config_key="max_depth",
            config_value="3"
        )
        
        assert config.job_id == "job-id"
        assert config.config_key == "max_depth"
        assert config.config_value == "3"
    
    @pytest.mark.unit
    def test_job_configuration_repr(self):
        """Test job configuration string representation."""
        config = JobConfiguration(
            job_id="job-id",
            config_key="max_depth",
            config_value="3"
        )
        
        repr_str = repr(config)
        assert "JobConfiguration" in repr_str
        assert "job-id" in repr_str
        assert "max_depth" in repr_str


class TestArtifactModel:
    """Test Artifact model."""
    
    @pytest.mark.unit
    def test_artifact_creation(self):
        """Test artifact creation."""
        artifact = Artifact(
            job_id="job-id",
            user_id="user-id",
            artifact_type=ArtifactType.WEB_PAGE,
            title="Test Artifact",
            description="Test description",
            source_url="https://example.com",
            content_hash="abc123",
            file_size=1024,
            mime_type="text/html",
            minio_path="artifacts/test.html",
            content_text="<html>Test content</html>",
            keywords=["test", "web"],
            tags=["sample", "test"],
            language="en",
            is_public=False
        )
        
        assert artifact.job_id == "job-id"
        assert artifact.user_id == "user-id"
        assert artifact.artifact_type == ArtifactType.WEB_PAGE
        assert artifact.title == "Test Artifact"
        assert artifact.description == "Test description"
        assert artifact.source_url == "https://example.com"
        assert artifact.content_hash == "abc123"
        assert artifact.file_size == 1024
        assert artifact.mime_type == "text/html"
        assert artifact.minio_path == "artifacts/test.html"
        assert artifact.content_text == "<html>Test content</html>"
        assert artifact.keywords == ["test", "web"]
        assert artifact.tags == ["sample", "test"]
        assert artifact.language == "en"
        assert artifact.is_public is False
    
    @pytest.mark.unit
    def test_artifact_file_size_formatted(self):
        """Test artifact file size formatting."""
        # Test bytes
        artifact = Artifact(
            job_id="job-id",
            user_id="user-id",
            artifact_type=ArtifactType.WEB_PAGE,
            title="Test",
            content_hash="abc123",
            minio_path="test.html",
            file_size=512
        )
        assert artifact.file_size_formatted == "512.0 B"
        
        # Test KB
        artifact.file_size = 2048
        assert artifact.file_size_formatted == "2.0 KB"
        
        # Test MB
        artifact.file_size = 2097152
        assert artifact.file_size_formatted == "2.0 MB"
        
        # Test GB
        artifact.file_size = 2147483648
        assert artifact.file_size_formatted == "2.0 GB"
    
    @pytest.mark.unit
    def test_artifact_has_content(self):
        """Test artifact content check."""
        # Has content text
        artifact1 = Artifact(
            job_id="job-id",
            user_id="user-id",
            artifact_type=ArtifactType.WEB_PAGE,
            title="Test",
            content_hash="abc123",
            minio_path="test.html",
            content_text="Some content"
        )
        assert artifact1.has_content is True
        
        # Has content summary
        artifact2 = Artifact(
            job_id="job-id",
            user_id="user-id",
            artifact_type=ArtifactType.WEB_PAGE,
            title="Test",
            content_hash="abc123",
            minio_path="test.html",
            content_summary="Some summary"
        )
        assert artifact2.has_content is True
        
        # No content
        artifact3 = Artifact(
            job_id="job-id",
            user_id="user-id",
            artifact_type=ArtifactType.WEB_PAGE,
            title="Test",
            content_hash="abc123",
            minio_path="test.html"
        )
        assert artifact3.has_content is False
    
    @pytest.mark.unit
    def test_artifact_repr(self):
        """Test artifact string representation."""
        artifact = Artifact(
            job_id="job-id",
            user_id="user-id",
            artifact_type=ArtifactType.WEB_PAGE,
            title="Test Artifact",
            content_hash="abc123",
            minio_path="test.html"
        )
        
        repr_str = repr(artifact)
        assert "Artifact" in repr_str
        assert "Test Artifact" in repr_str
        assert "web_page" in repr_str


class TestMetadataTagModel:
    """Test MetadataTag model."""
    
    @pytest.mark.unit
    def test_metadata_tag_creation(self):
        """Test metadata tag creation."""
        tag = MetadataTag(
            artifact_id="artifact-id",
            tag_type="category",
            tag_key="topic",
            tag_value="technology"
        )
        
        assert tag.artifact_id == "artifact-id"
        assert tag.tag_type == "category"
        assert tag.tag_key == "topic"
        assert tag.tag_value == "technology"
    
    @pytest.mark.unit
    def test_metadata_tag_repr(self):
        """Test metadata tag string representation."""
        tag = MetadataTag(
            artifact_id="artifact-id",
            tag_type="category",
            tag_key="topic",
            tag_value="technology"
        )
        
        repr_str = repr(tag)
        assert "MetadataTag" in repr_str
        assert "artifact-id" in repr_str
        assert "category" in repr_str
        assert "topic" in repr_str


class TestContentExtractionModel:
    """Test ContentExtraction model."""
    
    @pytest.mark.unit
    def test_content_extraction_creation(self):
        """Test content extraction creation."""
        extraction = ContentExtraction(
            artifact_id="artifact-id",
            extraction_type="text",
            extracted_data={"text": "Extracted text content"},
            confidence_score=0.95
        )
        
        assert extraction.artifact_id == "artifact-id"
        assert extraction.extraction_type == "text"
        assert extraction.extracted_data == {"text": "Extracted text content"}
        assert extraction.confidence_score == 0.95
    
    @pytest.mark.unit
    def test_content_extraction_repr(self):
        """Test content extraction string representation."""
        extraction = ContentExtraction(
            artifact_id="artifact-id",
            extraction_type="text",
            extracted_data={"text": "Extracted text content"}
        )
        
        repr_str = repr(extraction)
        assert "ContentExtraction" in repr_str
        assert "artifact-id" in repr_str
        assert "text" in repr_str


class TestSystemConfigModel:
    """Test SystemConfig model."""
    
    @pytest.mark.unit
    def test_system_config_creation(self):
        """Test system config creation."""
        config = SystemConfig(
            key="max_file_size",
            value="104857600",
            type="integer",
            description="Maximum file size in bytes",
            is_sensitive=False
        )
        
        assert config.key == "max_file_size"
        assert config.value == "104857600"
        assert config.type == "integer"
        assert config.description == "Maximum file size in bytes"
        assert config.is_sensitive is False
    
    @pytest.mark.unit
    def test_system_config_repr(self):
        """Test system config string representation."""
        config = SystemConfig(
            key="max_file_size",
            value="104857600"
        )
        
        repr_str = repr(config)
        assert "SystemConfig" in repr_str
        assert "max_file_size" in repr_str


class TestAPIRateLimitModel:
    """Test APIRateLimit model."""
    
    @pytest.mark.unit
    def test_api_rate_limit_creation(self):
        """Test API rate limit creation."""
        window_start = datetime.now(timezone.utc)
        rate_limit = APIRateLimit(
            user_id="user-id",
            endpoint="/api/jobs",
            request_count=5,
            window_start=window_start
        )
        
        assert rate_limit.user_id == "user-id"
        assert rate_limit.endpoint == "/api/jobs"
        assert rate_limit.request_count == 5
        assert rate_limit.window_start == window_start
    
    @pytest.mark.unit
    def test_api_rate_limit_repr(self):
        """Test API rate limit string representation."""
        rate_limit = APIRateLimit(
            user_id="user-id",
            endpoint="/api/jobs",
            request_count=5,
            window_start=datetime.now(timezone.utc)
        )
        
        repr_str = repr(rate_limit)
        assert "APIRateLimit" in repr_str
        assert "user-id" in repr_str
        assert "/api/jobs" in repr_str


class TestAuditLogModel:
    """Test AuditLog model."""
    
    @pytest.mark.unit
    def test_audit_log_creation(self):
        """Test audit log creation."""
        audit_log = AuditLog(
            user_id="user-id",
            action="create_job",
            resource_type="scraping_job",
            resource_id="job-id",
            details={"job_type": "web", "keywords": ["test"]},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        assert audit_log.user_id == "user-id"
        assert audit_log.action == "create_job"
        assert audit_log.resource_type == "scraping_job"
        assert audit_log.resource_id == "job-id"
        assert audit_log.details == {"job_type": "web", "keywords": ["test"]}
        assert audit_log.ip_address_str == "192.168.1.1"
        assert audit_log.user_agent == "Mozilla/5.0"
    
    @pytest.mark.unit
    def test_audit_log_ip_address_str(self):
        """Test audit log IP address string conversion."""
        audit_log = AuditLog(
            user_id="user-id",
            action="create_job",
            ip_address="192.168.1.1"
        )
        
        assert audit_log.ip_address_str == "192.168.1.1"
        
        # Test with None IP
        audit_log.ip_address = None
        assert audit_log.ip_address_str is None
    
    @pytest.mark.unit
    def test_audit_log_repr(self):
        """Test audit log string representation."""
        audit_log = AuditLog(
            user_id="user-id",
            action="create_job"
        )
        
        repr_str = repr(audit_log)
        assert "AuditLog" in repr_str
        assert "create_job" in repr_str
        assert "user-id" in repr_str


class TestAPIKeyModel:
    """Test APIKey model."""
    
    @pytest.mark.unit
    def test_api_key_creation(self):
        """Test API key creation."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        api_key = APIKey(
            user_id="user-id",
            key_name="Test API Key",
            key_hash="hashed_key",
            permissions=["read", "write"],
            is_active=True,
            expires_at=expires_at
        )
        
        assert api_key.user_id == "user-id"
        assert api_key.key_name == "Test API Key"
        assert api_key.key_hash == "hashed_key"
        assert api_key.permissions == ["read", "write"]
        assert api_key.is_active is True
        assert api_key.expires_at == expires_at
    
    @pytest.mark.unit
    def test_api_key_properties(self):
        """Test API key properties."""
        # Valid key
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        valid_key = APIKey(
            user_id="user-id",
            key_name="Valid Key",
            key_hash="hash",
            is_active=True,
            expires_at=expires_at
        )
        assert valid_key.is_expired is False
        assert valid_key.is_valid is True
        
        # Expired key
        expired_at = datetime.now(timezone.utc) - timedelta(days=1)
        expired_key = APIKey(
            user_id="user-id",
            key_name="Expired Key",
            key_hash="hash",
            is_active=True,
            expires_at=expired_at
        )
        assert expired_key.is_expired is True
        assert expired_key.is_valid is False
        
        # Inactive key
        inactive_key = APIKey(
            user_id="user-id",
            key_name="Inactive Key",
            key_hash="hash",
            is_active=False,
            expires_at=expires_at
        )
        assert inactive_key.is_valid is False
    
    @pytest.mark.unit
    def test_api_key_permissions(self):
        """Test API key permission checking."""
        api_key = APIKey(
            user_id="user-id",
            key_name="Test Key",
            key_hash="hash",
            permissions=["read", "write", "delete"]
        )
        
        assert api_key.has_permission("read") is True
        assert api_key.has_permission("write") is True
        assert api_key.has_permission("delete") is True
        assert api_key.has_permission("admin") is False
        
        # Test with no permissions
        api_key.permissions = None
        assert api_key.has_permission("read") is False
    
    @pytest.mark.unit
    def test_api_key_repr(self):
        """Test API key string representation."""
        api_key = APIKey(
            user_id="user-id",
            key_name="Test API Key",
            key_hash="hash"
        )
        
        repr_str = repr(api_key)
        assert "APIKey" in repr_str
        assert "Test API Key" in repr_str
        assert "user-id" in repr_str


class TestModelRelationships:
    """Test model relationships."""
    
    @pytest.mark.unit
    def test_user_relationships(self):
        """Test user model relationships."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hash"
        )
        
        # Test that relationships are defined
        assert hasattr(user, 'scraping_jobs')
        assert hasattr(user, 'artifacts')
        assert hasattr(user, 'api_keys')
        assert hasattr(user, 'user_sessions')
        assert hasattr(user, 'audit_logs')
        assert hasattr(user, 'api_rate_limits')
    
    @pytest.mark.unit
    def test_scraping_job_relationships(self):
        """Test scraping job model relationships."""
        job = ScrapingJob(
            user_id="user-id",
            job_type="web",
            title="Test Job"
        )
        
        # Test that relationships are defined
        assert hasattr(job, 'user')
        assert hasattr(job, 'artifacts')
        assert hasattr(job, 'job_configurations')
    
    @pytest.mark.unit
    def test_artifact_relationships(self):
        """Test artifact model relationships."""
        artifact = Artifact(
            job_id="job-id",
            user_id="user-id",
            artifact_type=ArtifactType.WEB_PAGE,
            title="Test Artifact",
            content_hash="abc123",
            minio_path="test.html"
        )
        
        # Test that relationships are defined
        assert hasattr(artifact, 'job')
        assert hasattr(artifact, 'user')
        assert hasattr(artifact, 'metadata_tags')
        assert hasattr(artifact, 'content_extractions')
