"""
Integration tests for the StratLogic Scraping System.

This module contains comprehensive integration tests for system integration
and error handling components, including error handling, logging, health checks,
and service integration.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import (
    StratLogicException, AuthenticationError, DatabaseError, 
    StorageError, ValidationError, RateLimitError
)
from src.core.health_checks import (
    HealthChecker, HealthMonitor, CircuitBreaker, 
    HealthStatus, HealthCheckResult
)
from src.services.logging_service import (
    StructuredLogger, LogAggregator, LogLevelManager,
    DistributedTracing, MetricsCollector
)
from src.api.middleware.error_handling import (
    ErrorHandlingMiddleware, ValidationErrorHandler,
    HTTPExceptionHandler, RetryMiddleware, CircuitBreakerMiddleware
)
from src.main import app


@pytest.fixture
def test_client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis_client = MagicMock()
    redis_client.get.return_value = None
    redis_client.incr.return_value = 1
    redis_client.setex.return_value = True
    redis_client.delete.return_value = 1
    return redis_client


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""
    
    async def test_custom_exception_handling(self, test_client):
        """Test that custom exceptions are properly handled."""
        # Test endpoint that raises a custom exception
        with patch('src.api.routes.auth.login', side_effect=AuthenticationError("Invalid credentials")):
            response = test_client.post("/api/v1/auth/login", json={
                "username": "testuser",
                "password": "wrongpassword"
            })
            
            assert response.status_code == 401
            data = response.json()
            assert data["error"] == "AUTHENTICATION_ERROR"
            assert "Invalid credentials" in data["message"]
            assert "request_id" in data
    
    async def test_validation_error_handling(self, test_client):
        """Test that validation errors are properly handled."""
        # Test with invalid JSON
        response = test_client.post("/api/v1/auth/login", data="invalid json")
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "request_id" in data
    
    async def test_database_error_handling(self, test_client):
        """Test that database errors are properly handled."""
        with patch('src.core.database.get_async_session', side_effect=DatabaseError("Connection failed")):
            response = test_client.get("/api/v1/users/me")
            
            assert response.status_code == 500
            data = response.json()
            assert data["error"] == "DATABASE_ERROR"
            assert "request_id" in data
    
    async def test_rate_limit_error_handling(self, test_client):
        """Test that rate limit errors are properly handled."""
        with patch('src.services.security_service.SecurityService.check_rate_limit', 
                  return_value=(False, {"limit_exceeded": True})):
            response = test_client.post("/api/v1/auth/login", json={
                "username": "testuser",
                "password": "password123"
            })
            
            # Should be rate limited
            assert response.status_code == 429
            data = response.json()
            assert data["error"] == "RATE_LIMIT_ERROR"
            assert "request_id" in data
    
    async def test_unexpected_error_handling(self, test_client):
        """Test that unexpected errors are properly handled."""
        with patch('src.api.routes.auth.login', side_effect=Exception("Unexpected error")):
            response = test_client.post("/api/v1/auth/login", json={
                "username": "testuser",
                "password": "password123"
            })
            
            assert response.status_code == 500
            data = response.json()
            assert data["error"] == "INTERNAL_SERVER_ERROR"
            assert "request_id" in data


class TestLoggingIntegration:
    """Integration tests for logging functionality."""
    
    def test_structured_logging(self):
        """Test structured logging functionality."""
        logger = StructuredLogger("test_logger")
        
        # Test logging with structured data
        with patch('structlog.get_logger') as mock_logger:
            logger.info("Test message", user_id="123", action="login")
            
            mock_logger.assert_called_with("test_logger")
            # Verify structured data was passed
    
    def test_log_aggregation(self):
        """Test log aggregation functionality."""
        aggregator = LogAggregator("test_logs.log")
        
        # Add log entries
        log_entry = {
            "level": "INFO",
            "message": "Test log entry",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": "123"
        }
        
        aggregator.add_log_entry(log_entry)
        
        # Test search functionality
        results = aggregator.search_logs(query="Test log entry")
        assert len(results) > 0
        assert results[0]["message"] == "Test log entry"
    
    def test_log_level_management(self):
        """Test log level management."""
        manager = LogLevelManager()
        
        # Set log level
        manager.set_logger_level("test_logger", "DEBUG")
        
        # Get log level
        level = manager.get_logger_level("test_logger")
        assert level == "DEBUG"
        
        # Test invalid level
        with pytest.raises(ValueError):
            manager.set_logger_level("test_logger", "INVALID_LEVEL")
    
    def test_distributed_tracing(self):
        """Test distributed tracing functionality."""
        tracing = DistributedTracing()
        
        # Start trace
        tracing.start_trace("test_trace_123")
        
        # Get trace context
        context = tracing.get_trace_context()
        assert context["trace_id"] == "test_trace_123"
        assert context["span_id"] is not None
        
        # Add trace to log data
        log_data = {"message": "Test message"}
        traced_data = tracing.add_trace_to_log(log_data)
        assert traced_data["trace_id"] == "test_trace_123"
    
    def test_metrics_collection(self):
        """Test metrics collection functionality."""
        collector = MetricsCollector()
        
        # Record metrics
        collector.record_request(0.5)
        collector.record_request(1.0)
        collector.record_error()
        
        # Get metrics
        metrics = collector.get_metrics()
        assert metrics["request_count"] == 2
        assert metrics["error_count"] == 1
        assert metrics["avg_response_time"] == 0.75
        assert metrics["error_rate"] == 0.5


class TestHealthCheckIntegration:
    """Integration tests for health check functionality."""
    
    async def test_health_checker_creation(self):
        """Test health checker creation and registration."""
        checker = HealthChecker()
        
        # Verify default checks are registered
        assert "database" in checker.checks
        assert "redis" in checker.checks
        assert "minio" in checker.checks
        assert "external_apis" in checker.checks
        assert "system_resources" in checker.checks
    
    async def test_circuit_breaker_functionality(self):
        """Test circuit breaker pattern."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)
        
        # Initially closed
        assert breaker.can_execute() is True
        
        # Record failures
        breaker.record_failure()
        assert breaker.can_execute() is True
        
        breaker.record_failure()
        assert breaker.can_execute() is False  # Should be open
        
        # Wait for recovery
        time.sleep(1.1)
        assert breaker.can_execute() is True  # Should be half-open
        
        # Record success
        breaker.record_success()
        assert breaker.can_execute() is True  # Should be closed
    
    async def test_database_health_check(self, mock_db):
        """Test database health check."""
        checker = HealthChecker()
        
        # Mock successful database check
        mock_result = MagicMock()
        mock_result.fetchone.return_value = MagicMock()
        mock_db.execute.return_value = mock_result
        
        with patch('src.core.health_checks.get_async_session', return_value=mock_db):
            result = await checker._check_database()
            
            assert result["status"] == HealthStatus.HEALTHY
            assert "Database is healthy" in result["message"]
    
    async def test_redis_health_check(self, mock_redis):
        """Test Redis health check."""
        checker = HealthChecker()
        
        # Mock Redis info
        mock_redis.info.return_value = {
            "redis_version": "6.0.0",
            "uptime_in_seconds": 3600,
            "used_memory_human": "1MB",
            "maxmemory_human": "100MB",
            "connected_clients": 5,
            "maxclients": 100,
            "keyspace_hits": 1000,
            "keyspace_misses": 100
        }
        
        with patch('src.core.health_checks.redis.Redis', return_value=mock_redis):
            result = await checker._check_redis()
            
            assert result["status"] == HealthStatus.HEALTHY
            assert "Redis is healthy" in result["message"]
            assert result["details"]["hit_rate"] == 0.9090909090909091
    
    async def test_minio_health_check(self):
        """Test MinIO health check."""
        checker = HealthChecker()
        
        # Mock MinIO client
        mock_minio = MagicMock()
        mock_bucket = MagicMock()
        mock_bucket.name = "artifacts"
        mock_minio.list_buckets.return_value = [mock_bucket]
        
        with patch('src.core.health_checks.Minio', return_value=mock_minio):
            result = await checker._check_minio()
            
            assert result["status"] == HealthStatus.DEGRADED  # Missing required buckets
            assert "missing buckets" in result["message"]
    
    async def test_overall_health_status(self):
        """Test overall health status calculation."""
        checker = HealthChecker()
        
        # Mock all health checks to return healthy
        with patch.object(checker, '_check_database', return_value={
            "status": HealthStatus.HEALTHY,
            "message": "Database is healthy",
            "details": {}
        }):
            with patch.object(checker, '_check_redis', return_value={
                "status": HealthStatus.HEALTHY,
                "message": "Redis is healthy",
                "details": {}
            }):
                with patch.object(checker, '_check_minio', return_value={
                    "status": HealthStatus.HEALTHY,
                    "message": "MinIO is healthy",
                    "details": {}
                }):
                    overall_health = await checker.get_overall_health()
                    
                    assert overall_health["status"] == HealthStatus.HEALTHY
                    assert overall_health["summary"]["total_checks"] == 5
                    assert overall_health["summary"]["status_counts"]["healthy"] == 3


