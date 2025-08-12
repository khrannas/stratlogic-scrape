from typing import List, Optional
from sqlalchemy.orm import Session
import uuid

from src.core.models.artifact import Artifact, ContentExtraction
from src.api.schemas import artifact_schemas

class ArtifactService:
    def create_artifact(self, db: Session, *, artifact_in: artifact_schemas.ArtifactCreate) -> Artifact:
        db_artifact = Artifact(**artifact_in.dict())
        db.add(db_artifact)
        db.commit()
        db.refresh(db_artifact)
        return db_artifact

    def get_artifact(self, db: Session, *, artifact_id: uuid.UUID) -> Optional[Artifact]:
        return db.query(Artifact).filter(Artifact.id == artifact_id).first()

    def get_artifacts_by_job(self, db: Session, *, job_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Artifact]:
        return db.query(Artifact).filter(Artifact.job_id == job_id).offset(skip).limit(limit).all()

    def update_artifact(self, db: Session, *, db_obj: Artifact, obj_in: artifact_schemas.ArtifactUpdate) -> Artifact:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove_artifact(self, db: Session, *, artifact_id: uuid.UUID) -> Artifact:
        db_obj = db.query(Artifact).get(artifact_id)
        db.delete(db_obj)
        db.commit()
        return db_obj

    def add_extraction_to_artifact(self, db: Session, *, artifact_id: uuid.UUID, extraction_in: artifact_schemas.ContentExtractionCreate) -> ContentExtraction:
        db_extraction = ContentExtraction(
            artifact_id=artifact_id,
            **extraction_in.dict()
        )
        db.add(db_extraction)
        db.commit()
        db.refresh(db_extraction)
        return db_extraction

    def get_artifacts(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Artifact]:
        return db.query(Artifact).offset(skip).limit(limit).all()

    def delete_artifact(self, db: Session, *, artifact_id: uuid.UUID) -> Artifact:
        return self.remove_artifact(db, artifact_id=artifact_id)

    def upload_artifact_file(self, db: Session, *, artifact_id: uuid.UUID, file) -> str:
        # This would integrate with the storage service
        # For now, return a placeholder URL
        return f"/storage/artifacts/{artifact_id}/{file.filename}"

    def get_download_url(self, db: Session, *, artifact_id: uuid.UUID) -> str:
        # This would integrate with the storage service
        # For now, return a placeholder URL
        return f"/storage/artifacts/{artifact_id}/download"


artifact_service = ArtifactService()
