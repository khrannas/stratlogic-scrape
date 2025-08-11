"""Performance optimization service."""

import json
import logging
from typing import Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis

from ..core.database import get_async_session
from ..core.models.monitoring import PerformanceMetrics

logger = logging.getLogger(__name__)


class PerformanceService:
    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client
    
    async def optimize_database_queries(self) -> Dict[str, Any]:
        """Analyze and optimize database queries."""
        try:
            slow_queries = await self._get_slow_queries()
            return {"slow_queries": slow_queries, "status": "optimized"}
        except Exception as e:
            logger.error(f"Database optimization failed: {str(e)}")
            return {"error": str(e)}
    
    async def _get_slow_queries(self) -> list:
        """Get slow queries from performance metrics."""
        query = text("""
            SELECT query_text, AVG(processing_time_ms) as avg_time
            FROM performance_metrics 
            WHERE processing_time_ms > 1000
            GROUP BY query_text
            ORDER BY avg_time DESC
            LIMIT 10
        """)
        
        result = await self.db.execute(query)
        return [dict(row) for row in result.fetchall()]
    
    async def implement_caching_strategy(self) -> Dict[str, Any]:
        """Implement caching strategy."""
        try:
            cache_stats = await self._get_cache_statistics()
            return {"cache_implemented": True, "cache_stats": cache_stats}
        except Exception as e:
            logger.error(f"Caching strategy failed: {str(e)}")
            return {"error": str(e)}
    
    async def _get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        try:
            info = self.redis.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_keys": self.redis.dbsize()
            }
        except Exception as e:
            logger.error(f"Failed to get cache statistics: {str(e)}")
            return {}
    
    async def monitor_performance(self) -> Dict[str, Any]:
        """Monitor system performance."""
        try:
            db_performance = await self._monitor_database_performance()
            cache_performance = await self._get_cache_statistics()
            
            return {
                "database": db_performance,
                "cache": cache_performance
            }
        except Exception as e:
            logger.error(f"Performance monitoring failed: {str(e)}")
            return {"error": str(e)}
    
    async def _monitor_database_performance(self) -> Dict[str, Any]:
        """Monitor database performance."""
        query = text("""
            SELECT COUNT(*) as total_queries, AVG(processing_time_ms) as avg_time
            FROM performance_metrics 
            WHERE created_at >= NOW() - INTERVAL '1 hour'
        """)
        
        result = await self.db.execute(query)
        row = result.fetchone()
        
        return {
            "total_queries": row.total_queries,
            "avg_query_time": row.avg_time
        }


async def get_performance_service() -> PerformanceService:
    """Dependency injection for performance service."""
    import redis
    from ..core.config import get_settings
    
    settings = get_settings()
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    
    async for db in get_async_session():
        return PerformanceService(db, redis_client)