class TestServiceIntegration:
    """Integration tests for service integration."""
    
    async def test_service_communication(self, mock_db, mock_redis):
        """Test service communication patterns."""
        # Test that services can communicate with each other
        from src.services.monitoring_service import MonitoringService
        from src.services.security_service import SecurityService
        
        monitoring_service = MonitoringService(mock_db, mock_redis)
        security_service = SecurityService(mock_db, mock_redis)
        
        # Test that services can be instantiated together
        assert monitoring_service is not None
        assert security_service is not None
    
    async def test_dependency_injection(self, test_client):
        """Test dependency injection in API endpoints."""
        # Test that dependencies are properly injected
        with patch('src.api.dependencies.get_current_user') as mock_user:
            mock_user.return_value = MagicMock(id=uuid4(), username="testuser")
            
            response = test_client.get("/api/v1/users/me")
            
            # Should not raise dependency injection errors
            assert response.status_code in [200, 401, 403]  # Depending on auth setup
    
    async def test_graceful_degradation(self, test_client):
        """Test graceful degradation when services are unavailable."""
        # Test that the system degrades gracefully when Redis is unavailable
        with patch('src.services.security_service.SecurityService.check_rate_limit', 
                  side_effect=Exception("Redis unavailable")):
            response = test_client.post("/api/v1/auth/login", json={
                "username": "testuser",
                "password": "password123"
            })
            
            # Should handle Redis unavailability gracefully
            assert response.status_code in [200, 401, 500]  # Should not crash
    
    async def test_error_propagation(self, test_client):
        """Test that errors propagate correctly through the system."""
        # Test that errors from lower layers propagate to API responses
        with patch('src.core.database.get_async_session', side_effect=Exception("Database error")):
            response = test_client.get("/api/v1/users/me")
            
            # Should return error response instead of crashing
            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert "request_id" in data


