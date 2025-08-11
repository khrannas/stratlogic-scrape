import uuid
from sqlalchemy import Column, String, DateTime, UUID, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True) # Can be null for system actions
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(UUID(as_uuid=True))
    details = Column(JSONB)
    ip_address = Column(INET)
    user_agent = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    user = relationship("User", back_populates="audit_logs")
