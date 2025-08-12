import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

# ContentExtraction Schemas
class ContentExtractionBase(BaseModel):
    extraction_type: str
    extracted_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None

class ContentExtractionCreate(ContentExtractionBase):
    pass

class ContentExtraction(ContentExtractionBase):
    id: uuid.UUID
    artifact_id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True

# Artifact Schemas
class ArtifactBase(BaseModel):
    artifact_type: str = Field(..., example="web_page")
    source_url: Optional[str] = Field(None, example="https://example.com")
    title: Optional[str] = Field(None, example="Example Web Page")
    content_hash: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    minio_path: str
    is_public: bool = False

class ArtifactCreate(ArtifactBase):
    user_id: uuid.UUID
    job_id: uuid.UUID

class ArtifactUpdate(BaseModel):
    title: Optional[str] = None
    is_public: Optional[bool] = None

class Artifact(ArtifactBase):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    created_at: datetime
    extractions: List[ContentExtraction] = []

    class Config:
        orm_mode = True
