"""
Search and content analysis models for the StratLogic Scraping System.

This module contains SQLAlchemy models for search indexing, semantic embeddings,
content analysis, and search query tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Float, Integer, String, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TSVECTOR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..models import Base, TimestampMixin


class SearchType(str, Enum):
    """Search type enumeration."""
    FULL_TEXT = "full_text"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class AnalysisType(str, Enum):
    """Content analysis type enumeration."""
    ENTITY_EXTRACTION = "entity_extraction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    TOPIC_MODELING = "topic_modeling"
    KEYWORD_EXTRACTION = "keyword_extraction"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"


class SearchIndex(Base, TimestampMixin):
    """Search index for full-text search capabilities."""
    
    __tablename__ = "search_index"
    
    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    artifact_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False, index=True)
    content_text: str = Column(Text, nullable=False)
    search_vector: TSVECTOR = Column(TSVECTOR, nullable=False)
    title: str = Column(String(500), nullable=False)
    description: Optional[str] = Column(Text)
    keywords: Optional[str] = Column(Text)  # JSON string of keywords
    tags: Optional[str] = Column(Text)  # JSON string of tags
    language: str = Column(String(10), default="en")
    is_active: bool = Column(Integer, default=1, nullable=False)  # 0 or 1 for boolean
    
    # Relationships
    artifact = relationship("Artifact", back_populates="search_index")
    
    # Full-text search index
    __table_args__ = (
        Index('idx_search_vector', 'search_vector', postgresql_using='gin'),
        Index('idx_artifact_id', 'artifact_id'),
        Index('idx_is_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<SearchIndex(id={self.id}, artifact_id={self.artifact_id}, title='{self.title}')>"


class SearchEmbedding(Base, TimestampMixin):
    """Semantic search embeddings for vector similarity search."""
    
    __tablename__ = "search_embeddings"
    
    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    artifact_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False, index=True)
    model_name: str = Column(String(100), nullable=False)  # e.g., 'all-MiniLM-L6-v2'
    embedding_vector: str = Column(Text, nullable=False)  # JSON string of embedding
    content_hash: str = Column(String(64), nullable=False, index=True)  # Hash of content used for embedding
    is_active: bool = Column(Integer, default=1, nullable=False)  # 0 or 1 for boolean
    
    # Relationships
    artifact = relationship("Artifact", back_populates="search_embeddings")
    
    # Indexes
    __table_args__ = (
        Index('idx_artifact_model', 'artifact_id', 'model_name'),
        Index('idx_content_hash', 'content_hash'),
        Index('idx_is_active_embedding', 'is_active'),
    )
    
    def __repr__(self):
        return f"<SearchEmbedding(id={self.id}, artifact_id={self.artifact_id}, model='{self.model_name}')>"


class ContentAnalysis(Base, TimestampMixin):
    """Content analysis results from langchain processing."""
    
    __tablename__ = "content_analysis"
    
    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    artifact_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False, index=True)
    analysis_type: AnalysisType = Column(SQLEnum(AnalysisType), nullable=False, index=True)
    analysis_data: str = Column(Text, nullable=False)  # JSON string of analysis results
    confidence_score: Optional[float] = Column(Float)
    model_used: str = Column(String(100), nullable=False)  # e.g., 'gpt-4', 'spacy', etc.
    processing_time_ms: Optional[float] = Column(Float)
    is_active: bool = Column(Integer, default=1, nullable=False)  # 0 or 1 for boolean
    
    # Relationships
    artifact = relationship("Artifact", back_populates="content_analyses")
    
    # Indexes
    __table_args__ = (
        Index('idx_artifact_analysis_type', 'artifact_id', 'analysis_type'),
        Index('idx_analysis_type', 'analysis_type'),
        Index('idx_is_active_analysis', 'is_active'),
    )
    
    def __repr__(self):
        return f"<ContentAnalysis(id={self.id}, artifact_id={self.artifact_id}, type='{self.analysis_type}')>"


class SearchQuery(Base, TimestampMixin):
    """Search query tracking for analytics."""
    
    __tablename__ = "search_queries"
    
    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: UUID = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    query_text: str = Column(Text, nullable=False)
    search_type: SearchType = Column(SQLEnum(SearchType), nullable=False, index=True)
    filters: Optional[str] = Column(Text)  # JSON string of search filters
    results_count: int = Column(Integer, default=0, nullable=False)
    processing_time_ms: Optional[float] = Column(Float)
    ip_address: Optional[str] = Column(String(45))  # IPv6 compatible
    user_agent: Optional[str] = Column(Text)
    session_id: Optional[str] = Column(String(100))
    
    # Relationships
    user = relationship("User", back_populates="search_queries")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_search_type', 'user_id', 'search_type'),
        Index('idx_search_type', 'search_type'),
        Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<SearchQuery(id={self.id}, user_id={self.user_id}, query='{self.query_text[:50]}...')>"


# Add relationships to existing models
from ..models import User, Artifact

# Add to User model
User.search_queries = relationship("SearchQuery", back_populates="user", cascade="all, delete-orphan")

# Add to Artifact model
Artifact.search_index = relationship("SearchIndex", back_populates="artifact", uselist=False, cascade="all, delete-orphan")
Artifact.search_embeddings = relationship("SearchEmbedding", back_populates="artifact", cascade="all, delete-orphan")
Artifact.content_analyses = relationship("ContentAnalysis", back_populates="artifact", cascade="all, delete-orphan")
