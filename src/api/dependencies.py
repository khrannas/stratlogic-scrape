"""
API dependencies for StratLogic Scraping System.

This module provides dependency injection functions for database sessions,
authentication, and other common API requirements.
"""

from typing import Generator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..core.database import get_db as get_database_session
from ..core.models import User
from ..core.repositories.user import UserRepository
from ..auth.jwt import get_current_user as get_user_from_token, require_role as require_user_role
from ..core.utils import get_logger

# Get logger
logger = get_logger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer()


async def get_db() -> AsyncSession:
    """
    Get database session dependency.
    
    Returns:
        AsyncSession: Database session
    """
    async for session in get_database_session():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user dependency.
    
    Args:
        credentials: HTTP authorization credentials
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    return await get_user_from_token(credentials, db)


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user dependency.
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_role(required_role: str):
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


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get optional user (for endpoints that work with or without authentication).
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        Optional[User]: User if authenticated, None otherwise
    """
    try:
        # Check if Authorization header exists
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        # Extract token
        token = auth_header.split(" ")[1]
        
        # Verify token and get user
        from ..auth.jwt import verify_token
        payload = verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Get user from database
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        
        if not user or not user.is_active:
            return None
        
        return user
        
    except Exception as e:
        logger.debug(f"Optional user authentication failed: {e}")
        return None


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    Get user repository dependency.
    
    Args:
        db: Database session
        
    Returns:
        UserRepository: User repository instance
    """
    return UserRepository(db)


async def validate_user_permissions(
    user_id: str,
    current_user: User = Depends(get_current_active_user)
) -> bool:
    """
    Validate that current user can access the specified user's data.
    
    Args:
        user_id: Target user ID
        current_user: Current authenticated user
        
    Returns:
        bool: True if access is allowed
        
    Raises:
        HTTPException: If access is denied
    """
    # Admin can access any user's data
    if current_user.role.value == "admin":
        return True
    
    # Users can only access their own data
    if str(current_user.id) == user_id:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied"
    )
