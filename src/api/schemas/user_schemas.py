import uuid
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

# Shared properties
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    username: str = Field(..., example="john_doe")
    full_name: str | None = Field(None, example="John Doe")

# Properties to receive on user creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="a_strong_password")

# Properties to receive on user update
class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    full_name: str | None = None
    password: str | None = None

# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: uuid.UUID
    is_active: bool = True
    role: str = "user"
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Properties to return to client
class User(UserInDBBase):
    pass

# Properties stored in DB
class UserInDB(UserInDBBase):
    password_hash: str
