from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid
import asyncio

from src.core.database import get_db
from src.api.dependencies.auth import get_current_user
from src.core.models.user import User
from src.services.job_service import job_service
from src.services.artifact_service import artifact_service
from src.scrapers.web_scraper import web_scraper
from src.api.schemas import job_schemas

router = APIRouter(prefix="/web-scraper", tags=["web-scraper"])

@router.post("/scrape", response_model=Dict[str, Any])
async def start_web_scraping(
    keywords: List[str],
    max_results_per_keyword: int = 10,
    search_engines: List[str] = ["duckduckgo"],
    expand_keywords: bool = True,
    extract_images: bool = True,
    extract_links: bool = True,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a web scraping job
    """
    try:
        # Create job record
        job_data = job_schemas.ScrapingJobCreate(
            user_id=current_user.id,
            job_type="web_scraper",
            keywords=keywords,
            status="pending"
        )

        job = job_service.create_job(db, job_in=job_data)
        job_id = str(job.id)

        # Start scraping in background
        if background_tasks:
            background_tasks.add_task(
                run_web_scraping_job,
                job_id=job_id,
                user_id=str(current_user.id),
                keywords=keywords,
                max_results_per_keyword=max_results_per_keyword,
                search_engines=search_engines,
                expand_keywords=expand_keywords,
                extract_images=extract_images,
                extract_links=extract_links
            )

        return {
            "job_id": job_id,
            "status": "started",
            "message": "Web scraping job started successfully",
            "keywords": keywords,
            "max_results_per_keyword": max_results_per_keyword,
            "search_engines": search_engines
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scraping job: {str(e)}")

@router.get("/job/{job_id}", response_model=job_schemas.ScrapingJob)
async def get_scraping_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get scraping job details
    """
    try:
        job = job_service.get_job(db, job_id=uuid.UUID(job_id))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Check if user owns the job
        if job.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        return job

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job: {str(e)}")

@router.get("/job/{job_id}/artifacts", response_model=List[Dict[str, Any]])
async def get_job_artifacts(
    job_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get artifacts from a scraping job
    """
    try:
        # Verify job exists and user has access
        job = job_service.get_job(db, job_id=uuid.UUID(job_id))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get artifacts
        artifacts = artifact_service.get_artifacts_by_job(
            db, job_id=uuid.UUID(job_id), skip=skip, limit=limit
        )

        return [artifact.__dict__ for artifact in artifacts]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get artifacts: {str(e)}")

@router.get("/stats", response_model=Dict[str, Any])
async def get_scraping_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get web scraper statistics
    """
    try:
        stats = await web_scraper.get_scraping_stats()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.post("/scrape-url", response_model=Dict[str, Any])
async def scrape_single_url(
    url: str,
    extract_images: bool = True,
    extract_links: bool = True,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Scrape a single URL
    """
    try:
        # Create job record
        job_data = job_schemas.ScrapingJobCreate(
            user_id=current_user.id,
            job_type="single_url_scraper",
            keywords=[url],  # Use URL as keyword for job tracking
            status="pending"
        )

        job = job_service.create_job(db, job_in=job_data)
        job_id = str(job.id)

        # Start scraping in background
        if background_tasks:
            background_tasks.add_task(
                run_single_url_scraping,
                job_id=job_id,
                user_id=str(current_user.id),
                url=url,
                extract_images=extract_images,
                extract_links=extract_links
            )

        return {
            "job_id": job_id,
            "status": "started",
            "message": "Single URL scraping started successfully",
            "url": url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start URL scraping: {str(e)}")

@router.post("/test-stealth", response_model=Dict[str, Any])
async def test_stealth_functionality(
    test_url: str = "https://bot.sannysoft.com",
    current_user: User = Depends(get_current_user)
):
    """
    Test stealth functionality against bot detection
    """
    try:
        result = await web_scraper.test_stealth_functionality(test_url)
        return {
            "message": "Stealth test completed",
            "test_url": test_url,
            "result": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stealth test failed: {str(e)}")

async def run_web_scraping_job(
    job_id: str,
    user_id: str,
    keywords: List[str],
    max_results_per_keyword: int = 10,
    search_engines: List[str] = ["duckduckgo"],
    expand_keywords: bool = True,
    extract_images: bool = True,
    extract_links: bool = True
):
    """
    Run web scraping job in background
    """
    try:
        result = await web_scraper.scrape_web_content(
            keywords=keywords,
            job_id=job_id,
            user_id=user_id,
            max_results_per_keyword=max_results_per_keyword,
            search_engines=search_engines,
            expand_keywords=expand_keywords,
            extract_images=extract_images,
            extract_links=extract_links
        )

        print(f"Web scraping job {job_id} completed: {result}")

    except Exception as e:
        print(f"Web scraping job {job_id} failed: {e}")
        # Update job status to failed
        db = next(get_db())
        try:
            job = job_service.get_job(db, job_id=uuid.UUID(job_id))
            if job:
                job.status = "failed"
                job.error_message = str(e)
                db.commit()
        except Exception as update_error:
            print(f"Failed to update job status: {update_error}")

async def run_single_url_scraping(
    job_id: str,
    user_id: str,
    url: str,
    extract_images: bool = True,
    extract_links: bool = True
):
    """
    Run single URL scraping in background
    """
    try:
        result = await web_scraper.scrape_single_url(
            url=url,
            user_id=user_id,
            job_id=job_id,
            extract_images=extract_images,
            extract_links=extract_links
        )

        print(f"Single URL scraping job {job_id} completed: {result}")

    except Exception as e:
        print(f"Single URL scraping job {job_id} failed: {e}")
        # Update job status to failed
        db = next(get_db())
        try:
            job = job_service.get_job(db, job_id=uuid.UUID(job_id))
            if job:
                job.status = "failed"
                job.error_message = str(e)
                db.commit()
        except Exception as update_error:
            print(f"Failed to update job status: {update_error}")
