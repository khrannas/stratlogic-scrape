"""
Database models for StratLogic Scraping System.

This module contains SQLAlchemy models for all database tables
with proper relationships, validation, and methods.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, BigInteger, ForeignKey, Enum, JSON, ARRAY, Numeric
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.declarative import declared_attr
import enum

from .database import Base
from .utils import get_current_timestamp


class JobStatus(enum.Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ArtifactType(enum.Enum):
    """Artifact type enumeration."""
    WEB_PAGE = "web_page"
    PDF = "pdf"
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    PAPER = "paper"
    GOVERNMENT_DOC = "government_doc"
    SOCIAL_MEDIA = "social_media"


class UserRole(enum.Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    MODERATOR = "moderator"


class TimestampMixin:
    """Mixin for timestamp fields."""
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), default=get_current_timestamp, nullable=False)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), default=get_current_timestamp, onupdate=get_current_timestamp, nullable=False)


class User(Base, TimestampMixin):
    """User model."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    scraping_jobs = relationship("ScrapingJob", back_populates="user", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    api_rate_limits = relationship("APIRateLimit", back_populates="user", cascade="all, delete-orphan")
    
    # Security relationships
    security_events = relationship("SecurityEvent", back_populates="user", cascade="all, delete-orphan")
    security_alerts = relationship("SecurityAlert", foreign_keys="SecurityAlert.user_id", back_populates="user", cascade="all, delete-orphan")
    rate_limits = relationship("RateLimit", back_populates="user", cascade="all, delete-orphan")
    data_access_logs = relationship("DataAccessLog", back_populates="user", cascade="all, delete-orphan")
    
    # Content processing relationships
    export_jobs = relationship("ExportJob", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    scheduled_reports = relationship("ScheduledReport", back_populates="user", cascade="all, delete-orphan")
    document_annotations = relationship("DocumentAnnotation", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_viewer(self) -> bool:
        """Check if user is viewer."""
        return self.role == UserRole.VIEWER


class UserSession(Base, TimestampMixin):
    """User session model."""
    
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="user_sessions")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.now(timezone.utc) > self.expires_at


class ScrapingJob(Base, TimestampMixin):
    """Scraping job model."""
    
    __tablename__ = "scraping_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    job_type = Column(String(50), nullable=False, index=True)  # 'web', 'paper', 'government'
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    keywords = Column(ARRAY(String))
    expanded_keywords = Column(ARRAY(String))
    urls = Column(ARRAY(String))
    search_queries = Column(ARRAY(String))
    configuration = Column(JSON)
    progress = Column(Integer, default=0, nullable=False)  # 0-100
    total_items = Column(Integer, default=0, nullable=False)
    processed_items = Column(Integer, default=0, nullable=False)
    failed_items = Column(Integer, default=0, nullable=False)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="scraping_jobs")
    artifacts = relationship("Artifact", back_populates="job", cascade="all, delete-orphan")
    job_configurations = relationship("JobConfiguration", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ScrapingJob(id={self.id}, title='{self.title}', status={self.status})>"
    
    @property
    def is_completed(self) -> bool:
        """Check if job is completed."""
        return self.status == JobStatus.COMPLETED
    
    @property
    def is_running(self) -> bool:
        """Check if job is running."""
        return self.status == JobStatus.RUNNING
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items - self.failed_items) / self.total_items * 100
    
    def update_progress(self, processed: int, total: int, failed: int = 0):
        """Update job progress."""
        self.processed_items = processed
        self.total_items = total
        self.failed_items = failed
        
        if total > 0:
            self.progress = int((processed / total) * 100)
        else:
            self.progress = 0


class JobConfiguration(Base, TimestampMixin):
    """Job configuration model."""
    
    __tablename__ = "job_configurations"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scraping_jobs.id"), nullable=False, index=True)
    config_key = Column(String(100), nullable=False, index=True)
    config_value = Column(Text)
    
    # Relationships
    job = relationship("ScrapingJob", back_populates="job_configurations")
    
    def __repr__(self):
        return f"<JobConfiguration(id={self.id}, job_id={self.job_id}, key='{self.config_key}')>"


