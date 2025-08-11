"""
Job repository for database operations.

This module provides the JobRepository class for scraping job-related database operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc, select
from datetime import datetime, timezone

from .base import BaseRepository
from ..models import ScrapingJob, JobStatus
from ..utils import get_logger

logger = get_logger(__name__)


class JobRepository(BaseRepository[ScrapingJob, dict, dict]):
    """Repository for ScrapingJob model operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize JobRepository with database session."""
        super().__init__(ScrapingJob, db)
        self.db = db
    
    async def get_by_id(self, job_id: UUID) -> Optional[ScrapingJob]:
        """
        Get job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            ScrapingJob instance or None
        """
        try:
            result = await self.db.execute(
                select(ScrapingJob).where(ScrapingJob.id == job_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting job by ID {job_id}: {e}")
            return None
    
    async def create(self, job: ScrapingJob) -> ScrapingJob:
        """
        Create a new scraping job.
        
        Args:
            job: Job instance to create
            
        Returns:
            Created job instance
        """
        try:
            self.db.add(job)
            await self.db.commit()
            await self.db.refresh(job)
            return job
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating job: {e}")
            raise
    
    async def update(self, job: ScrapingJob) -> ScrapingJob:
        """
        Update job.
        
        Args:
            job: Job instance to update
            
        Returns:
            Updated job instance
        """
        try:
            self.db.add(job)
            await self.db.commit()
            await self.db.refresh(job)
            return job
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating job: {e}")
            raise
    
    async def delete(self, job_id: UUID) -> bool:
        """
        Delete job.
        
        Args:
            job_id: Job ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            job = await self.get_by_id(job_id)
            if job:
                await self.db.delete(job)
                await self.db.commit()
                return True
            return False
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting job {job_id}: {e}")
            return False
    
    async def list_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[JobStatus] = None,
        job_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[ScrapingJob]:
        """
        List jobs by user with filters.
        
        Args:
            user_id: User ID to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by job status
            job_type: Filter by job type
            search: Search term for job title or description
            
        Returns:
            List of jobs for the user
        """
        try:
            query = select(ScrapingJob).where(ScrapingJob.user_id == user_id)
            
            # Apply filters
            if status:
                query = query.where(ScrapingJob.status == status)
            
            if job_type:
                query = query.where(ScrapingJob.job_type == job_type)
            
            if search:
                search_pattern = f"%{search}%"
                query = query.where(
                    or_(
                        ScrapingJob.title.ilike(search_pattern),
                        ScrapingJob.description.ilike(search_pattern)
                    )
                )
            
            # Apply ordering and pagination
            query = query.order_by(desc(ScrapingJob.created_at)).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error listing jobs for user {user_id}: {e}")
            return []
    
    async def get_user_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get job statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with job statistics
        """
        try:
            # Get total jobs
            total_jobs = await self.db.execute(
                select(ScrapingJob).where(ScrapingJob.user_id == user_id)
            )
            total_jobs = len(total_jobs.scalars().all())
            
            # Get jobs by status
            pending_jobs = await self.db.execute(
                select(ScrapingJob).where(
                    and_(ScrapingJob.user_id == user_id, ScrapingJob.status == JobStatus.PENDING)
                )
            )
            pending_jobs = len(pending_jobs.scalars().all())
            
            running_jobs = await self.db.execute(
                select(ScrapingJob).where(
                    and_(ScrapingJob.user_id == user_id, ScrapingJob.status == JobStatus.RUNNING)
                )
            )
            running_jobs = len(running_jobs.scalars().all())
            
            completed_jobs = await self.db.execute(
                select(ScrapingJob).where(
                    and_(ScrapingJob.user_id == user_id, ScrapingJob.status == JobStatus.COMPLETED)
                )
            )
            completed_jobs = len(completed_jobs.scalars().all())
            
            failed_jobs = await self.db.execute(
                select(ScrapingJob).where(
                    and_(ScrapingJob.user_id == user_id, ScrapingJob.status == JobStatus.FAILED)
                )
            )
            failed_jobs = len(failed_jobs.scalars().all())
            
            cancelled_jobs = await self.db.execute(
                select(ScrapingJob).where(
                    and_(ScrapingJob.user_id == user_id, ScrapingJob.status == JobStatus.CANCELLED)
                )
            )
            cancelled_jobs = len(cancelled_jobs.scalars().all())
            
            # Calculate average duration for completed jobs
            completed_jobs_with_duration = await self.db.execute(
                select(ScrapingJob).where(
                    and_(
                        ScrapingJob.user_id == user_id,
                        ScrapingJob.status == JobStatus.COMPLETED,
                        ScrapingJob.started_at.isnot(None),
                        ScrapingJob.completed_at.isnot(None)
                    )
                )
            )
            completed_jobs_with_duration = completed_jobs_with_duration.scalars().all()
            
            total_duration = 0
            for job in completed_jobs_with_duration:
                if job.started_at and job.completed_at:
                    duration = (job.completed_at - job.started_at).total_seconds()
                    total_duration += duration
            
            average_duration = total_duration / len(completed_jobs_with_duration) if completed_jobs_with_duration else None
            
            # Calculate success rate
            total_finished = completed_jobs + failed_jobs + cancelled_jobs
            success_rate = (completed_jobs / total_finished * 100) if total_finished > 0 else 0
            
            return {
                "total_jobs": total_jobs,
                "pending_jobs": pending_jobs,
                "running_jobs": running_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "cancelled_jobs": cancelled_jobs,
                "average_duration": average_duration,
                "success_rate": success_rate
            }
            
        except Exception as e:
            logger.error(f"Error getting job stats for user {user_id}: {e}")
            return {
                "total_jobs": 0,
                "pending_jobs": 0,
                "running_jobs": 0,
                "completed_jobs": 0,
                "failed_jobs": 0,
                "cancelled_jobs": 0,
                "average_duration": None,
                "success_rate": 0.0
            }
