"""
Tests for performance optimization functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.services.performance_service import PerformanceService
from src.core.models.monitoring import PerformanceMetrics


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
    redis_client.info.return_value = {
        "connected_clients": 5,
        "used_memory_human": "1.2MB",
        "keyspace_hits": 1000,
        "keyspace_misses": 100
    }
    redis_client.dbsize.return_value = 50
    return redis_client


@pytest.fixture
def performance_service(mock_db, mock_redis):
    """Create performance service with mocked dependencies."""
    return PerformanceService(mock_db, mock_redis)


class TestPerformanceService:
    """Test cases for PerformanceService."""
    
    async def test_optimize_database_queries_success(self, performance_service):
        """Test successful database optimization."""
        mock_row = MagicMock()
        mock_row.query_text = "SELECT * FROM users WHERE id = ?"
        mock_row.avg_time = 1500.5
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        performance_service.db.execute.return_value = mock_result
        
        result = await performance_service.optimize_database_queries()
        
        assert result["status"] == "optimized"
        assert len(result["slow_queries"]) == 1
        assert result["slow_queries"][0]["query_text"] == "SELECT * FROM users WHERE id = ?"
        assert result["slow_queries"][0]["avg_time"] == 1500.5
    
    async def test_optimize_database_queries_error(self, performance_service):
        """Test database optimization with error."""
        performance_service.db.execute.side_effect = Exception("Database error")
        
        result = await performance_service.optimize_database_queries()
        
        assert "error" in result
        assert "Database error" in result["error"]
    
    async def test_implement_caching_strategy_success(self, performance_service):
        """Test successful caching strategy implementation."""
        result = await performance_service.implement_caching_strategy()
        
        assert result["cache_implemented"] is True
        assert "cache_stats" in result
        assert result["cache_stats"]["connected_clients"] == 5
        assert result["cache_stats"]["used_memory_human"] == "1.2MB"
        assert result["cache_stats"]["total_keys"] == 50
    
    async def test_implement_caching_strategy_error(self, performance_service):
        """Test caching strategy with Redis error."""
        performance_service.redis.info.side_effect = Exception("Redis error")
        
        result = await performance_service.implement_caching_strategy()
        
        assert "error" in result
        assert "Redis error" in result["error"]
    
    async def test_monitor_performance_success(self, performance_service):
        """Test successful performance monitoring."""
        mock_db_row = MagicMock()
        mock_db_row.total_queries = 100
        mock_db_row.avg_time = 250.5
        
        mock_db_result = MagicMock()
        mock_db_result.fetchone.return_value = mock_db_row
        performance_service.db.execute.return_value = mock_db_result
        
        result = await performance_service.monitor_performance()
        
        assert "database" in result
        assert "cache" in result
        assert result["database"]["total_queries"] == 100
        assert result["database"]["avg_query_time"] == 250.5
        assert result["cache"]["connected_clients"] == 5
    
    async def test_monitor_performance_error(self, performance_service):
        """Test performance monitoring with error."""
        performance_service.db.execute.side_effect = Exception("Monitoring error")
        
        result = await performance_service.monitor_performance()
        
        assert "error" in result
        assert "Monitoring error" in result["error"]
    
    async def test_get_slow_queries(self, performance_service):
        """Test getting slow queries."""
        mock_row1 = MagicMock()
        mock_row1.query_text = "SELECT * FROM artifacts WHERE user_id = ?"
        mock_row1.avg_time = 2000.0
        
        mock_row2 = MagicMock()
        mock_row2.query_text = "SELECT * FROM scraping_jobs WHERE status = ?"
        mock_row2.avg_time = 1500.0
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row1, mock_row2]
        performance_service.db.execute.return_value = mock_result
        
        slow_queries = await performance_service._get_slow_queries()
        
        assert len(slow_queries) == 2
        assert slow_queries[0]["query_text"] == "SELECT * FROM artifacts WHERE user_id = ?"
        assert slow_queries[0]["avg_time"] == 2000.0
        assert slow_queries[1]["query_text"] == "SELECT * FROM scraping_jobs WHERE status = ?"
        assert slow_queries[1]["avg_time"] == 1500.0
    
    async def test_get_cache_statistics_success(self, performance_service):
        """Test getting cache statistics successfully."""
        stats = await performance_service._get_cache_statistics()
        
        assert stats["connected_clients"] == 5
        assert stats["used_memory_human"] == "1.2MB"
        assert stats["total_keys"] == 50
    
    async def test_get_cache_statistics_error(self, performance_service):
        """Test getting cache statistics with error."""
        performance_service.redis.info.side_effect = Exception("Redis info error")
        
        stats = await performance_service._get_cache_statistics()
        
        assert stats == {}
    
    async def test_monitor_database_performance(self, performance_service):
        """Test monitoring database performance."""
        mock_row = MagicMock()
        mock_row.total_queries = 500
        mock_row.avg_time = 300.75
        
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        performance_service.db.execute.return_value = mock_result
        
        db_performance = await performance_service._monitor_database_performance()
        
        assert db_performance["total_queries"] == 500
        assert db_performance["avg_query_time"] == 300.75


class TestPerformanceModels:
    """Test cases for performance-related models."""
    
    def test_performance_metrics_model(self):
        """Test PerformanceMetrics model creation."""
        user_id = uuid4()
        metric = PerformanceMetrics(
            metric_type="database_query",
            processing_time_ms=150.5,
            query_text="SELECT * FROM users",
            user_id=user_id
        )
        
        assert metric.metric_type == "database_query"
        assert metric.processing_time_ms == 150.5
        assert metric.query_text == "SELECT * FROM users"
        assert metric.user_id == user_id


class TestPerformanceIntegration:
    """Integration tests for performance functionality."""
    
    @pytest.mark.asyncio
    async def test_full_performance_workflow(self, performance_service):
        """Test complete performance optimization workflow."""
        # Mock database responses
        mock_slow_query_row = MagicMock()
        mock_slow_query_row.query_text = "SELECT * FROM large_table"
        mock_slow_query_row.avg_time = 3000.0
        
        mock_slow_result = MagicMock()
        mock_slow_result.fetchall.return_value = [mock_slow_query_row]
        
        mock_db_row = MagicMock()
        mock_db_row.total_queries = 1000
        mock_db_row.avg_time = 500.0
        
        mock_db_result = MagicMock()
        mock_db_result.fetchone.return_value = mock_db_row
        
        performance_service.db.execute.side_effect = [mock_slow_result, mock_db_result]
        
        # Test database optimization
        db_result = await performance_service.optimize_database_queries()
        assert db_result["status"] == "optimized"
        assert len(db_result["slow_queries"]) == 1
        
        # Test caching strategy
        cache_result = await performance_service.implement_caching_strategy()
        assert cache_result["cache_implemented"] is True
        
        # Test performance monitoring
        monitor_result = await performance_service.monitor_performance()
        assert "database" in monitor_result
        assert "cache" in monitor_result
        assert monitor_result["database"]["total_queries"] == 1000
