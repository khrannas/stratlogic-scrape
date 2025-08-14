from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
import uuid

from src.core.models.artifact import Artifact, ContentExtraction
from src.core.models.job import ScrapingJob
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

    def get_artifacts(
        self,
        db: Session,
        *,
        search: Optional[str] = None,
        source_type: Optional[str] = None,
        job_id: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> List[Artifact]:
        """
        Get artifacts with filtering and pagination.

        Args:
            db: Database session
            search: Search term to filter by title or content
            source_type: Filter by source type (web, paper, government)
            job_id: Filter by job ID
            page: Page number (1-based)
            size: Number of items per page
        """
        query = db.query(Artifact).join(ScrapingJob, Artifact.job_id == ScrapingJob.id)

        # Apply job_id filter
        if job_id:
            try:
                job_uuid = uuid.UUID(job_id)
                query = query.filter(Artifact.job_id == job_uuid)
            except ValueError:
                # If job_id is not a valid UUID, return empty list
                return []

        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Artifact.title.ilike(search_term),
                    # Note: Content is not stored in the database, it's in MinIO
                    # We can only search by title for now
                )
            )

        # Apply source type filter (map to job_type)
        if source_type:
            # Map frontend source_type to job_type
            source_type_mapping = {
                'web': 'web_scraper',
                'paper': 'paper_scraper',
                'government': 'government_scraper'
            }
            job_type = source_type_mapping.get(source_type, source_type)
            query = query.filter(ScrapingJob.job_type == job_type)

        # Apply pagination
        skip = (page - 1) * size
        query = query.offset(skip).limit(size)

        return query.all()

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
