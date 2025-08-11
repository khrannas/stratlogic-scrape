"""
Redis configuration module.

This module contains Redis-specific configuration and utilities.
"""

import redis
from typing import Optional, Dict, Any

from ..src.core.config import settings


def create_redis_client():
    """Create Redis client with configuration."""
    return redis.from_url(
        settings.redis_url,
        password=settings.redis_password,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30,
    )


def check_redis_health():
    """Check Redis health and connectivity."""
    try:
        client = create_redis_client()
        client.ping()
        return True
    except Exception:
        return False


def get_redis_info():
    """Get Redis connection information."""
    return {
        "url": settings.redis_url.replace(settings.redis_password or "", "***") if settings.redis_password else settings.redis_url,
        "password_set": bool(settings.redis_password),
    }


def get_redis_stats():
    """Get Redis statistics."""
    try:
        client = create_redis_client()
        info = client.info()
        return {
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "0B"),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
        }
    except Exception:
        return {}


def clear_redis_cache():
    """Clear all Redis cache."""
    try:
        client = create_redis_client()
        client.flushdb()
        return True
    except Exception:
        return False


def get_redis_keys(pattern: str = "*"):
    """Get Redis keys matching pattern."""
    try:
        client = create_redis_client()
        return client.keys(pattern)
    except Exception:
        return []


def set_redis_key(key: str, value: str, expire: Optional[int] = None):
    """Set Redis key with optional expiration."""
    try:
        client = create_redis_client()
        client.set(key, value, ex=expire)
        return True
    except Exception:
        return False


def get_redis_key(key: str):
    """Get Redis key value."""
    try:
        client = create_redis_client()
        return client.get(key)
    except Exception:
        return None
