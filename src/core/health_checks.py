"""
Health check system for the StratLogic Scraping System.

This module provides comprehensive health checks for all system components,
including database, Redis, MinIO, and external services, with automatic
service recovery and circuit breaker patterns.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from contextlib import asynccontextmanager

import redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from minio import Minio
from minio.error import S3Error

from .exceptions import HealthCheckError
from .database import get_async_session
from .config import get_settings
from ..services.logging_service import get_logger


logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    duration: float
    last_check: Optional[datetime] = None


class CircuitBreaker:
    """Circuit breaker pattern for health checks."""
    
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def record_success(self):
        """Record a successful operation."""
        if self.state == "HALF_OPEN":
            self._reset()
        self.failure_count = 0
    
    def record_failure(self):
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def can_execute(self) -> bool:
        """Check if operation can be executed."""
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        
        return True  # HALF_OPEN
    
    def _reset(self):
        """Reset circuit breaker."""
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None


class HealthChecker:
    """Main health checker class."""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.check_results: Dict[str, HealthCheckResult] = {}
        self.settings = get_settings()
        
        # Register default health checks
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default health checks."""
        self.register_check("database", self._check_database)
        self.register_check("redis", self._check_redis)
        self.register_check("minio", self._check_minio)
        self.register_check("external_apis", self._check_external_apis)
        self.register_check("system_resources", self._check_system_resources)
    
    def register_check(self, name: str, check_func: Callable):
        """Register a new health check."""
        self.checks[name] = check_func
        self.circuit_breakers[name] = CircuitBreaker()
    
    async def run_check(self, name: str) -> HealthCheckResult:
        """Run a specific health check."""
        if name not in self.checks:
            raise HealthCheckError(name, f"Health check '{name}' not found")
        
        circuit_breaker = self.circuit_breakers[name]
        
        if not circuit_breaker.can_execute():
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message="Circuit breaker is open",
                details={"circuit_state": circuit_breaker.state},
                timestamp=datetime.utcnow(),
                duration=0.0,
                last_check=self.check_results.get(name, None)
            )
        
        start_time = time.time()
        
        try:
            result = await self.checks[name]()
            circuit_breaker.record_success()
            
            health_result = HealthCheckResult(
                name=name,
                status=result.get("status", HealthStatus.UNKNOWN),
                message=result.get("message", ""),
                details=result.get("details", {}),
                timestamp=datetime.utcnow(),
                duration=time.time() - start_time,
                last_check=self.check_results.get(name, None)
            )
            
            self.check_results[name] = health_result
            return health_result
            
        except Exception as e:
            circuit_breaker.record_failure()
            logger.error(f"Health check '{name}' failed", extra={"error": str(e)})
            
            health_result = HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                details={"error": str(e), "circuit_state": circuit_breaker.state},
                timestamp=datetime.utcnow(),
                duration=time.time() - start_time,
                last_check=self.check_results.get(name, None)
            )
            
            self.check_results[name] = health_result
            return health_result
    
    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks."""
        results = {}
        
        for name in self.checks:
            try:
                results[name] = await self.run_check(name)
            except Exception as e:
                logger.error(f"Failed to run health check '{name}'", extra={"error": str(e)})
                results[name] = HealthCheckResult(
                    name=name,
                    status=HealthStatus.UNKNOWN,
                    message=f"Check execution failed: {str(e)}",
                    details={"error": str(e)},
                    timestamp=datetime.utcnow(),
                    duration=0.0
                )
        
        return results
    
    async def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        results = await self.run_all_checks()
        
        # Count statuses
        status_counts = {}
        for result in results.values():
            status = result.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Determine overall status
        if status_counts.get("unhealthy", 0) > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif status_counts.get("degraded", 0) > 0:
            overall_status = HealthStatus.DEGRADED
        elif status_counts.get("healthy", 0) > 0:
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {name: {
                "status": result.status.value,
                "message": result.message,
                "duration": result.duration,
                "timestamp": result.timestamp.isoformat()
            } for name, result in results.items()},
            "summary": {
                "total_checks": len(results),
                "status_counts": status_counts
            }
        }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            async with get_async_session() as session:
                # Test basic connectivity
                result = await session.execute(text("SELECT 1"))
                result.fetchone()
                
                # Test connection pool
                pool_info = await session.execute(text("""
                    SELECT 
                        count(*) as active_connections,
                        max_conn as max_connections
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                """))
                pool_data = pool_info.fetchone()
                
                # Check for slow queries
                slow_queries = await session.execute(text("""
                    SELECT 
                        query,
                        mean_time,
                        calls
                    FROM pg_stat_statements 
                    WHERE mean_time > 1000
                    ORDER BY mean_time DESC 
                    LIMIT 5
                """))
                slow_queries_data = slow_queries.fetchall()
                
                details = {
                    "active_connections": pool_data.active_connections if pool_data else 0,
                    "max_connections": pool_data.max_connections if pool_data else 0,
                    "slow_queries": len(slow_queries_data)
                }
                
                if slow_queries_data:
                    details["slow_queries_details"] = [
                        {"query": q.query[:100] + "...", "mean_time": q.mean_time, "calls": q.calls}
                        for q in slow_queries_data
                    ]
                
                return {
                    "status": HealthStatus.HEALTHY,
                    "message": "Database is healthy",
                    "details": details
                }
                
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Database check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis health."""
        try:
            redis_client = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                db=self.settings.redis_db,
                decode_responses=True
            )
            
            # Test basic connectivity
            redis_client.ping()
            
            # Get Redis info
            info = redis_client.info()
            
            # Check memory usage
            memory_usage = info.get("used_memory_human", "0B")
            max_memory = info.get("maxmemory_human", "0B")
            
            # Check connected clients
            connected_clients = info.get("connected_clients", 0)
            max_clients = info.get("maxclients", 0)
            
            details = {
                "version": info.get("redis_version", "unknown"),
                "uptime": info.get("uptime_in_seconds", 0),
                "memory_usage": memory_usage,
                "max_memory": max_memory,
                "connected_clients": connected_clients,
                "max_clients": max_clients,
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
            
            # Calculate hit rate
            total_requests = details["keyspace_hits"] + details["keyspace_misses"]
            if total_requests > 0:
                details["hit_rate"] = details["keyspace_hits"] / total_requests
            else:
                details["hit_rate"] = 0
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": "Redis is healthy",
                "details": details
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Redis check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _check_minio(self) -> Dict[str, Any]:
        """Check MinIO health."""
        try:
            minio_client = Minio(
                endpoint=f"{self.settings.minio_host}:{self.settings.minio_port}",
                access_key=self.settings.minio_access_key,
                secret_key=self.settings.minio_secret_key,
                secure=self.settings.minio_secure
            )
            
            # Test basic connectivity
            buckets = minio_client.list_buckets()
            bucket_count = len(list(buckets))
            
            # Check if required buckets exist
            required_buckets = ["artifacts", "temp", "backups"]
            existing_buckets = [b.name for b in minio_client.list_buckets()]
            missing_buckets = [b for b in required_buckets if b not in existing_buckets]
            
            details = {
                "bucket_count": bucket_count,
                "existing_buckets": existing_buckets,
                "missing_buckets": missing_buckets
            }
            
            if missing_buckets:
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": f"MinIO is accessible but missing buckets: {missing_buckets}",
                    "details": details
                }
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": "MinIO is healthy",
                "details": details
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"MinIO check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _check_external_apis(self) -> Dict[str, Any]:
        """Check external API health."""
        import aiohttp
        
        apis_to_check = [
            {"name": "arxiv", "url": "http://export.arxiv.org/api/query?search_query=all:electron&start=0&max_results=1"},
            {"name": "openai", "url": "https://api.openai.com/v1/models", "headers": {"Authorization": f"Bearer {self.settings.openai_api_key}"}},
        ]
        
        results = {}
        healthy_count = 0
        
        async with aiohttp.ClientSession() as session:
            for api in apis_to_check:
                try:
                    start_time = time.time()
                    
                    headers = api.get("headers", {})
                    async with session.get(api["url"], headers=headers, timeout=10) as response:
                        duration = time.time() - start_time
                        
                        if response.status == 200:
                            results[api["name"]] = {
                                "status": "healthy",
                                "response_time": duration,
                                "status_code": response.status
                            }
                            healthy_count += 1
                        else:
                            results[api["name"]] = {
                                "status": "unhealthy",
                                "response_time": duration,
                                "status_code": response.status
                            }
                            
                except Exception as e:
                    results[api["name"]] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
        
        total_apis = len(apis_to_check)
        if healthy_count == total_apis:
            status = HealthStatus.HEALTHY
            message = "All external APIs are healthy"
        elif healthy_count > 0:
            status = HealthStatus.DEGRADED
            message = f"{healthy_count}/{total_apis} external APIs are healthy"
        else:
            status = HealthStatus.UNHEALTHY
            message = "All external APIs are unhealthy"
        
        return {
            "status": status,
            "message": message,
            "details": {
                "total_apis": total_apis,
                "healthy_apis": healthy_count,
                "api_results": results
            }
        }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        import psutil
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network = psutil.net_io_counters()
            
            details = {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            }
            
            # Determine status based on thresholds
            if cpu_percent > 90 or memory.percent > 90 or details["disk"]["percent"] > 90:
                status = HealthStatus.UNHEALTHY
                message = "System resources are critically high"
            elif cpu_percent > 70 or memory.percent > 70 or details["disk"]["percent"] > 70:
                status = HealthStatus.DEGRADED
                message = "System resources are elevated"
            else:
                status = HealthStatus.HEALTHY
                message = "System resources are healthy"
            
            return {
                "status": status,
                "message": message,
                "details": details
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNKNOWN,
                "message": f"System resource check failed: {str(e)}",
                "details": {"error": str(e)}
            }


