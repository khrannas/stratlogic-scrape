"""
Job management routes for StratLogic Scraping System.

This module provides endpoints for scraping job management,
job monitoring, and job configuration.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.models import User, ScrapingJob, JobStatus, JobConfiguration
from ...core.repositories.job import JobRepository
from ..dependencies import get_db, get_current_active_user, require_role
from ..middleware import log_request, log_error
from ...core.utils import get_logger

# Get logger
logger = get_logger(__name__)

# Create router
router = APIRouter()


# Pydantic models for job requests/responses
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List as ListType


class JobBase(BaseModel):
    """Base job model."""
    title: str = Field(..., min_length=1, max_length=255, description="Job title")
    description: Optional[str] = Field(None, description="Job description")
    job_type: str = Field(..., description="Job type (web, paper, government)")
    keywords: Optional[ListType[str]] = Field(None, description="Search keywords")
    urls: Optional[ListType[str]] = Field(None, description="Target URLs")
    search_queries: Optional[ListType[str]] = Field(None, description="Search queries")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Job configuration")


class JobCreate(JobBase):
    """Job creation request model."""
    pass


class JobUpdate(BaseModel):
    """Job update request model."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    keywords: Optional[ListType[str]] = None
    urls: Optional[ListType[str]] = None
    search_queries: Optional[ListType[str]] = None
    configuration: Optional[Dict[str, Any]] = None


