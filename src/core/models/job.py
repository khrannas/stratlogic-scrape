import uuid
from sqlalchemy import Column, String, Integer, DateTime, UUID, Text, ARRAY, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base

class ScrapingJob(Base):
    __tablename__ = "scraping_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_type = Column(String(50), nullable=False)
    keywords = Column(ARRAY(Text), nullable=False)
    max_results = Column(Integer, default=10)
    expanded_keywords = Column(ARRAY(Text))
    status = Column(String(20), default="pending", index=True)
    progress = Column(Integer, default=0)
    total_items = Column(Integer, default=0)
    completed_items = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="scraping_jobs")
    artifacts = relationship("Artifact", back_populates="job", cascade="all, delete-orphan")
    configurations = relationship("JobConfiguration", back_populates="job", cascade="all, delete-orphan")

class JobConfiguration(Base):
    __tablename__ = "job_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scraping_jobs.id"), nullable=False)
    config_key = Column(String(100), nullable=False)
    config_value = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    job = relationship("ScrapingJob", back_populates="configurations")
