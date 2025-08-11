import uuid
from sqlalchemy import Column, String, BigInteger, Boolean, DateTime, UUID, Text, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base

class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scraping_jobs.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    artifact_type = Column(String(50), nullable=False)
    source_url = Column(Text, index=True)
    title = Column(String(500))
    content_hash = Column(String(64), nullable=False, index=True)
    file_size = Column(BigInteger)
    mime_type = Column(String(100))
    minio_path = Column(String(500), nullable=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    job = relationship("ScrapingJob", back_populates="artifacts")
    user = relationship("User", back_populates="artifacts")
    metadata_tags = relationship("MetadataTag", back_populates="artifact", cascade="all, delete-orphan")
    extractions = relationship("ContentExtraction", back_populates="artifact", cascade="all, delete-orphan")

class ContentExtraction(Base):
    __tablename__ = "content_extractions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False)
    extraction_type = Column(String(50), nullable=False)
    extracted_data = Column(JSONB)
    confidence_score = Column(DECIMAL(3, 2))
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    artifact = relationship("Artifact", back_populates="extractions")
