"""
Optimized Redis configuration module.

This module provides enhanced Redis configuration with performance optimizations,
advanced caching strategies, and monitoring capabilities.
"""

import redis
import json
import time
import logging
from typing import Optional, Dict, Any, List
from functools import wraps

from ..src.core.config import settings

logger = logging.getLogger(__name__)


class OptimizedRedisClient:
    """Optimized Redis client with enhanced caching capabilities."""
    
    def __init__(self):
        self.client = redis.from_url(
            settings.redis_url,
            password=settings.redis_password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
            max_connections=50,  # Increased connection pool
            socket_keepalive=True,
            socket_keepalive_options={},
        )
        self.cache_stats = {"hits": 0, "misses": 0, "sets": 0}
    
    def get(self, key: str, default=None):
        """Get value from cache with statistics tracking."""
        try:
            value = self.client.get(key)
            if value is not None:
                self.cache_stats["hits"] += 1
                return value
            else:
                self.cache_stats["misses"] += 1
                return default
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            self.cache_stats["misses"] += 1
            return default
    
    def set(self, key: str, value: str, ex: Optional[int] = None):
        """Set value in cache with statistics tracking."""
        try:
            result = self.client.set(key, value, ex=ex)
            if result:
                self.cache_stats["sets"] += 1
            return result
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    def setex(self, key: str, time: int, value: str):
        """Set value with expiration."""
        return self.set(key, value, ex=time)
    
    def delete(self, key: str):
        """Delete key from cache."""
        try:
            return self.client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    def exists(self, key: str):
        """Check if key exists."""
        try:
            return self.client.exists(key)
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    def keys(self, pattern: str = "*"):
        """Get keys matching pattern."""
        try:
            return self.client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis keys error for pattern {pattern}: {e}")
            return []
    
    def info(self):
        """Get Redis server information."""
        try:
            return self.client.info()
        except Exception as e:
            logger.error(f"Redis info error: {e}")
            return {}
    
    def dbsize(self):
        """Get database size."""
        try:
            return self.client.dbsize()
        except Exception as e:
            logger.error(f"Redis dbsize error: {e}")
            return 0
    
    def flushdb(self):
        """Clear all keys from current database."""
        try:
            return self.client.flushdb()
        except Exception as e:
            logger.error(f"Redis flushdb error: {e}")
            return False
    
    def get_cache_stats(self):
        """Get cache performance statistics."""
        return self.cache_stats.copy()
    
    def reset_cache_stats(self):
        """Reset cache statistics."""
        self.cache_stats = {"hits": 0, "misses": 0, "sets": 0}
    
    def get_cache_hit_rate(self):
        """Calculate cache hit rate."""
        total = self.cache_stats["hits"] + self.cache_stats["misses"]
        return (self.cache_stats["hits"] / total * 100) if total > 0 else 0


def create_optimized_redis_client():
    """Create optimized Redis client."""
    return OptimizedRedisClient()


def check_optimized_redis_health():
    """Check optimized Redis health and connectivity."""
    try:
        client = create_optimized_redis_client()
        client.client.ping()
        
        # Get Redis info
        info = client.info()
        
        return {
            "status": "healthy",
            "version": info.get("redis_version", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "0B"),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "cache_stats": client.get_cache_stats()
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def get_optimized_redis_info():
    """Get optimized Redis connection information."""
    return {
        "url": settings.redis_url.replace(settings.redis_password or "", "***") if settings.redis_password else settings.redis_url,
        "password_set": bool(settings.redis_password),
        "max_connections": 50,
        "socket_keepalive": True,
        "health_check_interval": 30,
        "optimizations": [
            "Enhanced connection pooling",
            "Cache statistics tracking",
            "Automatic retry on timeout",
            "Socket keepalive",
            "Health check monitoring"
        ]
    }


class CacheManager:
    """Advanced cache management with strategies and patterns."""
    
    def __init__(self, redis_client: OptimizedRedisClient):
        self.redis = redis_client
        self.default_ttl = 3600  # 1 hour default
    
    def cache_user_data(self, user_id: str, user_data: Dict[str, Any], ttl: int = 3600):
        """Cache user data with optimized key pattern."""
        key = f"user:{user_id}:data"
        return self.redis.setex(key, ttl, json.dumps(user_data))
    
    def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user data."""
        key = f"user:{user_id}:data"
        data = self.redis.get(key)
        return json.loads(data) if data else None
    
    def cache_job_statistics(self, stats: Dict[str, Any], ttl: int = 1800):
        """Cache job statistics."""
        key = "stats:jobs:24h"
        return self.redis.setex(key, ttl, json.dumps(stats))
    
    def get_job_statistics(self) -> Optional[Dict[str, Any]]:
        """Get cached job statistics."""
        key = "stats:jobs:24h"
        data = self.redis.get(key)
        return json.loads(data) if data else None
    
    def cache_search_results(self, query: str, results: List[Dict], ttl: int = 900):
        """Cache search results."""
        key = f"search:results:{hash(query)}"
        return self.redis.setex(key, ttl, json.dumps(results))
    
    def get_search_results(self, query: str) -> Optional[List[Dict]]:
        """Get cached search results."""
        key = f"search:results:{hash(query)}"
        data = self.redis.get(key)
        return json.loads(data) if data else None
    
    def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a user."""
        pattern = f"user:{user_id}:*"
        keys = self.redis.keys(pattern)
        for key in keys:
            self.redis.delete(key)
    
    def invalidate_job_cache(self, job_id: str):
        """Invalidate job-related cache entries."""
        patterns = [
            f"job:{job_id}:*",
            "stats:jobs:*"
        ]
        for pattern in patterns:
            keys = self.redis.keys(pattern)
            for key in keys:
                self.redis.delete(key)
    
    def get_cache_keys_by_pattern(self, pattern: str) -> List[str]:
        """Get cache keys matching pattern."""
        return self.redis.keys(pattern)
    
    def get_cache_usage_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache usage statistics."""
        info = self.redis.info()
        cache_stats = self.redis.get_cache_stats()
        
        return {
            "redis_info": {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            },
            "cache_stats": cache_stats,
            "hit_rate": self.redis.get_cache_hit_rate(),
            "total_keys": self.redis.dbsize()
        }


def cache_decorator(ttl: int = 3600, key_prefix: str = "cache"):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            redis_client = create_optimized_redis_client()
            
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            
            return result
        return wrapper
    return decorator


def get_redis_performance_tips():
    """Get Redis performance optimization tips."""
    return {
        "connection_pooling": {
            "max_connections": "Set to 50 for optimal performance",
            "socket_keepalive": "Enable to maintain persistent connections",
            "health_check_interval": "30 seconds for connection health monitoring",
            "retry_on_timeout": "Enable automatic retry on connection timeout"
        },
        "caching_strategies": {
            "ttl_strategy": "Use appropriate TTL based on data volatility",
            "key_patterns": "Use consistent key naming patterns",
            "cache_invalidation": "Implement proper cache invalidation strategies",
            "cache_warming": "Pre-populate cache with frequently accessed data"
        },
        "memory_optimization": {
            "maxmemory_policy": "Use allkeys-lru for automatic eviction",
            "memory_monitoring": "Monitor memory usage and set appropriate limits",
            "data_serialization": "Use efficient serialization formats",
            "compression": "Consider compression for large values"
        },
        "monitoring": {
            "cache_hit_rate": "Monitor and optimize cache hit rates",
            "slow_queries": "Monitor Redis slow query log",
            "memory_usage": "Track memory usage patterns",
            "connection_stats": "Monitor connection pool utilization"
        }
    }
