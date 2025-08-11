"""
Content processing API routes for the StratLogic Scraping System.

This module provides API endpoints for content enrichment, document processing,
analytics, and export functionality.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...core.database import get_async_session
from ...core.models.content_processing import (
    ContentType, QualityLevel, ExportFormat, ReportType, ProcessingStatus
)
from ...services.content_enrichment import ContentEnrichmentService
from ...services.document_processing import DocumentProcessingService
from ...services.analytics_service import AnalyticsService
from ...services.export_service import ExportService
from ...storage.minio_client import get_minio_client
from ...api.dependencies import get_current_user
from ...core.models import User

router = APIRouter()


# Pydantic models for request/response
class ContentEnrichmentResponse(BaseModel):
    id: UUID
    artifact_id: UUID
    content_type: str
    language: Optional[str]
    word_count: Optional[int]
    character_count: Optional[int]
    quality_score: Optional[float]
    quality_level: Optional[str]
    readability_score: Optional[float]
    complexity_score: Optional[float]
    processing_status: str
    tags: List[str] = []
    created_at: str
    updated_at: str


class DocumentStructureResponse(BaseModel):
    id: UUID
    content_id: UUID
    title: Optional[str]
    authors: Optional[List[str]]
    abstract: Optional[str]
    headings: Optional[List[str]]
    page_count: Optional[int]
    document_type: Optional[str]
    language: Optional[str]
    tables_count: int = 0
    annotations_count: int = 0
    created_at: str
    updated_at: str


class ContentAnalyticsResponse(BaseModel):
    id: UUID
    content_id: UUID
    view_count: int
    download_count: int
    share_count: int
    impact_score: Optional[float]
    relevance_score: Optional[float]
    popularity_score: Optional[float]
    last_accessed: Optional[str]
    created_at: str
    updated_at: str


class ExportJobResponse(BaseModel):
    id: UUID
    user_id: UUID
    export_format: str
    status: str
    progress: float
    file_path: Optional[str]
    file_size: Optional[int]
    error_message: Optional[str]
    created_at: str
    updated_at: str


class ReportResponse(BaseModel):
    id: UUID
    user_id: UUID
    report_type: str
    report_title: str
    report_description: Optional[str]
    report_data: dict
    file_path: Optional[str]
    file_size: Optional[int]
    created_at: str
    updated_at: str


class EnrichArtifactRequest(BaseModel):
    artifact_id: UUID


class ProcessDocumentRequest(BaseModel):
    content_enrichment_id: UUID


class CreateExportRequest(BaseModel):
    export_format: ExportFormat
    export_query: Optional[dict] = None


class CreateReportRequest(BaseModel):
    report_type: ReportType
    report_title: str
    report_description: Optional[str] = None


# Content Enrichment Routes
@router.post("/enrich", response_model=ContentEnrichmentResponse)
async def enrich_artifact(
    request: EnrichArtifactRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_async_session)
):
    """Enrich an artifact with content analysis."""
    try:
        service = ContentEnrichmentService(db)
        enrichment = await service.enrich_artifact(request.artifact_id)
        
        return ContentEnrichmentResponse(
            id=enrichment.id,
            artifact_id=enrichment.artifact_id,
            content_type=enrichment.content_type.value,
            language=enrichment.language,
            word_count=enrichment.word_count,
            character_count=enrichment.character_count,
            quality_score=enrichment.quality_score,
            quality_level=enrichment.quality_level.value if enrichment.quality_level else None,
            readability_score=enrichment.readability_score,
            complexity_score=enrichment.complexity_score,
            processing_status=enrichment.processing_status.value,
            tags=[tag.name for tag in enrichment.tags],
            created_at=enrichment.created_at.isoformat(),
            updated_at=enrichment.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/enrich/{enrichment_id}", response_model=ContentEnrichmentResponse)
async def get_content_enrichment(
    enrichment_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_async_session)
):
    """Get content enrichment by ID."""
    try:
        service = ContentEnrichmentService(db)
        enrichment = await service.get_content_enrichment(enrichment_id)
        
        if not enrichment:
            raise HTTPException(status_code=404, detail="Content enrichment not found")
        
        return ContentEnrichmentResponse(
            id=enrichment.id,
            artifact_id=enrichment.artifact_id,
            content_type=enrichment.content_type.value,
            language=enrichment.language,
            word_count=enrichment.word_count,
            character_count=enrichment.character_count,
            quality_score=enrichment.quality_score,
            quality_level=enrichment.quality_level.value if enrichment.quality_level else None,
            readability_score=enrichment.readability_score,
            complexity_score=enrichment.complexity_score,
            processing_status=enrichment.processing_status.value,
            tags=[tag.name for tag in enrichment.tags],
            created_at=enrichment.created_at.isoformat(),
            updated_at=enrichment.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Document Processing Routes
@router.post("/documents/process", response_model=DocumentStructureResponse)
async def process_document(
    request: ProcessDocumentRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_async_session),
    minio_client = Depends(get_minio_client)
):
    """Process document and extract structure."""
    try:
        service = DocumentProcessingService(db, minio_client)
        structure = await service.process_document(request.content_enrichment_id)
        
        return DocumentStructureResponse(
            id=structure.id,
            content_id=structure.content_id,
            title=structure.title,
            authors=structure.authors,
            abstract=structure.abstract,
            headings=structure.headings,
            page_count=structure.page_count,
            document_type=structure.document_type,
            language=structure.language,
            tables_count=len(structure.tables),
            annotations_count=len(structure.annotations),
            created_at=structure.created_at.isoformat(),
            updated_at=structure.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/documents/{structure_id}", response_model=DocumentStructureResponse)
async def get_document_structure(
    structure_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_async_session),
    minio_client = Depends(get_minio_client)
):
    """Get document structure by ID."""
    try:
        service = DocumentProcessingService(db, minio_client)
        structure = await service.get_document_structure(structure_id)
        
        if not structure:
            raise HTTPException(status_code=404, detail="Document structure not found")
        
        return DocumentStructureResponse(
            id=structure.id,
            content_id=structure.content_id,
            title=structure.title,
            authors=structure.authors,
            abstract=structure.abstract,
            headings=structure.headings,
            page_count=structure.page_count,
            document_type=structure.document_type,
            language=structure.language,
            tables_count=len(structure.tables),
            annotations_count=len(structure.annotations),
            created_at=structure.created_at.isoformat(),
            updated_at=structure.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Analytics Routes
@router.post("/analytics/{content_id}/view")
async def record_content_view(
    content_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_async_session)
):
    """Record a content view."""
    try:
        service = AnalyticsService(db)
        await service.record_content_view(content_id, current_user.id)
        return {"message": "View recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analytics/{content_id}/download")
async def record_content_download(
    content_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_async_session)
):
    """Record a content download."""
    try:
        service = AnalyticsService(db)
        await service.record_content_download(content_id, current_user.id)
        return {"message": "Download recorded successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/{content_id}", response_model=ContentAnalyticsResponse)
async def get_content_analytics(
    content_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_async_session)
):
    """Get analytics for content."""
    try:
        service = AnalyticsService(db)
        analytics = await service._get_analytics_by_content(content_id)
        
        if not analytics:
            # Create analytics if it doesn't exist
            analytics = await service.create_content_analytics(content_id)
        
        return ContentAnalyticsResponse(
            id=analytics.id,
            content_id=analytics.content_id,
            view_count=analytics.view_count,
            download_count=analytics.download_count,
            share_count=analytics.share_count,
            impact_score=analytics.impact_score,
            relevance_score=analytics.relevance_score,
            popularity_score=analytics.popularity_score,
            last_accessed=analytics.last_accessed.isoformat() if analytics.last_accessed else None,
            created_at=analytics.created_at.isoformat(),
            updated_at=analytics.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/trending")
async def get_trending_content(
    period: str = Query("daily", description="Trend period"),
    limit: int = Query(20, description="Number of items to return"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_async_session)
):
    """Get trending content."""
    try:
        service = AnalyticsService(db)
        trending = await service.get_trending_content(period, limit)
        return {"trending_content": trending}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/summary")
async def get_analytics_summary(
    current_user: User = Depends(get_current_user),
    db = Depends(get_async_session)
):
    """Get analytics summary."""
    try:
        service = AnalyticsService(db)
        summary = await service.get_content_analytics_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Export Routes
@router.post("/export", response_model=ExportJobResponse)
async def create_export_job(
    request: CreateExportRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_async_session),
    minio_client = Depends(get_minio_client)
):
    """Create an export job."""
    try:
        service = ExportService(db, minio_client)
        export_job = await service.create_export_job(
            current_user.id,
            request.export_format,
            request.export_query
        )
        
        return ExportJobResponse(
            id=export_job.id,
            user_id=export_job.user_id,
            export_format=export_job.export_format.value,
            status=export_job.status.value,
            progress=export_job.progress,
            file_path=export_job.file_path,
            file_size=export_job.file_size,
            error_message=export_job.error_message,
            created_at=export_job.created_at.isoformat(),
            updated_at=export_job.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/export/{job_id}", response_model=ExportJobResponse)
async def get_export_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_async_session),
    minio_client = Depends(get_minio_client)
):
    """Get export job by ID."""
    try:
        service = ExportService(db, minio_client)
        export_job = await service.get_export_job(job_id)
        
        if not export_job:
            raise HTTPException(status_code=404, detail="Export job not found")
        
        return ExportJobResponse(
            id=export_job.id,
            user_id=export_job.user_id,
            export_format=export_job.export_format.value,
            status=export_job.status.value,
            progress=export_job.progress,
            file_path=export_job.file_path,
            file_size=export_job.file_size,
            error_message=export_job.error_message,
            created_at=export_job.created_at.isoformat(),
            updated_at=export_job.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/export", response_model=List[ExportJobResponse])
async def get_user_export_jobs(
    limit: int = Query(50, description="Number of jobs to return"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_async_session),
    minio_client = Depends(get_minio_client)
):
    """Get export jobs for current user."""
    try:
        service = ExportService(db, minio_client)
        export_jobs = await service.get_user_export_jobs(current_user.id, limit)
        
        return [
            ExportJobResponse(
                id=job.id,
                user_id=job.user_id,
                export_format=job.export_format.value,
                status=job.status.value,
                progress=job.progress,
                file_path=job.file_path,
                file_size=job.file_size,
                error_message=job.error_message,
                created_at=job.created_at.isoformat(),
                updated_at=job.updated_at.isoformat()
            )
            for job in export_jobs
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Report Routes
@router.post("/reports", response_model=ReportResponse)
async def create_report(
    request: CreateReportRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_async_session),
    minio_client = Depends(get_minio_client)
):
    """Create a new report."""
    try:
        service = ExportService(db, minio_client)
        report = await service.create_report(
            current_user.id,
            request.report_type,
            request.report_title,
            request.report_description
        )
        
        return ReportResponse(
            id=report.id,
            user_id=report.user_id,
            report_type=report.report_type.value,
            report_title=report.report_title,
            report_description=report.report_description,
            report_data=report.report_data,
            file_path=report.file_path,
            file_size=report.file_size,
            created_at=report.created_at.isoformat(),
            updated_at=report.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db = Depends(get_async_session),
    minio_client = Depends(get_minio_client)
):
    """Get report by ID."""
    try:
        service = ExportService(db, minio_client)
        report = await service.get_report(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return ReportResponse(
            id=report.id,
            user_id=report.user_id,
            report_type=report.report_type.value,
            report_title=report.report_title,
            report_description=report.report_description,
            report_data=report.report_data,
            file_path=report.file_path,
            file_size=report.file_size,
            created_at=report.created_at.isoformat(),
            updated_at=report.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reports", response_model=List[ReportResponse])
async def get_user_reports(
    limit: int = Query(50, description="Number of reports to return"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_async_session),
    minio_client = Depends(get_minio_client)
):
    """Get reports for current user."""
    try:
        service = ExportService(db, minio_client)
        reports = await service.get_user_reports(current_user.id, limit)
        
        return [
            ReportResponse(
                id=report.id,
                user_id=report.user_id,
                report_type=report.report_type.value,
                report_title=report.report_title,
                report_description=report.report_description,
                report_data=report.report_data,
                file_path=report.file_path,
                file_size=report.file_size,
                created_at=report.created_at.isoformat(),
                updated_at=report.updated_at.isoformat()
            )
            for report in reports
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
