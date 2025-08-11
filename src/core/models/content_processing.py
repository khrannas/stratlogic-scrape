"""
Content processing models for the StratLogic Scraping System.

This module defines SQLAlchemy models for advanced content processing,
including content enrichment, document processing, analytics, and export functionality.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TSVECTOR
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

from ..models import Base, TimestampMixin


# Association tables for many-to-many relationships
content_tag_association = Table(
    'content_tag_association',
    Base.metadata,
    Column('content_id', PGUUID(as_uuid=True), ForeignKey('content_enrichment.id')),
    Column('tag_id', PGUUID(as_uuid=True), ForeignKey('content_tags.id'))
)

content_relationship_association = Table(
    'content_relationship_association',
    Base.metadata,
    Column('content_id', PGUUID(as_uuid=True), ForeignKey('content_enrichment.id')),
    Column('related_content_id', PGUUID(as_uuid=True), ForeignKey('content_enrichment.id'))
)


class ContentType(str, Enum):
    """Content type enumeration."""
    TEXT = "text"
    PDF = "pdf"
    IMAGE = "image"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    WEBPAGE = "webpage"
    PAPER = "paper"
    GOVERNMENT_DOC = "government_doc"


class QualityLevel(str, Enum):
    """Content quality level enumeration."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """Processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportFormat(str, Enum):
    """Export format enumeration."""
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    PDF = "pdf"
    HTML = "html"
    XML = "xml"


class ReportType(str, Enum):
    """Report type enumeration."""
    CONTENT_ANALYSIS = "content_analysis"
    USAGE_STATISTICS = "usage_statistics"
    QUALITY_REPORT = "quality_report"
    TREND_ANALYSIS = "trend_analysis"
    SOURCE_ANALYSIS = "source_analysis"
    CUSTOM = "custom"


# Content Enrichment Models
class ContentEnrichment(Base, TimestampMixin):
    """Model for content enrichment data."""
    
    __tablename__ = "content_enrichment"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    artifact_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False)
    content_type: Mapped[ContentType] = mapped_column(String(50), nullable=False)
    
    # Content analysis results
    extracted_text: Mapped[Optional[str]] = mapped_column(Text)
    language: Mapped[Optional[str]] = mapped_column(String(10))
    word_count: Mapped[Optional[int]] = mapped_column(Integer)
    character_count: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Quality metrics
    quality_score: Mapped[Optional[float]] = mapped_column(Float)
    quality_level: Mapped[Optional[QualityLevel]] = mapped_column(String(20))
    readability_score: Mapped[Optional[float]] = mapped_column(Float)
    complexity_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Processing metadata
    processing_status: Mapped[ProcessingStatus] = mapped_column(String(20), default=ProcessingStatus.PENDING)
    processing_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relationships
    artifact = relationship("Artifact", back_populates="content_enrichment")
    tags = relationship("ContentTag", secondary=content_tag_association, back_populates="contents")
    versions = relationship("ContentVersion", back_populates="content", cascade="all, delete-orphan")
    relationships = relationship("ContentRelationship", back_populates="content", cascade="all, delete-orphan")
    document_structure = relationship("DocumentStructure", back_populates="content", uselist=False, cascade="all, delete-orphan")
    ocr_results = relationship("OCRResult", back_populates="content", cascade="all, delete-orphan")
    analytics = relationship("ContentAnalytics", back_populates="content", uselist=False, cascade="all, delete-orphan")


class ContentTag(Base, TimestampMixin):
    """Model for content tags."""
    
    __tablename__ = "content_tags"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    category: Mapped[Optional[str]] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Relationships
    contents = relationship("ContentEnrichment", secondary=content_tag_association, back_populates="tags")


class ContentVersion(Base, TimestampMixin):
    """Model for content versioning."""
    
    __tablename__ = "content_versions"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    content_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("content_enrichment.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    change_description: Mapped[Optional[str]] = mapped_column(Text)
    change_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Relationships
    content = relationship("ContentEnrichment", back_populates="versions")


class ContentRelationship(Base, TimestampMixin):
    """Model for content relationships."""
    
    __tablename__ = "content_relationships"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    content_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("content_enrichment.id"), nullable=False)
    related_content_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("content_enrichment.id"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)  # similar, related, duplicate, etc.
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    relationship_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Relationships
    content = relationship("ContentEnrichment", foreign_keys=[content_id], back_populates="relationships")
    related_content = relationship("ContentEnrichment", foreign_keys=[related_content_id])


# Document Processing Models
class DocumentStructure(Base, TimestampMixin):
    """Model for document structure analysis."""
    
    __tablename__ = "document_structures"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    content_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("content_enrichment.id"), nullable=False)
    
    # Structure analysis
    title: Mapped[Optional[str]] = mapped_column(String(500))
    authors: Mapped[Optional[List[str]]] = mapped_column(JSON)
    abstract: Mapped[Optional[str]] = mapped_column(Text)
    sections: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON)
    headings: Mapped[Optional[List[str]]] = mapped_column(JSON)
    page_count: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Metadata
    document_type: Mapped[Optional[str]] = mapped_column(String(50))
    language: Mapped[Optional[str]] = mapped_column(String(10))
    structure_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Relationships
    content = relationship("ContentEnrichment", back_populates="document_structure")
    tables = relationship("DocumentTable", back_populates="document_structure", cascade="all, delete-orphan")
    annotations = relationship("DocumentAnnotation", back_populates="document_structure", cascade="all, delete-orphan")


