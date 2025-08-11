"""
Monitoring service for the StratLogic Scraping System.

This service handles system health checks, metrics collection,
user activity tracking, and performance monitoring.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.database import get_async_session
from ..core.models.monitoring import (
    Alert, HealthStatus, PerformanceMetrics, ScrapingMetrics,
    ServiceType, SystemHealth, UserActivity
)
from ..core.models import User, ScrapingJob
from ..storage.minio_client import MinIOClient
from ..core.config import get_settings


class MonitoringService:
    """Service for system monitoring and analytics."""
    
    def __init__(self, db: AsyncSession, minio_client: MinIOClient):
        self.db = db
        self.minio_client = minio_client
        self.settings = get_settings()
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive system health check."""
        health_results = {}
        
        # Check database health
        db_health = await self._check_database_health()
        health_results["database"] = db_health
        
        # Check MinIO health
        minio_health = await self._check_minio_health()
        health_results["minio"] = minio_health
        
        # Check Redis health (if available)
        redis_health = await self._check_redis_health()
        health_results["redis"] = redis_health
        
        # Store health check results
        await self._store_health_check(health_results)
        
        return health_results
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        start_time = time.time()
        try:
            # Test database connection with a simple query
            result = await self.db.execute(select(func.count(User.id)))
            count = result.scalar()
            
            response_time = (time.time() - start_time) * 1000
            status = HealthStatus.HEALTHY if count is not None else HealthStatus.DEGRADED
            
            return {
                "status": status,
                "response_time_ms": response_time,
                "details": {"user_count": count}
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "status": HealthStatus.UNHEALTHY,
                "response_time_ms": response_time,
                "error_message": str(e)
            }
    
    async def _check_minio_health(self) -> Dict[str, Any]:
        """Check MinIO connectivity and bucket access."""
        start_time = time.time()
        try:
            # Test MinIO connection by listing buckets
            buckets = await self.minio_client.list_buckets()
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": HealthStatus.HEALTHY,
                "response_time_ms": response_time,
                "details": {"bucket_count": len(buckets)}
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "status": HealthStatus.UNHEALTHY,
                "response_time_ms": response_time,
                "error_message": str(e)
            }
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity."""
        start_time = time.time()
        try:
            # This would require Redis client implementation
            # For now, return unknown status
            response_time = (time.time() - start_time) * 1000
            return {
                "status": HealthStatus.UNKNOWN,
                "response_time_ms": response_time,
                "details": {"message": "Redis health check not implemented"}
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "status": HealthStatus.UNHEALTHY,
                "response_time_ms": response_time,
                "error_message": str(e)
            }
    
    async def _store_health_check(self, health_results: Dict[str, Any]) -> None:
        """Store health check results in database."""
        for service_type, result in health_results.items():
            health_record = SystemHealth(
                service_type=ServiceType(service_type),
                status=result["status"],
                response_time_ms=result.get("response_time_ms"),
                error_message=result.get("error_message"),
                details=json.dumps(result.get("details", {}))
            )
            self.db.add(health_record)
        
        await self.db.commit()
    
    async def record_scraping_metrics(
        self,
        job_id: UUID,
        scraper_type: str,
        success: bool,
        duration_ms: float,
        items_processed: int = 0,
        items_failed: int = 0,
        error_message: Optional[str] = None
    ) -> None:
        """Record scraping job metrics."""
        metrics = ScrapingMetrics(
            job_id=job_id,
            scraper_type=scraper_type,
            success=success,
            duration_ms=duration_ms,
            items_processed=items_processed,
            items_failed=items_failed,
            error_message=error_message
        )
        
        self.db.add(metrics)
        await self.db.commit()
    
    async def record_user_activity(
        self,
        user_id: UUID,
        activity_type: str,
        endpoint: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record user activity for analytics."""
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            endpoint=endpoint,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            details=json.dumps(details) if details else None
        )
        
        self.db.add(activity)
        await self.db.commit()
    
    async def record_performance_metric(
        self,
        metric_name: str,
        metric_type: str,
        value: float,
        unit: str,
        labels: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record performance metric."""
        metric = PerformanceMetrics(
            metric_name=metric_name,
            metric_type=metric_type,
            value=value,
            unit=unit,
            labels=json.dumps(labels) if labels else None
        )
        
        self.db.add(metric)
        await self.db.commit()
    
    async def get_scraping_analytics(
        self,
        days: int = 7,
        scraper_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get scraping analytics for the specified period."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Build query
        query = select(ScrapingMetrics).where(
            ScrapingMetrics.created_at >= start_date
        )
        
        if scraper_type:
            query = query.where(ScrapingMetrics.scraper_type == scraper_type)
        
        result = await self.db.execute(query)
        metrics = result.scalars().all()
        
        # Calculate analytics
        total_jobs = len(metrics)
        successful_jobs = sum(1 for m in metrics if m.success)
        failed_jobs = total_jobs - successful_jobs
        success_rate = (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0
        
        avg_duration = sum(m.duration_ms for m in metrics) / total_jobs if total_jobs > 0 else 0
        total_items_processed = sum(m.items_processed for m in metrics)
        total_items_failed = sum(m.items_failed for m in metrics)
        
        return {
            "period_days": days,
            "total_jobs": total_jobs,
            "successful_jobs": successful_jobs,
            "failed_jobs": failed_jobs,
            "success_rate": round(success_rate, 2),
            "average_duration_ms": round(avg_duration, 2),
            "total_items_processed": total_items_processed,
            "total_items_failed": total_items_failed,
            "scraper_type": scraper_type or "all"
        }
    
    async def get_user_activity_analytics(
        self,
        days: int = 7,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get user activity analytics for the specified period."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Build query
        query = select(UserActivity).where(
            UserActivity.created_at >= start_date
        )
        
        if user_id:
            query = query.where(UserActivity.user_id == user_id)
        
        result = await self.db.execute(query)
        activities = result.scalars().all()
        
        # Calculate analytics
        total_activities = len(activities)
        activity_types = {}
        endpoints = {}
        
        for activity in activities:
            # Count activity types
            activity_types[activity.activity_type] = activity_types.get(activity.activity_type, 0) + 1
            
            # Count endpoints
            if activity.endpoint:
                endpoints[activity.endpoint] = endpoints.get(activity.endpoint, 0) + 1
        
        return {
            "period_days": days,
            "total_activities": total_activities,
            "activity_types": activity_types,
            "top_endpoints": dict(sorted(endpoints.items(), key=lambda x: x[1], reverse=True)[:10]),
            "user_id": str(user_id) if user_id else "all"
        }
    
    async def get_system_performance_metrics(
        self,
        metric_name: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get system performance metrics."""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = select(PerformanceMetrics).where(
            PerformanceMetrics.timestamp >= start_time
        )
        
        if metric_name:
            query = query.where(PerformanceMetrics.metric_name == metric_name)
        
        query = query.order_by(PerformanceMetrics.timestamp.desc())
        
        result = await self.db.execute(query)
        metrics = result.scalars().all()
        
        return [
            {
                "id": str(metric.id),
                "metric_name": metric.metric_name,
                "metric_type": metric.metric_type,
                "value": metric.value,
                "unit": metric.unit,
                "labels": json.loads(metric.labels) if metric.labels else None,
                "timestamp": metric.timestamp.isoformat()
            }
            for metric in metrics
        ]
    
    async def create_alert(
        self,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        source: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a new system alert."""
        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            source=source,
            details=json.dumps(details) if details else None
        )
        
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        
        return alert
    
    async def get_active_alerts(self) -> List[Alert]:
        """Get all unresolved alerts."""
        query = select(Alert).where(Alert.resolved == False).order_by(Alert.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def resolve_alert(self, alert_id: UUID, resolved_by: UUID) -> Alert:
        """Mark an alert as resolved."""
        query = select(Alert).where(Alert.id == alert_id)
        result = await self.db.execute(query)
        alert = result.scalar_one_or_none()
        
        if alert:
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = resolved_by
            await self.db.commit()
            await self.db.refresh(alert)
        
        return alert


async def get_monitoring_service() -> MonitoringService:
    """Dependency injection for monitoring service."""
    async for db in get_async_session():
        minio_client = MinIOClient()
        return MonitoringService(db, minio_client)
