import uuid
from sqlalchemy import Column, String, DateTime, UUID, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base

class MetadataTag(Base):
    __tablename__ = "metadata_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False)
    tag_type = Column(String(50), nullable=False)
    tag_key = Column(String(100), nullable=False, index=True)
    tag_value = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    artifact = relationship("Artifact", back_populates="metadata_tags")