class DocumentTable(Base, TimestampMixin):
    """Model for extracted tables from documents."""
    
    __tablename__ = "document_tables"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_structure_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("document_structures.id"), nullable=False)
    
    # Table data
    table_title: Mapped[Optional[str]] = mapped_column(String(500))
    table_data: Mapped[List[List[str]]] = mapped_column(JSON, nullable=False)
    headers: Mapped[Optional[List[str]]] = mapped_column(JSON)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Extraction metadata
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    extraction_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Relationships
    document_structure = relationship("DocumentStructure", back_populates="tables")


class DocumentAnnotation(Base, TimestampMixin):
    """Model for document annotations."""
    
    __tablename__ = "document_annotations"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_structure_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("document_structures.id"), nullable=False)
    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    
    # Annotation data
    annotation_type: Mapped[str] = mapped_column(String(50), nullable=False)  # highlight, comment, tag, etc.
    annotation_text: Mapped[Optional[str]] = mapped_column(Text)
    annotation_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Position data
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    start_position: Mapped[Optional[int]] = mapped_column(Integer)
    end_position: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Relationships
    document_structure = relationship("DocumentStructure", back_populates="annotations")
    user = relationship("User")


class OCRResult(Base, TimestampMixin):
    """Model for OCR processing results."""
    
    __tablename__ = "ocr_results"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    content_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("content_enrichment.id"), nullable=False)
    
    # OCR data
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    language: Mapped[Optional[str]] = mapped_column(String(10))
    
    # Processing metadata
    ocr_engine: Mapped[str] = mapped_column(String(50), nullable=False)  # tesseract, easyocr, etc.
    processing_time: Mapped[Optional[float]] = mapped_column(Float)
    ocr_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Relationships
    content = relationship("ContentEnrichment", back_populates="ocr_results")


# Content Analytics Models
class ContentAnalytics(Base, TimestampMixin):
    """Model for content analytics data."""
    
    __tablename__ = "content_analytics"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    content_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("content_enrichment.id"), nullable=False)
    
    # Usage analytics
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    share_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Impact metrics
    impact_score: Mapped[Optional[float]] = mapped_column(Float)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float)
    popularity_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Trend data
    trend_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    analytics_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Relationships
    content = relationship("ContentEnrichment", back_populates="analytics")
    trends = relationship("ContentTrend", back_populates="analytics", cascade="all, delete-orphan")
    recommendations = relationship("ContentRecommendation", back_populates="analytics", cascade="all, delete-orphan")


class ContentTrend(Base, TimestampMixin):
    """Model for content trend analysis."""
    
    __tablename__ = "content_trends"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    analytics_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("content_analytics.id"), nullable=False)
    
    # Trend data
    trend_type: Mapped[str] = mapped_column(String(50), nullable=False)  # popularity, relevance, usage, etc.
    trend_value: Mapped[float] = mapped_column(Float, nullable=False)
    trend_direction: Mapped[str] = mapped_column(String(20), nullable=False)  # increasing, decreasing, stable
    trend_period: Mapped[str] = mapped_column(String(20), nullable=False)  # daily, weekly, monthly
    
    # Time series data
    time_series_data: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON)
    trend_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Relationships
    analytics = relationship("ContentAnalytics", back_populates="trends")


class ContentRecommendation(Base, TimestampMixin):
    """Model for content recommendations."""
    
    __tablename__ = "content_recommendations"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    analytics_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("content_analytics.id"), nullable=False)
    recommended_content_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("content_enrichment.id"), nullable=False)
    
    # Recommendation data
    recommendation_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation_reason: Mapped[Optional[str]] = mapped_column(Text)
    recommendation_type: Mapped[str] = mapped_column(String(50), nullable=False)  # similar, popular, trending, etc.
    
    # User interaction
    is_clicked: Mapped[bool] = mapped_column(Boolean, default=False)
    click_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    recommendation_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Relationships
    analytics = relationship("ContentAnalytics", back_populates="recommendations")
    recommended_content = relationship("ContentEnrichment")


# Export and Reporting Models
class ExportJob(Base, TimestampMixin):
    """Model for export jobs."""
    
    __tablename__ = "export_jobs"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Export configuration
    export_format: Mapped[ExportFormat] = mapped_column(String(20), nullable=False)
    export_query: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Job status
    status: Mapped[ProcessingStatus] = mapped_column(String(20), default=ProcessingStatus.PENDING)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metadata
    export_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Relationships
    user = relationship("User")


class Report(Base, TimestampMixin):
    """Model for generated reports."""
    
    __tablename__ = "reports"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Report configuration
    report_type: Mapped[ReportType] = mapped_column(String(50), nullable=False)
    report_title: Mapped[str] = mapped_column(String(200), nullable=False)
    report_description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Report data
    report_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    report_visualizations: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON)
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Generation metadata
    generation_parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    report_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Relationships
    user = relationship("User")
    scheduled_reports = relationship("ScheduledReport", back_populates="report", cascade="all, delete-orphan")


class ScheduledReport(Base, TimestampMixin):
    """Model for scheduled reports."""
    
    __tablename__ = "scheduled_reports"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    report_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("reports.id"))
    
    # Schedule configuration
    schedule_name: Mapped[str] = mapped_column(String(200), nullable=False)
    schedule_cron: Mapped[str] = mapped_column(String(100), nullable=False)  # cron expression
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Report configuration
    report_type: Mapped[ReportType] = mapped_column(String(50), nullable=False)
    report_parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    
    # Execution tracking
    last_execution: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_execution: Mapped[Optional[datetime]] = mapped_column(DateTime)
    execution_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    user = relationship("User")
    report = relationship("Report", back_populates="scheduled_reports")
