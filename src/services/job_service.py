from typing import List, Optional
from sqlalchemy.orm import Session
import uuid

from src.core.models.job import ScrapingJob, JobConfiguration
from src.api.schemas import job_schemas

class JobService:
    def create_job(self, db: Session, *, job_in: job_schemas.ScrapingJobCreate) -> ScrapingJob:
        db_job = ScrapingJob(
            user_id=job_in.user_id,
            job_type=job_in.job_type,
            keywords=job_in.keywords,
            max_results=job_in.max_results,
            status=job_in.status,
            progress=job_in.progress,
            total_items=job_in.total_items,
            completed_items=job_in.completed_items,
            error_message=job_in.error_message,
        )
        for config in job_in.configurations:
            db_job.configurations.append(JobConfiguration(**config.dict()))

        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job

    def get_job(self, db: Session, *, job_id: uuid.UUID) -> Optional[ScrapingJob]:
        return db.query(ScrapingJob).filter(ScrapingJob.id == job_id).first()

    def get_jobs_by_user(self, db: Session, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[ScrapingJob]:
        return db.query(ScrapingJob).filter(ScrapingJob.user_id == user_id).offset(skip).limit(limit).all()

    def update_job(self, db: Session, *, db_obj: ScrapingJob, obj_in: job_schemas.ScrapingJobUpdate) -> ScrapingJob:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove_job(self, db: Session, *, job_id: uuid.UUID) -> ScrapingJob:
        db_obj = db.query(ScrapingJob).get(job_id)
        db.delete(db_obj)
        db.commit()
        return db_obj

    def get_jobs(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ScrapingJob]:
        return db.query(ScrapingJob).offset(skip).limit(limit).all()

    def delete_job(self, db: Session, *, job_id: uuid.UUID) -> ScrapingJob:
        return self.remove_job(db, job_id=job_id)

job_service = JobService()
