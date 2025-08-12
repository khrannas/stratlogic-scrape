from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.api.schemas import job_schemas
from src.services import job_service
from src.core.database import get_db

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)

@router.post("/", response_model=job_schemas.Job)
def create_job(
    *,
    db: Session = Depends(get_db),
    job_in: job_schemas.JobCreate,
):
    """
    Create new scraping job.
    """
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
    Get job status.
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