class Artifact(Base, TimestampMixin):
    """Artifact model."""
    
    __tablename__ = "artifacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scraping_jobs.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    artifact_type = Column(Enum(ArtifactType), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    source_url = Column(Text)
    content_hash = Column(String(64), nullable=False, index=True)
    file_size = Column(BigInteger)
    mime_type = Column(String(100))
    minio_path = Column(String(500), nullable=False)
    content_text = Column(Text)
    content_summary = Column(Text)
    keywords = Column(ARRAY(String))
    tags = Column(ARRAY(String))
    language = Column(String(10))
    is_public = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    job = relationship("ScrapingJob", back_populates="artifacts")
    user = relationship("User", back_populates="artifacts")
    metadata_tags = relationship("MetadataTag", back_populates="artifact", cascade="all, delete-orphan")
    content_extractions = relationship("ContentExtraction", back_populates="artifact", cascade="all, delete-orphan")
    content_enrichment = relationship("ContentEnrichment", back_populates="artifact", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Artifact(id={self.id}, title='{self.title}', type={self.artifact_type})>"
    
    @property
    def file_size_formatted(self) -> str:
        """Get formatted file size."""
        if not self.file_size:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
    
    @property
    def has_content(self) -> bool:
        """Check if artifact has content."""
        return bool(self.content_text or self.content_summary)


class MetadataTag(Base, TimestampMixin):
    """Metadata tag model."""
    
    __tablename__ = "metadata_tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    artifact_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False, index=True)
    tag_type = Column(String(50), nullable=False, index=True)
    tag_key = Column(String(100), nullable=False, index=True)
    tag_value = Column(Text)
    
    # Relationships
    artifact = relationship("Artifact", back_populates="metadata_tags")
    
    def __repr__(self):
        return f"<MetadataTag(id={self.id}, artifact_id={self.artifact_id}, type='{self.tag_type}', key='{self.tag_key}')>"


class ContentExtraction(Base, TimestampMixin):
    """Content extraction model."""
    
    __tablename__ = "content_extractions"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    artifact_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False, index=True)
    extraction_type = Column(String(50), nullable=False, index=True)
    extracted_data = Column(JSON)
    confidence_score = Column(Numeric(3, 2))
    
    # Relationships
    artifact = relationship("Artifact", back_populates="content_extractions")
    
    def __repr__(self):
        return f"<ContentExtraction(id={self.id}, artifact_id={self.artifact_id}, type='{self.extraction_type}')>"


class SystemConfig(Base, TimestampMixin):
    """System configuration model."""
    
    __tablename__ = "system_config"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text)
    type = Column(String(20), default="string")
    description = Column(Text)
    is_sensitive = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f"<SystemConfig(id={self.id}, key='{self.key}')>"


class APIRateLimit(Base, TimestampMixin):
    """API rate limit model."""
    
    __tablename__ = "api_rate_limits"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    endpoint = Column(String(100), nullable=False, index=True)
    request_count = Column(Integer, default=0, nullable=False)
    window_start = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="api_rate_limits")
    
    def __repr__(self):
        return f"<APIRateLimit(id={self.id}, user_id={self.user_id}, endpoint='{self.endpoint}')>"


class AuditLog(Base, TimestampMixin):
    """Audit log model."""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50))
    resource_id = Column(UUID(as_uuid=True))
    details = Column(JSON)
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"
    
    @property
    def ip_address_str(self) -> Optional[str]:
        """Get IP address as string."""
        return str(self.ip_address) if self.ip_address else None


class APIKey(Base, TimestampMixin):
    """API key model."""
    
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, index=True)
    permissions = Column(ARRAY(String))
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.key_name}', user_id={self.user_id})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if API key is expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if API key is valid."""
        return self.is_active and not self.is_expired
    
    def has_permission(self, permission: str) -> bool:
        """Check if API key has specific permission."""
        if not self.permissions:
            return False
        return permission in self.permissions
