"""
Job repository for database operations.

This module provides the JobRepository class for scraping job-related database operations.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime, timezone

from .base import BaseRepository
from ..models import ScrapingJob, JobStatus
from ..utils import get_logger

logger = get_logger(__name__)


class JobRepository(BaseRepository[ScrapingJob, dict, dict]):
    """Repository for ScrapingJob model operations."""
    
    def __init__(self):
        """Initialize JobRepository."""
        super().__init__(ScrapingJob)
    
    def get_jobs_by_user(
        self, 
        db: Session, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ScrapingJob]:
        """
        Get jobs by user ID.
        
        Args:
            db: Database session
            user_id: User ID to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of jobs for the user
        """
        return self.get_multi_by_field(db, "user_id", user_id, skip, limit)
    
    def get_jobs_by_status(
        self, 
        db: Session, 
        status: JobStatus, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ScrapingJob]:
        """
        Get jobs by status.
        
        Args:
            db: Database session
            status: Job status to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of jobs with specified status
        """
        try:
            return db.query(ScrapingJob).filter(
                ScrapingJob.status == status
            ).order_by(desc(ScrapingJob.created_at)).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting jobs by status {status}: {e}")
            return []
    
    def get_jobs_by_type(
        self, 
        db: Session, 
        job_type: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ScrapingJob]:
        """
        Get jobs by type.
        
        Args:
            db: Database session
            job_type: Job type to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of jobs with specified type
        """
        try:
            return db.query(ScrapingJob).filter(
                ScrapingJob.job_type == job_type
            ).order_by(desc(ScrapingJob.created_at)).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting jobs by type {job_type}: {e}")
            return []
    
    def get_running_jobs(self, db: Session) -> List[ScrapingJob]:
        """
        Get all running jobs.
        
        Args:
            db: Database session
            
        Returns:
            List of running jobs
        """
        return self.get_jobs_by_status(db, JobStatus.RUNNING)
    
    def get_pending_jobs(self, db: Session) -> List[ScrapingJob]:
        """
        Get all pending jobs.
        
        Args:
            db: Database session
            
        Returns:
            List of pending jobs
        """
        return self.get_jobs_by_status(db, JobStatus.PENDING)
    
    def get_completed_jobs(self, db: Session, skip: int = 0, limit: int = 100) -> List[ScrapingJob]:
        """
        Get completed jobs.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of completed jobs
        """
        try:
            return db.query(ScrapingJob).filter(
                ScrapingJob.status == JobStatus.COMPLETED
            ).order_by(desc(ScrapingJob.completed_at)).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting completed jobs: {e}")
            return []
    
    def get_failed_jobs(self, db: Session, skip: int = 0, limit: int = 100) -> List[ScrapingJob]:
        """
        Get failed jobs.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of failed jobs
        """
        try:
            return db.query(ScrapingJob).filter(
                ScrapingJob.status == JobStatus.FAILED
            ).order_by(desc(ScrapingJob.updated_at)).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting failed jobs: {e}")
            return []
    
    def create_job(self, db: Session, job_data: dict) -> Optional[ScrapingJob]:
        """
        Create a new scraping job.
        
        Args:
            db: Database session
            job_data: Job data dictionary
            
        Returns:
            Created job instance or None
        """
        try:
            job = ScrapingJob(**job_data)
            db.add(job)
            db.commit()
            db.refresh(job)
            return job
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating job: {e}")
            return None
    
    def update_job_status(
        self, 
        db: Session, 
        job_id: str, 
        status: JobStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update job status.
        
        Args:
            db: Database session
            job_id: Job ID to update
            status: New status
            error_message: Error message (for failed jobs)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            job = self.get(db, job_id)
            if job:
                job.status = status
                job.error_message = error_message
                
                if status == JobStatus.RUNNING:
                    job.started_at = datetime.now(timezone.utc)
                elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    job.completed_at = datetime.now(timezone.utc)
                
                db.add(job)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating job status {job_id} to {status}: {e}")
            return False
    
    def update_job_progress(
        self, 
        db: Session, 
        job_id: str, 
        processed: int, 
        total: int, 
        failed: int = 0
    ) -> bool:
        """
        Update job progress.
        
        Args:
            db: Database session
            job_id: Job ID to update
            processed: Number of processed items
            total: Total number of items
            failed: Number of failed items
            
        Returns:
            True if successful, False otherwise
        """
        try:
            job = self.get(db, job_id)
            if job:
                job.update_progress(processed, total, failed)
                db.add(job)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating job progress {job_id}: {e}")
            return False
    
    def cancel_job(self, db: Session, job_id: str) -> bool:
        """
        Cancel a job.
        
        Args:
            db: Database session
            job_id: Job ID to cancel
            
        Returns:
            True if successful, False otherwise
        """
        return self.update_job_status(db, job_id, JobStatus.CANCELLED)
    
    def retry_job(self, db: Session, job_id: str) -> bool:
        """
        Retry a failed job.
        
        Args:
            db: Database session
            job_id: Job ID to retry
            
        Returns:
            True if successful, False otherwise
        """
        try:
            job = self.get(db, job_id)
            if job and job.status == JobStatus.FAILED:
                job.status = JobStatus.PENDING
                job.error_message = None
                job.started_at = None
                job.completed_at = None
                job.progress = 0
                job.processed_items = 0
                job.failed_items = 0
                
                db.add(job)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error retrying job {job_id}: {e}")
            return False
    
    def search_jobs(
        self, 
        db: Session, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ScrapingJob]:
        """
        Search jobs by title or description.
        
        Args:
            db: Database session
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching jobs
        """
        try:
            search_pattern = f"%{search_term}%"
            return db.query(ScrapingJob).filter(
                or_(
                    ScrapingJob.title.ilike(search_pattern),
                    ScrapingJob.description.ilike(search_pattern)
                )
            ).order_by(desc(ScrapingJob.created_at)).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error searching jobs with term '{search_term}': {e}")
            return []
    
    def get_job_stats(self, db: Session, user_id: Optional[str] = None) -> dict:
        """
        Get job statistics.
        
        Args:
            db: Database session
            user_id: Optional user ID to filter by
            
        Returns:
            Dictionary with job statistics
        """
        try:
            query = db.query(ScrapingJob)
            if user_id:
                query = query.filter(ScrapingJob.user_id == user_id)
            
            total_jobs = query.count()
            
            status_counts = {}
            for status in JobStatus:
                count = query.filter(ScrapingJob.status == status).count()
                status_counts[status.value] = count
            
            type_counts = {}
            type_query = db.query(ScrapingJob.job_type).distinct()
            if user_id:
                type_query = type_query.filter(ScrapingJob.user_id == user_id)
            
            for job_type in type_query:
                count = query.filter(ScrapingJob.job_type == job_type[0]).count()
                type_counts[job_type[0]] = count
            
            return {
                "total_jobs": total_jobs,
                "status_counts": status_counts,
                "type_counts": type_counts
            }
        except Exception as e:
            logger.error(f"Error getting job stats: {e}")
            return {
                "total_jobs": 0,
                "status_counts": {},
                "type_counts": {}
            }
    
    def cleanup_old_jobs(self, db: Session, days: int = 90) -> int:
        """
        Clean up old completed/failed jobs.
        
        Args:
            db: Database session
            days: Number of days to keep jobs
            
        Returns:
            Number of jobs deleted
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            old_jobs = db.query(ScrapingJob).filter(
                and_(
                    ScrapingJob.status.in_([JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]),
                    ScrapingJob.updated_at < cutoff_date
                )
            ).all()
            
            count = len(old_jobs)
            for job in old_jobs:
                db.delete(job)
            
            db.commit()
            logger.info(f"Cleaned up {count} old jobs")
            return count
        except Exception as e:
            db.rollback()
            logger.error(f"Error cleaning up old jobs: {e}")
            return 0


# Global job repository instance
job_repository = JobRepository()
