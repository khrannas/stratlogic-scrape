"""
Security models for the StratLogic Scraping System.

This module defines security-related database models including audit logging,
API key management, session tracking, security alerts, and rate limiting.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from ..database import Base
from ..utils import TimestampMixin


class SecurityEventType(str, Enum):
    """Types of security events for audit logging."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_ACCESS = "data_access"
    DATA_EXPORT = "data_export"
    ADMIN_ACTION = "admin_action"
    SECURITY_ALERT = "security_alert"


class SecurityLevel(str, Enum):
    """Security levels for events and alerts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Status of security alerts."""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class SecurityEvent(Base, TimestampMixin):
    """Model for security event audit logging."""
    
    __tablename__ = "security_events"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    event_data = Column(Text, nullable=True)  # JSON string of additional data
    security_level = Column(String(20), default=SecurityLevel.LOW, nullable=False)
    session_id = Column(String(100), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="security_events")
    
    # Indexes
    __table_args__ = (
        Index("idx_security_events_user_type", "user_id", "event_type"),
        Index("idx_security_events_created_at", "created_at"),
        Index("idx_security_events_ip_address", "ip_address"),
        Index("idx_security_events_level", "security_level"),
    )


class ApiKey(Base, TimestampMixin):
    """Model for API key management."""
    
    __tablename__ = "api_keys"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    permissions = Column(Text, nullable=True)  # JSON string of permissions
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    last_used_ip = Column(String(45), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    # Indexes
    __table_args__ = (
        Index("idx_api_keys_user_id", "user_id"),
        Index("idx_api_keys_active", "is_active"),
        Index("idx_api_keys_expires", "expires_at"),
    )


class UserSession(Base, TimestampMixin):
    """Model for user session management."""
    
    __tablename__ = "user_sessions"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), nullable=False, unique=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_sessions_user_id", "user_id"),
        Index("idx_user_sessions_token", "session_token"),
        Index("idx_user_sessions_active", "is_active"),
        Index("idx_user_sessions_expires", "expires_at"),
    )


class SecurityAlert(Base, TimestampMixin):
    """Model for security alerts and notifications."""
    
    __tablename__ = "security_alerts"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    alert_type = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    security_level = Column(String(20), default=SecurityLevel.MEDIUM, nullable=False)
    status = Column(String(20), default=AlertStatus.OPEN, nullable=False)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(45), nullable=True)
    alert_data = Column(Text, nullable=True)  # JSON string of additional data
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="security_alerts")
    resolver = relationship("User", foreign_keys=[resolved_by])
    
    # Indexes
    __table_args__ = (
        Index("idx_security_alerts_type", "alert_type"),
        Index("idx_security_alerts_status", "status"),
        Index("idx_security_alerts_level", "security_level"),
        Index("idx_security_alerts_user", "user_id"),
        Index("idx_security_alerts_created", "created_at"),
    )


class RateLimit(Base, TimestampMixin):
    """Model for rate limiting tracking."""
    
    __tablename__ = "rate_limits"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(45), nullable=False, index=True)
    endpoint = Column(String(100), nullable=False)
    request_count = Column(Integer, default=1, nullable=False)
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    blocked_until = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="rate_limits")
    
    # Indexes
    __table_args__ = (
        Index("idx_rate_limits_user_ip", "user_id", "ip_address"),
        Index("idx_rate_limits_endpoint", "endpoint"),
        Index("idx_rate_limits_window", "window_start", "window_end"),
        Index("idx_rate_limits_blocked", "is_blocked", "blocked_until"),
    )


class DataAccessLog(Base, TimestampMixin):
    """Model for data access logging."""
    
    __tablename__ = "data_access_logs"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    resource_type = Column(String(50), nullable=False)  # 'artifact', 'job', 'user', etc.
    resource_id = Column(PostgresUUID(as_uuid=True), nullable=True)
    action = Column(String(50), nullable=False)  # 'read', 'write', 'delete', 'export'
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    access_data = Column(Text, nullable=True)  # JSON string of access details
    
    # Relationships
    user = relationship("User", back_populates="data_access_logs")
    
    # Indexes
    __table_args__ = (
        Index("idx_data_access_user", "user_id"),
        Index("idx_data_access_resource", "resource_type", "resource_id"),
        Index("idx_data_access_action", "action"),
        Index("idx_data_access_created", "created_at"),
    )
