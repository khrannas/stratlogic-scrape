from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.api.dependencies.auth import get_current_user
from src.api.schemas.user_schemas import User
from src.api.schemas.job_schemas import JobCreate, ScrapingJob
from src.api.schemas.artifact_schemas import Artifact
from src.scrapers.paper_scraper.paper_scraper import PaperScraper
from src.services.job_service import job_service
from src.services.artifact_service import artifact_service
from src.core.database import get_db

router = APIRouter(prefix="/papers", tags=["Paper Scraper"])
logger = logging.getLogger(__name__)

# Initialize paper scraper
paper_scraper = PaperScraper()

# Request model for paper search
class PaperSearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10
    sources: Optional[List[str]] = ["arxiv"]
    extract_pdfs: Optional[bool] = True
    analyze_content: Optional[bool] = True
    download_pdfs: Optional[bool] = True

@router.post("/search", response_model=ScrapingJob)
async def search_papers(
    request: PaperSearchRequest,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search and scrape academic papers

    Args:
        request: Paper search request containing query and options
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user

    Returns:
        Job response with job ID for tracking
    """
    try:
        # Create job
        job_data = JobCreate(
            user_id=current_user.id,
            job_type="paper_scraping",
            keywords=[request.query]  # Use the query as the primary keyword
        )

        job = job_service.create_job(db, job_in=job_data)

        # Start background task
        if background_tasks:
            background_tasks.add_task(
                _run_paper_scraping,
                job.id,
                current_user.id,
                request.query,
                request.max_results,
                request.sources,
                request.extract_pdfs,
                request.analyze_content,
                request.download_pdfs
            )

        return job

    except Exception as e:
        logger.error(f"Error creating paper scraping job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/job/{job_id}", response_model=ScrapingJob)
async def get_paper_scraping_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get paper scraping job status and results

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

        return job

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting paper scraping job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/paper/{paper_id}")
async def get_paper_by_id(
    paper_id: str,
    source: str = "arxiv",
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific paper by ID

    Args:
        paper_id: Paper identifier (arXiv ID or DOI)
        source: Source name ('arxiv', 'crossref')
        current_user: Current authenticated user

    Returns:
        Paper metadata and content
    """
    try:
        paper = await paper_scraper.get_paper_by_id(paper_id, source)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        return {
            "paper_id": paper_id,
            "source": source,
            "paper": paper,
            "retrieved_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting paper by ID: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def check_paper_scraper_health():
    """
    Check health of paper scraping services

    Returns:
        Health status of all paper scraping services
    """
    try:
        health_status = await paper_scraper.check_services_health()

        return {
            "status": "healthy" if all(health_status.values()) else "degraded",
            "services": health_status,
            "checked_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error checking paper scraper health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/artifacts/{job_id}", response_model=List[Artifact])
async def get_paper_artifacts(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get artifacts from a paper scraping job

    Args:
        job_id: Job identifier
        current_user: Current authenticated user

    Returns:
        List of artifacts from the job
    """
    try:
        # Verify job belongs to user
        job = job_service.get_job(db, job_id=job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get artifacts for the job
        artifacts = await artifact_service.get_artifacts_by_job_id(job_id)

        return [
            Artifact(
                id=artifact.id,
                user_id=artifact.user_id,
                job_id=artifact.job_id,
                artifact_type=artifact.artifact_type,
                source_url=artifact.source_url,
                title=artifact.title,
                content_hash=artifact.content_hash,
                file_size=artifact.file_size,
                mime_type=artifact.mime_type,
                minio_path=artifact.minio_path,
                is_public=artifact.is_public,
                created_at=artifact.created_at
            )
            for artifact in artifacts
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting paper artifacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/arxiv")
async def search_arxiv_papers(
    query: str,
    max_results: Optional[int] = 10,
    sort_by: str = "relevance",
    sort_order: str = "descending",
    current_user: User = Depends(get_current_user)
):
    """
    Search papers on arXiv

    Args:
        query: Search query
        max_results: Maximum number of results
        sort_by: Sort criteria
        sort_order: Sort order
        current_user: Current authenticated user

    Returns:
        List of arXiv papers
    """
    try:
        papers = await paper_scraper.arxiv_client.search_papers(
            query, max_results, sort_by, sort_order
        )

        return {
            "query": query,
            "source": "arxiv",
            "total_results": len(papers),
            "papers": papers,
            "searched_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error searching arXiv: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/crossref")
async def search_crossref_papers(
    query: str,
    max_results: Optional[int] = 10,
    sort: str = "relevance",
    order: str = "desc",
    current_user: User = Depends(get_current_user)
):
    """
    Search papers on CrossRef

    Args:
        query: Search query
        max_results: Maximum number of results
        sort: Sort criteria
        order: Sort order
        current_user: Current authenticated user

    Returns:
        List of CrossRef papers
    """
    try:
        papers = await paper_scraper.crossref_client.search_works(
            query, max_results, sort=sort, order=order
        )

        return {
            "query": query,
            "source": "crossref",
            "total_results": len(papers),
            "papers": papers,
            "searched_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error searching CrossRef: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_paper_content(
    paper_data: Dict[str, Any],
    extract_keywords: bool = True,
    generate_summary: bool = True,
    analyze_citations: bool = True,
    assess_quality: bool = True,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze paper content using LLM

    Args:
        paper_data: Paper metadata and content
        extract_keywords: Whether to extract keywords
        generate_summary: Whether to generate summary
        analyze_citations: Whether to analyze citations
        assess_quality: Whether to assess quality
        current_user: Current authenticated user

    Returns:
        Analysis results
    """
    try:
        analysis = await paper_scraper.content_analyzer.analyze_paper(
            paper_data,
            extract_keywords=extract_keywords,
            generate_summary=generate_summary,
            analyze_citations=analyze_citations,
            assess_quality=assess_quality
        )

        return {
            "analysis": analysis,
            "analyzed_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error analyzing paper content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare")
async def compare_papers(
    papers: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user)
):
    """
    Compare multiple papers

    Args:
        papers: List of paper data dictionaries
        current_user: Current authenticated user

    Returns:
        Comparison results
    """
    try:
        if len(papers) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 papers for comparison")

        comparison = await paper_scraper.content_analyzer.compare_papers(papers)

        return {
            "comparison": comparison,
            "compared_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing papers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _run_paper_scraping(
    job_id: str,
    user_id: str,
    query: str,
    max_results: int,
    sources: List[str],
    extract_pdfs: bool,
    analyze_content: bool,
    download_pdfs: bool
):
    """
    Background task to run paper scraping

    Args:
        job_id: Job identifier
        user_id: User identifier
        query: Search query
        max_results: Maximum number of results
        sources: List of sources to search
        extract_pdfs: Whether to extract PDFs
        analyze_content: Whether to analyze content
        download_pdfs: Whether to download PDFs
    """
    try:
        logger.info(f"Starting background paper scraping for job {job_id}")

        result = await paper_scraper.scrape_papers(
            query=query,
            job_id=job_id,
            user_id=user_id,
            max_results=max_results,
            sources=sources,
            extract_pdfs=extract_pdfs,
            analyze_content=analyze_content,
            download_pdfs=download_pdfs
        )

        # Update job with results
        await job_service.update_job_results(job_id, result)

        logger.info(f"Completed background paper scraping for job {job_id}")

    except Exception as e:
        logger.error(f"Error in background paper scraping for job {job_id}: {e}")
        await job_service.update_job_status(job_id, "failed")
        await job_service.update_job_results(job_id, {"error": str(e)})
