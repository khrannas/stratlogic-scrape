from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from src.api.dependencies.auth import get_current_user
from src.api.schemas.user_schemas import User
from src.api.schemas.job_schemas import JobCreate, ScrapingJob
from src.api.schemas.artifact_schemas import Artifact
from src.scrapers.government_scraper.government_scraper import GovernmentScraper
from src.services.job_service import job_service
from src.services.artifact_service import artifact_service
from src.core.database import get_db

router = APIRouter(prefix="/government", tags=["Government Scraper"])
logger = logging.getLogger(__name__)

# Initialize government scraper
government_scraper = GovernmentScraper()

@router.post("/search", response_model=ScrapingJob)
async def search_government_documents(
    keywords: List[str],
    sources: Optional[List[str]] = ["websites", "apis"],
    max_documents_per_keyword: Optional[int] = 20,
    process_documents: Optional[bool] = True,
    analyze_content: Optional[bool] = True,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search and scrape government documents

    Args:
        keywords: List of keywords to search for
        sources: List of sources to search ('websites', 'apis')
        max_documents_per_keyword: Maximum documents per keyword
        process_documents: Whether to process document content
        analyze_content: Whether to analyze content
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user

    Returns:
        Job response with job ID for tracking
    """
    try:
        # Create job
        job_data = JobCreate(
            user_id=current_user.id,
            job_type="government_scraping",
            keywords=keywords
        )

        job = job_service.create_job(db, job_in=job_data)

        # Start background task
        if background_tasks:
            background_tasks.add_task(
                _run_government_scraping,
                job.id,
                current_user.id,
                keywords,
                sources,
                max_documents_per_keyword,
                process_documents,
                analyze_content
            )

        return job

    except Exception as e:
        logger.error(f"Error creating government scraping job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/job/{job_id}", response_model=ScrapingJob)
async def get_government_scraping_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get government scraping job status and results

    Args:
        job_id: Job identifier
        current_user: Current authenticated user

    Returns:
        Job response with current status and progress
    """
    try:
        job = job_service.get_job(db, job_id=job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        return job

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting government scraping job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def check_government_scraper_health():
    """
    Check health of government scraping services

    Returns:
        Health status of all government scraping components
    """
    try:
        health_status = await government_scraper.check_services_health()

        return {
            "status": "healthy" if all(health_status.values()) else "degraded",
            "services": health_status,
            "checked_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "services": {},
            "error": str(e),
            "checked_at": datetime.now().isoformat()
        }

@router.get("/websites")
async def get_government_websites():
    """
    Get list of configured government websites

    Returns:
        List of government websites
    """
    try:
        from src.scrapers.government_scraper.config import government_scraper_settings

        return {
            "websites": government_scraper_settings.government_websites,
            "total_count": len(government_scraper_settings.government_websites)
        }

    except Exception as e:
        logger.error(f"Error getting government websites: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/apis")
async def get_government_apis():
    """
    Get list of configured government APIs

    Returns:
        List of government APIs
    """
    try:
        from src.scrapers.government_scraper.config import government_scraper_settings

        return {
            "apis": government_scraper_settings.government_apis,
            "total_count": len(government_scraper_settings.government_apis)
        }

    except Exception as e:
        logger.error(f"Error getting government APIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/website")
async def search_specific_website(
    website_url: str,
    keywords: List[str],
    max_pages: Optional[int] = 50,
    current_user: User = Depends(get_current_user)
):
    """
    Search a specific government website

    Args:
        website_url: URL of the government website
        keywords: List of keywords to search for
        max_pages: Maximum pages to crawl
        current_user: Current authenticated user

    Returns:
        List of matching documents
    """
    try:
        documents = await government_scraper.search_specific_website(
            website_url,
            keywords,
            max_pages
        )

        return {
            "website_url": website_url,
            "keywords": keywords,
            "documents_found": len(documents),
            "documents": documents
        }

    except Exception as e:
        logger.error(f"Error searching specific website: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/api")
async def search_specific_api(
    api_endpoint: str,
    keywords: List[str],
    max_results: Optional[int] = 50,
    current_user: User = Depends(get_current_user)
):
    """
    Search a specific government API

    Args:
        api_endpoint: API endpoint URL
        keywords: List of keywords to search for
        max_results: Maximum results to return
        current_user: Current authenticated user

    Returns:
        List of matching documents
    """
    try:
        documents = await government_scraper.search_specific_api(
            api_endpoint,
            keywords,
            max_results
        )

        return {
            "api_endpoint": api_endpoint,
            "keywords": keywords,
            "documents_found": len(documents),
            "documents": documents
        }

    except Exception as e:
        logger.error(f"Error searching specific API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/document/{document_url:path}")
async def get_document_by_url(
    document_url: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific document by URL

    Args:
        document_url: URL of the document
        current_user: Current authenticated user

    Returns:
        Document data
    """
    try:
        document = await government_scraper.get_document_by_url(document_url)

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return document

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document by URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/artifacts", response_model=List[Artifact])
async def get_government_artifacts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get government document artifacts for the current user

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of government document artifacts
    """
    try:
        artifacts = artifact_service.get_artifacts_by_type(
            db,
            user_id=current_user.id,
            artifact_type="government_document",
            skip=skip,
            limit=limit
        )

        return artifacts

    except Exception as e:
        logger.error(f"Error getting government artifacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/artifacts/{artifact_id}", response_model=Artifact)
async def get_government_artifact(
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific government document artifact

    Args:
        artifact_id: Artifact identifier
        db: Database session
        current_user: Current authenticated user

    Returns:
        Government document artifact
    """
    try:
        artifact = artifact_service.get_artifact(db, artifact_id=artifact_id)

        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")

        if artifact.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        return artifact

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting government artifact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_government_scraping_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get government scraping statistics for the current user

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        Government scraping statistics
    """
    try:
        # Get total artifacts
        total_artifacts = artifact_service.count_artifacts_by_type(
            db,
            user_id=current_user.id,
            artifact_type="government_document"
        )

        # Get total jobs
        total_jobs = job_service.count_jobs_by_type(
            db,
            user_id=current_user.id,
            job_type="government_scraping"
        )

        # Get recent jobs
        recent_jobs = job_service.get_jobs_by_type(
            db,
            user_id=current_user.id,
            job_type="government_scraping",
            skip=0,
            limit=5
        )

        return {
            "total_artifacts": total_artifacts,
            "total_jobs": total_jobs,
            "recent_jobs": recent_jobs,
            "user_id": current_user.id
        }

    except Exception as e:
        logger.error(f"Error getting government scraping stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task function
async def _run_government_scraping(
    job_id: str,
    user_id: str,
    keywords: List[str],
    sources: List[str],
    max_documents_per_keyword: int,
    process_documents: bool,
    analyze_content: bool
):
    """
    Background task to run government document scraping

    Args:
        job_id: Job identifier
        user_id: User identifier
        keywords: List of keywords to search for
        sources: List of sources to search
        max_documents_per_keyword: Maximum documents per keyword
        process_documents: Whether to process document content
        analyze_content: Whether to analyze content
    """
    try:
        logger.info(f"Starting background government scraping job: {job_id}")

        result = await government_scraper.scrape_government_documents(
            keywords=keywords,
            job_id=job_id,
            user_id=user_id,
            sources=sources,
            max_documents_per_keyword=max_documents_per_keyword,
            process_documents=process_documents,
            analyze_content=analyze_content
        )

        logger.info(f"Completed background government scraping job: {job_id}")

    except Exception as e:
        logger.error(f"Background government scraping job failed: {job_id} - {e}")
        # Job status will be updated to 'failed' by the scraper
