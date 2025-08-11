import uuid
from sqlalchemy import Column, String, DateTime, UUID, Text, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base

class SystemConfiguration(Base):
    __tablename__ = "system_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text)
    config_type = Column(String(20), default="string")
    description = Column(Text)
    is_sensitive = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ApiRateLimit(Base):
    __tablename__ = "api_rate_limits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True) # Can be null for global limits
    endpoint = Column(String(100), nullable=False)
    request_count = Column(Integer, default=0)
    window_start = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    # No back-population needed if we don't need to access rate limits from the user model directly
    user = relationship("User")
