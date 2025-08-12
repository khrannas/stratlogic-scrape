import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MetadataTagBase(BaseModel):
    tag_type: str = Field(..., example="keyword")
    tag_key: str = Field(..., example="topic")
    tag_value: Optional[str] = Field(None, example="AI")

class MetadataTagCreate(MetadataTagBase):
    artifact_id: uuid.UUID

class MetadataTag(MetadataTagBase):
    id: uuid.UUID
    artifact_id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True
