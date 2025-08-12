import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class SystemConfigurationBase(BaseModel):
    config_key: str
    config_value: Optional[str] = None
    config_type: str = "string"
    description: Optional[str] = None
    is_sensitive: bool = False

class SystemConfigurationCreate(SystemConfigurationBase):
    pass

class SystemConfigurationUpdate(BaseModel):
    config_value: Optional[str] = None
    description: Optional[str] = None

class SystemConfiguration(SystemConfigurationBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