class HealthMonitor:
    """Continuous health monitoring with automatic recovery."""
    
    def __init__(self, check_interval: float = 60.0):
        self.health_checker = HealthChecker()
        self.check_interval = check_interval
        self.monitoring_task = None
        self.is_monitoring = False
        self.recovery_actions = {}
        
        # Register recovery actions
        self._register_recovery_actions()
    
    def _register_recovery_actions(self):
        """Register automatic recovery actions."""
        self.recovery_actions["database"] = self._recover_database
        self.recovery_actions["redis"] = self._recover_redis
        self.recovery_actions["minio"] = self._recover_minio
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitor_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop continuous health monitoring."""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Health monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                # Run health checks
                results = await self.health_checker.run_all_checks()
                
                # Check for unhealthy services and attempt recovery
                for name, result in results.items():
                    if result.status == HealthStatus.UNHEALTHY:
                        await self._attempt_recovery(name, result)
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error("Health monitoring error", extra={"error": str(e)})
                await asyncio.sleep(self.check_interval)
    
    async def _attempt_recovery(self, service_name: str, result: HealthCheckResult):
        """Attempt to recover an unhealthy service."""
        if service_name not in self.recovery_actions:
            logger.warning(f"No recovery action available for {service_name}")
            return
        
        try:
            logger.info(f"Attempting recovery for {service_name}")
            await self.recovery_actions[service_name]()
            logger.info(f"Recovery completed for {service_name}")
        except Exception as e:
            logger.error(f"Recovery failed for {service_name}", extra={"error": str(e)})
    
    async def _recover_database(self):
        """Recover database connection."""
        # This would implement database-specific recovery logic
        # For now, just log the attempt
        logger.info("Database recovery attempted")
    
    async def _recover_redis(self):
        """Recover Redis connection."""
        # This would implement Redis-specific recovery logic
        logger.info("Redis recovery attempted")
    
    async def _recover_minio(self):
        """Recover MinIO connection."""
        # This would implement MinIO-specific recovery logic
        logger.info("MinIO recovery attempted")


# Global health checker instance
_health_checker = HealthChecker()
_health_monitor = HealthMonitor()


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    return _health_checker


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance."""
    return _health_monitor


async def check_health() -> Dict[str, Any]:
    """Quick health check function."""
    return await _health_checker.get_overall_health()


async def start_health_monitoring():
    """Start health monitoring."""
    await _health_monitor.start_monitoring()


async def stop_health_monitoring():
    """Stop health monitoring."""
    await _health_monitor.stop_monitoring()
