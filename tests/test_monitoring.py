"""
Tests for monitoring functionality.

This module contains tests for system health checks, analytics,
performance monitoring, and alerts.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.core.models.monitoring import (
    Alert, HealthStatus, PerformanceMetrics, ScrapingMetrics,
    ServiceType, SystemHealth, UserActivity
)
from src.services.monitoring_service import MonitoringService
from src.core.models import User, ScrapingJob


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def mock_minio_client():
    """Mock MinIO client."""
    client = AsyncMock()
    client.list_buckets = AsyncMock(return_value=["bucket1", "bucket2"])
    return client


@pytest.fixture
def monitoring_service(mock_db, mock_minio_client):
    """Create monitoring service with mocked dependencies."""
    return MonitoringService(mock_db, mock_minio_client)


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        role="ADMIN"
    )


@pytest.fixture
def sample_job():
    """Create a sample scraping job for testing."""
    return ScrapingJob(
        id=uuid4(),
        user_id=uuid4(),
        job_type="web",
        status="completed"
    )


class TestMonitoringService:
    """Test cases for MonitoringService."""
    
    async def test_check_database_health_success(self, monitoring_service, mock_db):
        """Test successful database health check."""
        # Mock successful database query
        mock_result = MagicMock()
        mock_result.scalar.return_value = 10
        mock_db.execute.return_value = mock_result
        
        health = await monitoring_service._check_database_health()
        
        assert health["status"] == HealthStatus.HEALTHY
        assert "response_time_ms" in health
        assert health["details"]["user_count"] == 10
    
    async def test_check_database_health_failure(self, monitoring_service, mock_db):
        """Test database health check failure."""
        # Mock database error
        mock_db.execute.side_effect = Exception("Database connection failed")
        
        health = await monitoring_service._check_database_health()
        
        assert health["status"] == HealthStatus.UNHEALTHY
        assert "response_time_ms" in health
        assert "error_message" in health
    
    async def test_check_minio_health_success(self, monitoring_service, mock_minio_client):
        """Test successful MinIO health check."""
        health = await monitoring_service._check_minio_health()
        
        assert health["status"] == HealthStatus.HEALTHY
        assert "response_time_ms" in health
        assert health["details"]["bucket_count"] == 2
    
    async def test_check_minio_health_failure(self, monitoring_service, mock_minio_client):
        """Test MinIO health check failure."""
        # Mock MinIO error
        mock_minio_client.list_buckets.side_effect = Exception("MinIO connection failed")
        
        health = await monitoring_service._check_minio_health()
        
        assert health["status"] == HealthStatus.UNHEALTHY
        assert "response_time_ms" in health
        assert "error_message" in health
    
    async def test_check_system_health(self, monitoring_service, mock_db):
        """Test comprehensive system health check."""
        # Mock successful database query
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db.execute.return_value = mock_result
        
        health_results = await monitoring_service.check_system_health()
        
        assert "database" in health_results
        assert "minio" in health_results
        assert "redis" in health_results
        assert mock_db.commit.called
    
    async def test_record_scraping_metrics(self, monitoring_service, mock_db, sample_job):
        """Test recording scraping metrics."""
        await monitoring_service.record_scraping_metrics(
            job_id=sample_job.id,
            scraper_type="web",
            success=True,
            duration_ms=1500.0,
            items_processed=10,
            items_failed=0
        )
        
        # Verify metrics were added to database
        assert mock_db.add.called
        assert mock_db.commit.called
        
        # Get the added metrics object
        added_metrics = mock_db.add.call_args[0][0]
        assert isinstance(added_metrics, ScrapingMetrics)
        assert added_metrics.job_id == sample_job.id
        assert added_metrics.scraper_type == "web"
        assert added_metrics.success is True
        assert added_metrics.duration_ms == 1500.0
        assert added_metrics.items_processed == 10
        assert added_metrics.items_failed == 0
    
    async def test_record_user_activity(self, monitoring_service, mock_db, sample_user):
        """Test recording user activity."""
        await monitoring_service.record_user_activity(
            user_id=sample_user.id,
            activity_type="login",
            endpoint="/api/v1/auth/login",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            session_id="session123"
        )
        
        # Verify activity was added to database
        assert mock_db.add.called
        assert mock_db.commit.called
        
        # Get the added activity object
        added_activity = mock_db.add.call_args[0][0]
        assert isinstance(added_activity, UserActivity)
        assert added_activity.user_id == sample_user.id
        assert added_activity.activity_type == "login"
        assert added_activity.endpoint == "/api/v1/auth/login"
        assert added_activity.ip_address == "192.168.1.1"
    
    async def test_record_performance_metric(self, monitoring_service, mock_db):
        """Test recording performance metric."""
        await monitoring_service.record_performance_metric(
            metric_name="api_response_time",
            metric_type="histogram",
            value=150.5,
            unit="ms",
            labels={"endpoint": "/api/v1/jobs"}
        )
        
        # Verify metric was added to database
        assert mock_db.add.called
        assert mock_db.commit.called
        
        # Get the added metric object
        added_metric = mock_db.add.call_args[0][0]
        assert isinstance(added_metric, PerformanceMetrics)
        assert added_metric.metric_name == "api_response_time"
        assert added_metric.metric_type == "histogram"
        assert added_metric.value == 150.5
        assert added_metric.unit == "ms"
    
    async def test_get_scraping_analytics(self, monitoring_service, mock_db):
        """Test getting scraping analytics."""
        # Mock scraping metrics data
        mock_metrics = [
            ScrapingMetrics(
                id=uuid4(),
                job_id=uuid4(),
                scraper_type="web",
                success=True,
                duration_ms=1000.0,
                items_processed=5,
                items_failed=0
            ),
            ScrapingMetrics(
                id=uuid4(),
                job_id=uuid4(),
                scraper_type="web",
                success=False,
                duration_ms=2000.0,
                items_processed=0,
                items_failed=1
            )
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_metrics
        mock_db.execute.return_value = mock_result
        
        analytics = await monitoring_service.get_scraping_analytics(days=7)
        
        assert analytics["period_days"] == 7
        assert analytics["total_jobs"] == 2
        assert analytics["successful_jobs"] == 1
        assert analytics["failed_jobs"] == 1
        assert analytics["success_rate"] == 50.0
        assert analytics["average_duration_ms"] == 1500.0
        assert analytics["total_items_processed"] == 5
        assert analytics["total_items_failed"] == 1
    
    async def test_get_user_activity_analytics(self, monitoring_service, mock_db, sample_user):
        """Test getting user activity analytics."""
        # Mock user activity data
        mock_activities = [
            UserActivity(
                id=uuid4(),
                user_id=sample_user.id,
                activity_type="login",
                endpoint="/api/v1/auth/login"
            ),
            UserActivity(
                id=uuid4(),
                user_id=sample_user.id,
                activity_type="api_call",
                endpoint="/api/v1/jobs"
            ),
            UserActivity(
                id=uuid4(),
                user_id=sample_user.id,
                activity_type="logout",
                endpoint="/api/v1/auth/logout"
            )
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_activities
        mock_db.execute.return_value = mock_result
        
        analytics = await monitoring_service.get_user_activity_analytics(days=7)
        
        assert analytics["period_days"] == 7
        assert analytics["total_activities"] == 3
        assert analytics["activity_types"]["login"] == 1
        assert analytics["activity_types"]["api_call"] == 1
        assert analytics["activity_types"]["logout"] == 1
        assert len(analytics["top_endpoints"]) == 3
    
    async def test_create_alert(self, monitoring_service, mock_db):
        """Test creating a system alert."""
        alert = await monitoring_service.create_alert(
            alert_type="error",
            severity="high",
            title="Database Connection Failed",
            message="Unable to connect to database",
            source="monitoring_service",
            details={"retry_count": 3}
        )
        
        assert isinstance(alert, Alert)
        assert alert.alert_type == "error"
        assert alert.severity == "high"
        assert alert.title == "Database Connection Failed"
        assert alert.message == "Unable to connect to database"
        assert alert.source == "monitoring_service"
        assert alert.resolved is False
        assert mock_db.commit.called
        assert mock_db.refresh.called
    
    async def test_get_active_alerts(self, monitoring_service, mock_db):
        """Test getting active alerts."""
        # Mock active alerts data
        mock_alerts = [
            Alert(
                id=uuid4(),
                alert_type="warning",
                severity="medium",
                title="High Memory Usage",
                message="Memory usage is above 80%",
                source="system_monitor",
                resolved=False
            )
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_alerts
        mock_db.execute.return_value = mock_result
        
        alerts = await monitoring_service.get_active_alerts()
        
        assert len(alerts) == 1
        assert alerts[0].alert_type == "warning"
        assert alerts[0].resolved is False
    
    async def test_resolve_alert(self, monitoring_service, mock_db, sample_user):
        """Test resolving an alert."""
        alert_id = uuid4()
        mock_alert = Alert(
            id=alert_id,
            alert_type="error",
            severity="high",
            title="Test Alert",
            message="Test message",
            source="test",
            resolved=False
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_alert
        mock_db.execute.return_value = mock_result
        
        resolved_alert = await monitoring_service.resolve_alert(alert_id, sample_user.id)
        
        assert resolved_alert.resolved is True
        assert resolved_alert.resolved_at is not None
        assert resolved_alert.resolved_by == sample_user.id
        assert mock_db.commit.called
        assert mock_db.refresh.called


class TestMonitoringModels:
    """Test cases for monitoring models."""
    
    def test_health_status_enum(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNHEALTHY == "unhealthy"
        assert HealthStatus.UNKNOWN == "unknown"
    
    def test_service_type_enum(self):
        """Test ServiceType enum values."""
        assert ServiceType.DATABASE == "database"
        assert ServiceType.MINIO == "minio"
        assert ServiceType.REDIS == "redis"
        assert ServiceType.API == "api"
        assert ServiceType.SCRAPER == "scraper"
        assert ServiceType.CELERY == "celery"
    
    def test_system_health_model(self):
        """Test SystemHealth model creation."""
        health = SystemHealth(
            service_type=ServiceType.DATABASE,
            status=HealthStatus.HEALTHY,
            response_time_ms=100.5,
            error_message=None,
            details='{"user_count": 10}'
        )
        
        assert health.service_type == ServiceType.DATABASE
        assert health.status == HealthStatus.HEALTHY
        assert health.response_time_ms == 100.5
        assert health.error_message is None
        assert health.details == '{"user_count": 10}'
    
    def test_scraping_metrics_model(self):
        """Test ScrapingMetrics model creation."""
        job_id = uuid4()
        metrics = ScrapingMetrics(
            job_id=job_id,
            scraper_type="web",
            success=True,
            duration_ms=1500.0,
            items_processed=10,
            items_failed=0,
            error_message=None
        )
        
        assert metrics.job_id == job_id
        assert metrics.scraper_type == "web"
        assert metrics.success is True
        assert metrics.duration_ms == 1500.0
        assert metrics.items_processed == 10
        assert metrics.items_failed == 0
    
    def test_user_activity_model(self):
        """Test UserActivity model creation."""
        user_id = uuid4()
        activity = UserActivity(
            user_id=user_id,
            activity_type="login",
            endpoint="/api/v1/auth/login",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            session_id="session123"
        )
        
        assert activity.user_id == user_id
        assert activity.activity_type == "login"
        assert activity.endpoint == "/api/v1/auth/login"
        assert activity.ip_address == "192.168.1.1"
        assert activity.user_agent == "Mozilla/5.0"
        assert activity.session_id == "session123"
    
    def test_performance_metrics_model(self):
        """Test PerformanceMetrics model creation."""
        metric = PerformanceMetrics(
            metric_name="api_response_time",
            metric_type="histogram",
            value=150.5,
            unit="ms",
            labels='{"endpoint": "/api/v1/jobs"}'
        )
        
        assert metric.metric_name == "api_response_time"
        assert metric.metric_type == "histogram"
        assert metric.value == 150.5
        assert metric.unit == "ms"
        assert metric.labels == '{"endpoint": "/api/v1/jobs"}'
    
    def test_alert_model(self):
        """Test Alert model creation."""
        alert = Alert(
            alert_type="error",
            severity="high",
            title="Database Connection Failed",
            message="Unable to connect to database",
            source="monitoring_service",
            resolved=False
        )
        
        assert alert.alert_type == "error"
        assert alert.severity == "high"
        assert alert.title == "Database Connection Failed"
        assert alert.message == "Unable to connect to database"
        assert alert.source == "monitoring_service"
        assert alert.resolved is False
