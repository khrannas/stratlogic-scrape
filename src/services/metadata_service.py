from typing import List
from sqlalchemy.orm import Session
import uuid

from src.core.models.metadata import MetadataTag
from src.api.schemas import metadata_schemas

class MetadataService:
    def add_tag_to_artifact(self, db: Session, *, tag_in: metadata_schemas.MetadataTagCreate) -> MetadataTag:
        db_tag = MetadataTag(**tag_in.dict())
        db.add(db_tag)
        db.commit()
        db.refresh(db_tag)
        return db_tag

    def get_tags_for_artifact(self, db: Session, *, artifact_id: uuid.UUID) -> List[MetadataTag]:
        return db.query(MetadataTag).filter(MetadataTag.artifact_id == artifact_id).all()

metadata_service = MetadataService()
