from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserLogin(BaseModel):
    """Schema for user login request"""
    email: EmailStr = Field(..., example="user@example.com")
    password: str = Field(..., min_length=8, example="a_strong_password")

class UserRegister(BaseModel):
    """Schema for user registration request"""
    email: EmailStr = Field(..., example="user@example.com")
    username: str = Field(..., min_length=3, max_length=50, example="john_doe")
    password: str = Field(..., min_length=8, example="a_strong_password")
    full_name: Optional[str] = Field(None, example="John Doe")

class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class TokenData(BaseModel):
    """Schema for token payload data"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None

class UserResponse(BaseModel):
    """Schema for user response after authentication"""
    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
