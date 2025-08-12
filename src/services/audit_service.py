from typing import List
from sqlalchemy.orm import Session
import uuid

from src.core.models.audit import AuditLog
from src.api.schemas import audit_schemas

class AuditService:
    def create_log(self, db: Session, *, log_in: audit_schemas.AuditLogCreate) -> AuditLog:
        db_log = AuditLog(**log_in.dict())
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log

    def get_logs_by_user(self, db: Session, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        return db.query(AuditLog).filter(AuditLog.user_id == user_id).offset(skip).limit(limit).all()

audit_service = AuditService()
