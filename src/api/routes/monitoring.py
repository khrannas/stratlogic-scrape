"""
Monitoring API routes for the StratLogic Scraping System.

This module provides endpoints for system health checks,
analytics, performance monitoring, and alerts.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from datetime import datetime
from ...auth.jwt import get_current_user
from ...core.models import User
from ...services.monitoring_service import MonitoringService, get_monitoring_service

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


# Pydantic models for API responses
class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str
    services: dict
    timestamp: str


class ScrapingAnalyticsResponse(BaseModel):
    """Response model for scraping analytics."""
    period_days: int
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    success_rate: float
    average_duration_ms: float
    total_items_processed: int
    total_items_failed: int
    scraper_type: str


class UserActivityAnalyticsResponse(BaseModel):
    """Response model for user activity analytics."""
    period_days: int
    total_activities: int
    activity_types: dict
    top_endpoints: dict
    user_id: str


class PerformanceMetricResponse(BaseModel):
    """Response model for performance metrics."""
    id: str
    metric_name: str
    metric_type: str
    value: float
    unit: str
    labels: Optional[dict]
    timestamp: str


class AlertResponse(BaseModel):
    """Response model for alerts."""
    id: str
    alert_type: str
    severity: str
    title: str
    message: str
    source: str
    resolved: bool
    created_at: str
    resolved_at: Optional[str]
    resolved_by: Optional[str]


class CreateAlertRequest(BaseModel):
    """Request model for creating alerts."""
    alert_type: str
    severity: str
    title: str
    message: str
    source: str
    details: Optional[dict] = None


@router.get("/health", response_model=HealthCheckResponse)
async def check_system_health(
    current_user: User = Depends(get_current_user),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
) -> HealthCheckResponse:
    """
    Perform comprehensive system health check.
    
    This endpoint checks the health of all system components including
    database, MinIO storage, and Redis cache.
    """
    from datetime import datetime
    
    # Check if user has admin privileges
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        health_results = await monitoring_service.check_system_health()
        
        # Determine overall system status
        overall_status = "healthy"
        for service, result in health_results.items():
            if result.get("status") == "unhealthy":
                overall_status = "unhealthy"
                break
            elif result.get("status") == "degraded":
                overall_status = "degraded"
        
        return HealthCheckResponse(
            status=overall_status,
            services=health_results,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/analytics/scraping", response_model=ScrapingAnalyticsResponse)
async def get_scraping_analytics(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    scraper_type: Optional[str] = Query(None, description="Filter by scraper type"),
    current_user: User = Depends(get_current_user),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
) -> ScrapingAnalyticsResponse:
    """
    Get scraping analytics for the specified period.
    
    Returns comprehensive analytics about scraping job performance,
    success rates, and processing statistics.
    """
    # Check if user has appropriate access
    if current_user.role not in ["ADMIN", "MODERATOR"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        analytics = await monitoring_service.get_scraping_analytics(days, scraper_type)
        return ScrapingAnalyticsResponse(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scraping analytics: {str(e)}")


@router.get("/analytics/user-activity", response_model=UserActivityAnalyticsResponse)
async def get_user_activity_analytics(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    user_id: Optional[UUID] = Query(None, description="Filter by specific user ID"),
    current_user: User = Depends(get_current_user),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
) -> UserActivityAnalyticsResponse:
    """
    Get user activity analytics for the specified period.
    
    Returns analytics about user activity patterns, login frequency,
    and API usage statistics.
    """
    # Check if user has appropriate access
    if current_user.role not in ["ADMIN", "MODERATOR"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Users can only view their own activity unless they're admin
    if current_user.role != "ADMIN" and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Can only view own activity")
    
    try:
        analytics = await monitoring_service.get_user_activity_analytics(days, user_id)
        return UserActivityAnalyticsResponse(**analytics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user activity analytics: {str(e)}")


@router.get("/metrics/performance", response_model=List[PerformanceMetricResponse])
async def get_performance_metrics(
    metric_name: Optional[str] = Query(None, description="Filter by metric name"),
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back"),
    current_user: User = Depends(get_current_user),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
) -> List[PerformanceMetricResponse]:
    """
    Get system performance metrics.
    
    Returns performance metrics for system monitoring and analysis.
    """
    # Check if user has appropriate access
    if current_user.role not in ["ADMIN", "MODERATOR"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        metrics = await monitoring_service.get_system_performance_metrics(metric_name, hours)
        return [PerformanceMetricResponse(**metric) for metric in metrics]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@router.get("/alerts", response_model=List[AlertResponse])
async def get_active_alerts(
    current_user: User = Depends(get_current_user),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
) -> List[AlertResponse]:
    """
    Get all active (unresolved) alerts.
    
    Returns a list of all unresolved system alerts and notifications.
    """
    # Check if user has appropriate access
    if current_user.role not in ["ADMIN", "MODERATOR"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        alerts = await monitoring_service.get_active_alerts()
        return [
            AlertResponse(
                id=str(alert.id),
                alert_type=alert.alert_type,
                severity=alert.severity,
                title=alert.title,
                message=alert.message,
                source=alert.source,
                resolved=alert.resolved,
                created_at=alert.created_at.isoformat(),
                resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
                resolved_by=str(alert.resolved_by) if alert.resolved_by else None
            )
            for alert in alerts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert_data: CreateAlertRequest,
    current_user: User = Depends(get_current_user),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
) -> AlertResponse:
    """
    Create a new system alert.
    
    Allows authorized users to create system alerts and notifications.
    """
    # Check if user has appropriate access
    if current_user.role not in ["ADMIN", "MODERATOR"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        alert = await monitoring_service.create_alert(
            alert_type=alert_data.alert_type,
            severity=alert_data.severity,
            title=alert_data.title,
            message=alert_data.message,
            source=alert_data.source,
            details=alert_data.details
        )
        
        return AlertResponse(
            id=str(alert.id),
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            source=alert.source,
            resolved=alert.resolved,
            created_at=alert.created_at.isoformat(),
            resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
            resolved_by=str(alert.resolved_by) if alert.resolved_by else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")


@router.put("/alerts/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
) -> AlertResponse:
    """
    Mark an alert as resolved.
    
    Allows authorized users to resolve system alerts.
    """
    # Check if user has appropriate access
    if current_user.role not in ["ADMIN", "MODERATOR"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        alert = await monitoring_service.resolve_alert(alert_id, current_user.id)
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return AlertResponse(
            id=str(alert.id),
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            message=alert.message,
            source=alert.source,
            resolved=alert.resolved,
            created_at=alert.created_at.isoformat(),
            resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
            resolved_by=str(alert.resolved_by) if alert.resolved_by else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")


@router.get("/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    monitoring_service: MonitoringService = Depends(get_monitoring_service)
) -> dict:
    """
    Get comprehensive dashboard data.
    
    Returns aggregated data for the monitoring dashboard including
    system health, recent metrics, and active alerts.
    """
    # Check if user has appropriate access
    if current_user.role not in ["ADMIN", "MODERATOR"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        # Get various dashboard components
        health_results = await monitoring_service.check_system_health()
        scraping_analytics = await monitoring_service.get_scraping_analytics(days=7)
        user_analytics = await monitoring_service.get_user_activity_analytics(days=7)
        active_alerts = await monitoring_service.get_active_alerts()
        recent_metrics = await monitoring_service.get_system_performance_metrics(hours=24)
        
        return {
            "system_health": health_results,
            "scraping_analytics": scraping_analytics,
            "user_analytics": user_analytics,
            "active_alerts_count": len(active_alerts),
            "recent_metrics_count": len(recent_metrics),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")
