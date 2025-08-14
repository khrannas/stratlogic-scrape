from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import uuid
import asyncio
from datetime import datetime, UTC

from src.core.models.job import ScrapingJob, JobConfiguration
from src.api.schemas import job_schemas
from src.core.database import get_db

class JobService:
    def create_job(self, db: Session, *, job_in: job_schemas.JobCreate) -> ScrapingJob:
        db_job = ScrapingJob(
            user_id=job_in.user_id,
            job_type=job_in.job_type,
            keywords=job_in.keywords,
            max_results=job_in.max_results,
            expanded_keywords=job_in.expanded_keywords,
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

    async def update_job_status(self, job_id: str, status: str, error_message: str = None):
        """
        Update job status asynchronously

        Args:
            job_id: Job identifier
            status: New status
            error_message: Error message if status is failed
        """
        try:
            # Get database session
            db = next(get_db())

            # Get job
            job = self.get_job(db, job_id=uuid.UUID(job_id))
            if not job:
                return

            # Update status
            job.status = status
            job.updated_at = datetime.now(UTC)

            if status == "running" and not job.started_at:
                job.started_at = datetime.now(UTC)
            elif status in ["completed", "failed"] and not job.completed_at:
                job.completed_at = datetime.now(UTC)

            if error_message:
                job.error_message = error_message

            # Save changes
            db.add(job)
            db.commit()
            db.refresh(job)

        except Exception as e:
            print(f"Error updating job status: {e}")
        finally:
            db.close()

    async def update_job_results(self, job_id: str, results: Dict[str, Any]):
        """
        Update job with results asynchronously

        Args:
            job_id: Job identifier
            results: Results data
        """
        try:
            # Get database session
            db = next(get_db())

            # Get job
            job = self.get_job(db, job_id=uuid.UUID(job_id))
            if not job:
                return

            # Update with results
            if "total_items" in results:
                job.total_items = results["total_items"]
            if "completed_items" in results:
                job.completed_items = results["completed_items"]
            if "progress" in results:
                job.progress = results["progress"]

            job.updated_at = datetime.now(UTC)

            # Save changes
            db.add(job)
            db.commit()
            db.refresh(job)

        except Exception as e:
            print(f"Error updating job results: {e}")
        finally:
            db.close()

    async def update_job_progress(self, job_id: str, progress: int):
        """
        Update job progress asynchronously

        Args:
            job_id: Job identifier
            progress: Progress percentage (0-100)
        """
        try:
            # Get database session
            db = next(get_db())

            # Get job
            job = self.get_job(db, job_id=uuid.UUID(job_id))
            if not job:
                return

            # Update progress
            job.progress = progress
            job.updated_at = datetime.now(UTC)

            # Save changes
            db.add(job)
            db.commit()
            db.refresh(job)

        except Exception as e:
            print(f"Error updating job progress: {e}")
        finally:
            db.close()

job_service = JobService()