class JobResponse(JobBase):
    """Job response model."""
    id: UUID
    user_id: UUID
    status: JobStatus
    progress: int
    total_items: int
    processed_items: int
    failed_items: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class JobStats(BaseModel):
    """Job statistics model."""
    total_jobs: int
    pending_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    cancelled_jobs: int
    average_duration: Optional[float]  # seconds
    success_rate: float  # percentage


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> JobResponse:
    """
    Create a new scraping job.
    
    Args:
        job_data: Job creation data
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        JobResponse: Created job data
        
    Raises:
        HTTPException: If job creation fails
    """
    log_request(request, "Create job", user_id=str(current_user.id), job_type=job_data.job_type)
    
    try:
        job_repo = JobRepository(db)
        
        # Create job
        job = ScrapingJob(
            user_id=current_user.id,
            job_type=job_data.job_type,
            title=job_data.title,
            description=job_data.description,
            keywords=job_data.keywords,
            urls=job_data.urls,
            search_queries=job_data.search_queries,
            configuration=job_data.configuration,
            status=JobStatus.PENDING,
            progress=0,
            total_items=0,
            processed_items=0,
            failed_items=0
        )
        
        # Save job to database
        await job_repo.create(job)
        
        log_request(request, "Job created successfully", job_id=str(job.id), user_id=str(current_user.id))
        
        return JobResponse.from_orm(job)
        
    except Exception as e:
        log_error(request, "Job creation failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job creation failed"
        )


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of jobs to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of jobs to return"),
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    search: Optional[str] = Query(None, description="Search term for job title"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[JobResponse]:
    """
    List user's scraping jobs.
    
    Args:
        request: FastAPI request object
        skip: Number of jobs to skip
        limit: Maximum number of jobs to return
        status: Filter by job status
        job_type: Filter by job type
        search: Search term for job title
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[JobResponse]: List of jobs
    """
    log_request(request, "List jobs", user_id=str(current_user.id))
    
    try:
        job_repo = JobRepository(db)
        jobs = await job_repo.list_by_user(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            status=status,
            job_type=job_type,
            search=search
        )
        
        return [JobResponse.from_orm(job) for job in jobs]
        
    except Exception as e:
        log_error(request, "Failed to list jobs", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list jobs"
        )


@router.get("/stats", response_model=JobStats)
async def get_job_stats(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> JobStats:
    """
    Get user's job statistics.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        JobStats: Job statistics
    """
    log_request(request, "Get job stats", user_id=str(current_user.id))
    
    try:
        job_repo = JobRepository(db)
        stats = await job_repo.get_user_stats(current_user.id)
        
        return JobStats(**stats)
        
    except Exception as e:
        log_error(request, "Failed to get job stats", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job statistics"
        )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> JobResponse:
    """
    Get job by ID.
    
    Args:
        job_id: Job ID
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        JobResponse: Job data
        
    Raises:
        HTTPException: If job not found or access denied
    """
    log_request(request, "Get job", job_id=str(job_id), user_id=str(current_user.id))
    
    try:
        job_repo = JobRepository(db)
        job = await job_repo.get_by_id(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check if user owns the job or is admin
        if job.user_id != current_user.id and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return JobResponse.from_orm(job)
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(request, "Failed to get job", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job"
        )


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: UUID,
    job_data: JobUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> JobResponse:
    """
    Update job (only if not running or completed).
    
    Args:
        job_id: Job ID
        job_data: Job update data
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        JobResponse: Updated job data
        
    Raises:
        HTTPException: If update fails
    """
    log_request(request, "Update job", job_id=str(job_id), user_id=str(current_user.id))
    
    try:
        job_repo = JobRepository(db)
        job = await job_repo.get_by_id(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check if user owns the job or is admin
        if job.user_id != current_user.id and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if job can be updated
        if job.status in [JobStatus.RUNNING, JobStatus.COMPLETED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update running or completed job"
            )
        
        # Update job fields
        if job_data.title is not None:
            job.title = job_data.title
        if job_data.description is not None:
            job.description = job_data.description
        if job_data.keywords is not None:
            job.keywords = job_data.keywords
        if job_data.urls is not None:
            job.urls = job_data.urls
        if job_data.search_queries is not None:
            job.search_queries = job_data.search_queries
        if job_data.configuration is not None:
            job.configuration = job_data.configuration
        
        # Save changes
        await job_repo.update(job)
        
        log_request(request, "Job updated successfully", job_id=str(job_id), user_id=str(current_user.id))
        
        return JobResponse.from_orm(job)
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(request, "Job update failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job update failed"
        )


@router.delete("/{job_id}")
async def delete_job(
    job_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete job (only if not running).
    
    Args:
        job_id: Job ID
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Deletion confirmation
        
    Raises:
        HTTPException: If deletion fails
    """
    log_request(request, "Delete job", job_id=str(job_id), user_id=str(current_user.id))
    
    try:
        job_repo = JobRepository(db)
        job = await job_repo.get_by_id(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check if user owns the job or is admin
        if job.user_id != current_user.id and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if job can be deleted
        if job.status == JobStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete running job"
            )
        
        # Delete job
        await job_repo.delete(job_id)
        
        log_request(request, "Job deleted successfully", job_id=str(job_id), user_id=str(current_user.id))
        
        return {"message": "Job deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(request, "Job deletion failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job deletion failed"
        )


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a running job.
    
    Args:
        job_id: Job ID
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Cancellation confirmation
        
    Raises:
        HTTPException: If cancellation fails
    """
    log_request(request, "Cancel job", job_id=str(job_id), user_id=str(current_user.id))
    
    try:
        job_repo = JobRepository(db)
        job = await job_repo.get_by_id(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check if user owns the job or is admin
        if job.user_id != current_user.id and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if job can be cancelled
        if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job cannot be cancelled"
            )
        
        # Cancel job
        job.status = JobStatus.CANCELLED
        await job_repo.update(job)
        
        log_request(request, "Job cancelled successfully", job_id=str(job_id), user_id=str(current_user.id))
        
        return {"message": "Job cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(request, "Job cancellation failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job cancellation failed"
        )


@router.post("/{job_id}/retry")
async def retry_job(
    job_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retry a failed job.
    
    Args:
        job_id: Job ID
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Retry confirmation
        
    Raises:
        HTTPException: If retry fails
    """
    log_request(request, "Retry job", job_id=str(job_id), user_id=str(current_user.id))
    
    try:
        job_repo = JobRepository(db)
        job = await job_repo.get_by_id(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check if user owns the job or is admin
        if job.user_id != current_user.id and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if job can be retried
        if job.status != JobStatus.FAILED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only failed jobs can be retried"
            )
        
        # Reset job for retry
        job.status = JobStatus.PENDING
        job.progress = 0
        job.processed_items = 0
        job.failed_items = 0
        job.error_message = None
        job.started_at = None
        job.completed_at = None
        
        await job_repo.update(job)
        
        log_request(request, "Job retry initiated", job_id=str(job_id), user_id=str(current_user.id))
        
        return {"message": "Job retry initiated"}
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(request, "Job retry failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job retry failed"
        )