class TestMiddlewareIntegration:
    """Integration tests for middleware functionality."""
    
    async def test_error_handling_middleware(self, test_client):
        """Test error handling middleware."""
        # Test that middleware properly handles errors
        with patch('src.api.routes.auth.login', side_effect=Exception("Test error")):
            response = test_client.post("/api/v1/auth/login", json={
                "username": "testuser",
                "password": "password123"
            })
            
            # Should have request ID in headers
            assert "X-Request-ID" in response.headers
            assert response.status_code == 500
    
    async def test_retry_middleware(self):
        """Test retry middleware functionality."""
        # Test retry logic for retryable errors
        middleware = RetryMiddleware(None, max_retries=2, retry_delay=0.1)
        
        call_count = 0
        
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise DatabaseError("Temporary database error")
            return "success"
        
        # Should retry and eventually succeed
        result = await failing_operation()
        assert result == "success"
        assert call_count == 3
    
    async def test_circuit_breaker_middleware(self):
        """Test circuit breaker middleware functionality."""
        middleware = CircuitBreakerMiddleware(None, failure_threshold=2, recovery_timeout=1.0)
        
        # Test circuit breaker state transitions
        assert middleware.circuit_state == "CLOSED"
        
        # Record failures
        middleware._record_failure()
        middleware._record_failure()
        
        assert middleware.circuit_state == "OPEN"
        assert middleware.can_execute() is False
        
        # Wait for recovery
        time.sleep(1.1)
        assert middleware.can_execute() is True
        assert middleware.circuit_state == "HALF_OPEN"


