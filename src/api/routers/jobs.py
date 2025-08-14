from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.api.schemas import job_schemas
from src.services.job_service import job_service
from src.core.database import get_db
from src.api.dependencies.auth import get_current_active_user
from src.core.models.user import User

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)

@router.post("/", response_model=job_schemas.Job)
def create_job(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    job_in: job_schemas.JobCreate,
):
    """
    Create a new web scraping job.

    This endpoint initiates a new scraping job that will collect data from the specified
    source. The job will be created with an initial status and can be monitored for progress.

    **Request Body:**
    - `job_type`: Type of scraper to use (web_scraper, paper_scraper, government_scraper)
    - `keywords`: List of keywords to search for
    - `max_results`: Maximum number of results to return (optional, default: 10)
    - `configurations`: Optional job configurations

    **Returns:**
    - Job object with generated ID and initial status

    **Raises:**
    - 422: If request body validation fails
    - 401: If authentication fails

    **Example:**
    ```json
    {
        "job_type": "paper_scraper",
        "keywords": ["health insurance"],
        "max_results": 10
    }
    ```
    """
    # Set the user_id from the authenticated user
    job_in.user_id = current_user.id
    job = job_service.create_job(db, job_in=job_in)
    return job

@router.get("/", response_model=List[job_schemas.Job])
def read_jobs(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve scraping jobs.
    """
    jobs = job_service.get_jobs(db, skip=skip, limit=limit)
    return jobs

@router.get("/{job_id}", response_model=job_schemas.Job)
def read_job(
    *,
    db: Session = Depends(get_db),
    job_id: str,
):
    """
    Get job by ID.
    """
    job = job_service.get_job(db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.put("/{job_id}", response_model=job_schemas.Job)
def update_job(
    *,
    db: Session = Depends(get_db),
    job_id: str,
    job_in: job_schemas.JobUpdate,
):
    """
    Update job.
    """
    job = job_service.get_job(db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job = job_service.update_job(db, db_obj=job, obj_in=job_in)
    return job

@router.delete("/{job_id}")
def delete_job(
    *,
    db: Session = Depends(get_db),
    job_id: str,
):
    """
    Delete job.
    """
    job = job_service.get_job(db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job_service.delete_job(db, job_id=job_id)
    return {"message": "Job deleted successfully"}

@router.get("/{job_id}/status", response_model=job_schemas.JobStatus)
def get_job_status(
    *,
    db: Session = Depends(get_db),
    job_id: str,
):
    """
    Get the current status and progress of a scraping job.

    This endpoint returns detailed status information about a specific job, including
    its current state, progress percentage, and timestamps.

    **Path Parameters:**
    - `job_id`: Unique identifier of the job (UUID format)

    **Returns:**
    - Job status object with current state and progress

    **Raises:**
    - 404: If job with the specified ID is not found

    **Example:**
    ```
    GET /api/v1/jobs/123e4567-e89b-12d3-a456-426614174000/status
    ```

    **Response:**
    ```json
    {
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "running",
        "progress": 75.5,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:45:00Z"
    }
    ```
    """
    job = job_service.get_job(db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_schemas.JobStatus(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        created_at=job.created_at,
        updated_at=job.updated_at
    )
