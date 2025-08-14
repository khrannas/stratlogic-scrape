from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.api.schemas import artifact_schemas
from src.services.artifact_service import artifact_service
from src.core.database import get_db

router = APIRouter(
    prefix="/artifacts",
    tags=["artifacts"],
)

@router.post("/", response_model=artifact_schemas.Artifact)
def create_artifact(
    *,
    db: Session = Depends(get_db),
    artifact_in: artifact_schemas.ArtifactCreate,
):
    """
    Create new artifact.
    """
    artifact = artifact_service.create_artifact(db, artifact_in=artifact_in)
    return artifact

@router.get("/", response_model=List[artifact_schemas.ArtifactResponse])
def read_artifacts(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search term for title or content"),
    source_type: Optional[str] = Query(None, description="Filter by source type (web, paper, government)"),
    job_id: Optional[str] = Query(None, description="Filter by job ID"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Number of items per page"),
):
    """
    Retrieve artifacts with filtering and pagination.
    """
    artifacts = artifact_service.get_artifacts(
        db,
        search=search,
        source_type=source_type,
        job_id=job_id,
        page=page,
        size=size
    )

    # Transform artifacts to include frontend-expected fields
    response_artifacts = []
    for artifact in artifacts:
        # Map job_type to source_type for frontend
        source_type_mapping = {
            'web_scraper': 'web',
            'paper_scraper': 'paper',
            'government_scraper': 'government'
        }
        mapped_source_type = source_type_mapping.get(artifact.job.job_type, artifact.job.job_type)

        response_artifact = artifact_schemas.ArtifactResponse(
            id=artifact.id,
            title=artifact.title,
            content="Content not available in database",  # TODO: Fetch from MinIO
            source_type=mapped_source_type,
            source_url=artifact.source_url,
            created_at=artifact.created_at,
            url=artifact.source_url  # Alias for frontend compatibility
        )
        response_artifacts.append(response_artifact)

    return response_artifacts

@router.get("/{artifact_id}", response_model=artifact_schemas.Artifact)
def read_artifact(
    *,
    db: Session = Depends(get_db),
    artifact_id: str,
):
    """
    Get artifact by ID.
    """
    artifact = artifact_service.get_artifact(db, artifact_id=artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact

@router.put("/{artifact_id}", response_model=artifact_schemas.Artifact)
def update_artifact(
    *,
    db: Session = Depends(get_db),
    artifact_id: str,
    artifact_in: artifact_schemas.ArtifactUpdate,
):
    """
    Update artifact.
    """
    artifact = artifact_service.get_artifact(db, artifact_id=artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    artifact = artifact_service.update_artifact(db, db_obj=artifact, obj_in=artifact_in)
    return artifact

@router.delete("/{artifact_id}")
def delete_artifact(
    *,
    db: Session = Depends(get_db),
    artifact_id: str,
):
    """
    Delete artifact.
    """
    artifact = artifact_service.get_artifact(db, artifact_id=artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    artifact_service.delete_artifact(db, artifact_id=artifact_id)
    return {"message": "Artifact deleted successfully"}

@router.post("/upload")
def upload_artifact_file(
    *,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    artifact_id: str = None,
):
    """
    Upload file for an artifact.
    """
    if not artifact_id:
        raise HTTPException(status_code=400, detail="Artifact ID is required")

    artifact = artifact_service.get_artifact(db, artifact_id=artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Upload file to storage
    file_url = artifact_service.upload_artifact_file(db, artifact_id=artifact_id, file=file)
    return {"message": "File uploaded successfully", "file_url": file_url}

@router.get("/{artifact_id}/download")
def download_artifact_file(
    *,
    db: Session = Depends(get_db),
    artifact_id: str,
):
    """
    Download artifact file.
    """
    artifact = artifact_service.get_artifact(db, artifact_id=artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Get download URL
    download_url = artifact_service.get_download_url(db, artifact_id=artifact_id)
    return {"download_url": download_url}
