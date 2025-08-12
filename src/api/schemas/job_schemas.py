import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

# JobConfiguration Schemas
class JobConfigurationBase(BaseModel):
    config_key: str
    config_value: Optional[str] = None

class JobConfigurationCreate(JobConfigurationBase):
    pass

class JobConfiguration(JobConfigurationBase):
    id: uuid.UUID
    job_id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True

# ScrapingJob Schemas
class ScrapingJobBase(BaseModel):
    job_type: str = Field(..., example="web_scraper")
    keywords: List[str] = Field(..., example=["AI", "machine learning"])
    status: str = "pending"
    progress: int = 0
    total_items: int = 0
    completed_items: int = 0
    error_message: Optional[str] = None

class ScrapingJobCreate(ScrapingJobBase):
    user_id: uuid.UUID
    configurations: Optional[List[JobConfigurationCreate]] = []

class ScrapingJobUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None
    total_items: Optional[int] = None
    completed_items: Optional[int] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None

class ScrapingJob(ScrapingJobBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expanded_keywords: Optional[List[str]] = []
    configurations: List[JobConfiguration] = []

    class Config:
        orm_mode = True
