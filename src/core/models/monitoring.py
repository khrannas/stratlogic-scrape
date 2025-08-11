"""
Monitoring and analytics data models for the StratLogic Scraping System.

This module contains SQLAlchemy models for tracking system health,
scraping metrics, user activity, and performance analytics.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Float, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from ..models import Base, TimestampMixin


class HealthStatus(str, Enum):
    """Health status enumeration for system components."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ServiceType(str, Enum):
    """Service type enumeration for monitoring."""
    DATABASE = "database"
    MINIO = "minio"
    REDIS = "redis"
    API = "api"
    SCRAPER = "scraper"
    CELERY = "celery"


class MetricType(str, Enum):
    """Metric type enumeration for analytics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class SystemHealth(Base, TimestampMixin):
    """System health check records."""
    
    __tablename__ = "system_health"
    
    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    service_type: ServiceType = Column(SQLEnum(ServiceType), nullable=False)
    status: HealthStatus = Column(SQLEnum(HealthStatus), nullable=False)
    response_time_ms: Optional[float] = Column(Float)
    error_message: Optional[str] = Column(Text)
    details: Optional[str] = Column(Text)  # JSON string with additional details


class ScrapingMetrics(Base, TimestampMixin):
    """Scraping performance and success metrics."""
    
    __tablename__ = "scraping_metrics"
    
    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("scraping_jobs.id"), nullable=False)
    scraper_type: String = Column(String(50), nullable=False)  # web, paper, government
    success: bool = Column(Integer, nullable=False)  # 0 or 1 for boolean
    duration_ms: float = Column(Float, nullable=False)
    items_processed: int = Column(Integer, default=0)
    items_failed: int = Column(Integer, default=0)
    error_message: Optional[str] = Column(Text)
    
    # Relationships
    job = relationship("ScrapingJob", back_populates="metrics")


class UserActivity(Base, TimestampMixin):
    """User activity tracking for analytics."""
    
    __tablename__ = "user_activity"
    
    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    activity_type: String = Column(String(50), nullable=False)  # login, logout, api_call, etc.
    endpoint: Optional[str] = Column(String(200))
    ip_address: Optional[str] = Column(String(45))  # IPv6 compatible
    user_agent: Optional[str] = Column(Text)
    session_id: Optional[str] = Column(String(100))
    details: Optional[str] = Column(Text)  # JSON string with additional details
    
    # Relationships
    user = relationship("User", back_populates="activities")


class PerformanceMetrics(Base, TimestampMixin):
    """System performance metrics."""
    
    __tablename__ = "performance_metrics"
    
    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    metric_name: String = Column(String(100), nullable=False)
    metric_type: MetricType = Column(SQLEnum(MetricType), nullable=False)
    value: float = Column(Float, nullable=False)
    unit: String = Column(String(20), nullable=False)  # ms, bytes, count, etc.
    labels: Optional[str] = Column(Text)  # JSON string with metric labels
    timestamp: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)


class Alert(Base, TimestampMixin):
    """System alerts and notifications."""
    
    __tablename__ = "alerts"
    
    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    alert_type: String = Column(String(50), nullable=False)  # error, warning, info
    severity: String = Column(String(20), nullable=False)  # low, medium, high, critical
    title: String = Column(String(200), nullable=False)
    message: Text = Column(Text, nullable=False)
    source: String = Column(String(100), nullable=False)  # service that generated the alert
    resolved: bool = Column(Integer, default=0)  # 0 or 1 for boolean
    resolved_at: Optional[datetime] = Column(DateTime)
    resolved_by: Optional[UUID] = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    details: Optional[str] = Column(Text)  # JSON string with additional details
    
    # Relationships
    resolver = relationship("User")


# Add relationships to existing models
from ..models import User, ScrapingJob

# Add to User model
User.activities = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")

# Add to ScrapingJob model  
ScrapingJob.metrics = relationship("ScrapingMetrics", back_populates="job", cascade="all, delete-orphan")
