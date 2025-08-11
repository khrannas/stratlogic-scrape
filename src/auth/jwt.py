"""
JWT token handling for StratLogic Scraping System.

This module provides JWT token creation, verification, and
user authentication utilities.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from uuid import UUID
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.database import get_db
from ..core.models import User, UserSession
from ..core.repositories.user import UserRepository
from ..core.utils import get_logger

# Get logger
logger = get_logger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as e:
        logger.warning(f"JWT token verification failed: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        db: Database session
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Get user from database
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(UUID(user_id))
        
        if user is None:
            raise credentials_exception
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return user
        
    except JWTError:
        raise credentials_exception


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        Current active user
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def require_role(required_role: str):
    """
    Dependency to require a specific user role.
    
    Args:
        required_role: Required role name
        
    Returns:
        Dependency function
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role.value != required_role and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user
    
    return role_checker


async def create_user_session(user_id: UUID, token: str, db: AsyncSession) -> UserSession:
    """
    Create a user session record.
    
    Args:
        user_id: User ID
        token: JWT token
        db: Database session
        
    Returns:
        Created user session
    """
    from ..auth.password import hash_password
    
    # Hash the token for storage
    token_hash = hash_password(token)
    
    # Calculate expiration
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours)
    
    # Create session
    session = UserSession(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expire
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return session


async def invalidate_user_session(token: str, db: AsyncSession) -> bool:
    """
    Invalidate a user session by token.
    
    Args:
        token: JWT token to invalidate
        db: Database session
        
    Returns:
        True if session was invalidated, False otherwise
    """
    from ..auth.password import hash_password
    
    token_hash = hash_password(token)
    
    # Find and delete session
    result = await db.execute(
        "DELETE FROM user_sessions WHERE token_hash = :token_hash",
        {"token_hash": token_hash}
    )
    
    await db.commit()
    return result.rowcount > 0