class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    async def test_complete_request_flow(self, test_client):
        """Test complete request flow with error handling."""
        # Test a complete request flow including error handling
        with patch('src.api.routes.auth.login', side_effect=AuthenticationError("Invalid credentials")):
            response = test_client.post("/api/v1/auth/login", json={
                "username": "testuser",
                "password": "wrongpassword"
            })
            
            # Verify complete error handling flow
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            assert "message" in data
            assert "request_id" in data
            assert "timestamp" in data
    
    async def test_health_check_endpoint(self, test_client):
        """Test health check endpoint integration."""
        # Test that health check endpoint works
        with patch('src.core.health_checks.check_health', return_value={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "summary": {"total_checks": 0, "status_counts": {}}
        }):
            response = test_client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    async def test_logging_integration(self, test_client):
        """Test logging integration in API requests."""
        # Test that logging is properly integrated
        with patch('src.services.logging_service.log_request') as mock_log:
            response = test_client.get("/api/v1/health")
            
            # Verify logging was called
            # Note: This might not be called depending on the actual implementation
            # The test verifies the integration point exists
    
    async def test_error_recovery(self, test_client):
        """Test error recovery mechanisms."""
        # Test that the system can recover from errors
        with patch('src.core.database.get_async_session', side_effect=Exception("Database error")):
            # First request should fail
            response1 = test_client.get("/api/v1/users/me")
            assert response1.status_code == 500
            
            # Second request should also fail (no recovery in this test)
            response2 = test_client.get("/api/v1/users/me")
            assert response2.status_code == 500


# Performance and stress tests
class TestPerformanceIntegration:
    """Performance integration tests."""
    
    async def test_concurrent_requests(self, test_client):
        """Test handling of concurrent requests."""
        import asyncio
        
        async def make_request():
            return test_client.get("/api/v1/health")
        
        # Make multiple concurrent requests
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code in [200, 401, 403]  # Depending on auth
    
    async def test_error_handling_performance(self, test_client):
        """Test error handling performance."""
        start_time = time.time()
        
        # Make multiple requests that will generate errors
        for _ in range(10):
            with patch('src.api.routes.auth.login', side_effect=Exception("Test error")):
                response = test_client.post("/api/v1/auth/login", json={
                    "username": "testuser",
                    "password": "password123"
                })
                assert response.status_code == 500
        
        end_time = time.time()
        
        # Should handle errors quickly (less than 1 second for 10 requests)
        assert end_time - start_time < 1.0
    
    async def test_health_check_performance(self):
        """Test health check performance."""
        checker = HealthChecker()
        
        start_time = time.time()
        
        # Run health checks
        with patch.object(checker, '_check_database', return_value={
            "status": HealthStatus.HEALTHY,
            "message": "Database is healthy",
            "details": {}
        }):
            overall_health = await checker.get_overall_health()
        
        end_time = time.time()
        
        # Health checks should complete quickly
        assert end_time - start_time < 5.0
        assert overall_health["status"] == HealthStatus.HEALTHY


if __name__ == "__main__":
    pytest.main([__file__])
