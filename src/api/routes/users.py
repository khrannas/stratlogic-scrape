"""
User management routes for StratLogic Scraping System.

This module provides endpoints for user profile management,
user administration, and user statistics.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ...core.models import User, UserRole
from ...core.repositories.user import UserRepository
from ...auth.models import UserResponse, UserUpdate, UserProfile, UserStats
from ..dependencies import (
    get_db, get_current_active_user, require_role, 
    get_user_repository, validate_user_permissions
)
from ..middleware import log_request, log_error
from ...core.utils import get_logger

# Get logger
logger = get_logger(__name__)

# Create router
router = APIRouter()


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    request: Request,
    current_user: User = Depends(get_current_active_user)
) -> UserProfile:
    """
    Get current user's profile.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        
    Returns:
        UserProfile: Current user's profile
    """
    log_request(request, "Get current user profile", user_id=str(current_user.id))
    
    return UserProfile.from_orm(current_user)


@router.put("/me", response_model=UserProfile)
async def update_current_user_profile(
    user_data: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserProfile:
    """
    Update current user's profile.
    
    Args:
        user_data: User update data
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserProfile: Updated user profile
        
    Raises:
        HTTPException: If update fails
    """
    log_request(request, "Update current user profile", user_id=str(current_user.id))
    
    try:
        user_repo = UserRepository(db)
        
        # Check for username conflicts
        if user_data.username and user_data.username != current_user.username:
            existing_user = await user_repo.get_by_username(user_data.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Check for email conflicts
        if user_data.email and user_data.email != current_user.email:
            existing_user = await user_repo.get_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Update user fields
        if user_data.username is not None:
            current_user.username = user_data.username
        if user_data.email is not None:
            current_user.email = user_data.email
        if user_data.full_name is not None:
            current_user.full_name = user_data.full_name
        
        # Save changes
        await user_repo.update(current_user)
        
        log_request(request, "User profile updated successfully", user_id=str(current_user.id))
        
        return UserProfile.from_orm(current_user)
        
    except IntegrityError as e:
        log_error(request, "User profile update failed - integrity error", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile update failed - duplicate data"
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error(request, "User profile update failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.get("/me/stats", response_model=UserStats)
async def get_current_user_stats(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserStats:
    """
    Get current user's statistics.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserStats: User statistics
    """
    log_request(request, "Get current user stats", user_id=str(current_user.id))
    
    try:
        # Get user statistics from repository
        user_repo = UserRepository(db)
        stats = await user_repo.get_user_stats(current_user.id)
        
        return UserStats(**stats)
        
    except Exception as e:
        log_error(request, "Failed to get user stats", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )


@router.get("/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> UserProfile:
    """
    Get user profile by ID (admin only or own profile).
    
    Args:
        user_id: Target user ID
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserProfile: User profile
        
    Raises:
        HTTPException: If access denied or user not found
    """
    log_request(request, "Get user profile", user_id=str(user_id), requester_id=str(current_user.id))
    
    try:
        # Validate permissions
        await validate_user_permissions(str(user_id), current_user)
        
        # Get user
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserProfile.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(request, "Failed to get user profile", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.get("/", response_model=List[UserResponse])
async def list_users(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    search: Optional[str] = Query(None, description="Search term for username or email"),
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
) -> List[UserResponse]:
    """
    List users (admin only).
    
    Args:
        request: FastAPI request object
        skip: Number of users to skip
        limit: Maximum number of users to return
        search: Search term for username or email
        role: Filter by user role
        is_active: Filter by active status
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        List[UserResponse]: List of users
    """
    log_request(request, "List users", requester_id=str(current_user.id))
    
    try:
        user_repo = UserRepository(db)
        users = await user_repo.list_users(
            skip=skip,
            limit=limit,
            search=search,
            role=role,
            is_active=is_active
        )
        
        return [UserResponse.from_orm(user) for user in users]
        
    except Exception as e:
        log_error(request, "Failed to list users", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.put("/{user_id}", response_model=UserProfile)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    request: Request,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
) -> UserProfile:
    """
    Update user (admin only).
    
    Args:
        user_id: Target user ID
        user_data: User update data
        request: FastAPI request object
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        UserProfile: Updated user profile
        
    Raises:
        HTTPException: If update fails
    """
    log_request(request, "Update user", user_id=str(user_id), admin_id=str(current_user.id))
    
    try:
        user_repo = UserRepository(db)
        
        # Get user to update
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check for username conflicts
        if user_data.username and user_data.username != user.username:
            existing_user = await user_repo.get_by_username(user_data.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Check for email conflicts
        if user_data.email and user_data.email != user.email:
            existing_user = await user_repo.get_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Update user fields
        if user_data.username is not None:
            user.username = user_data.username
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        if user_data.role is not None:
            user.role = user_data.role
        
        # Save changes
        await user_repo.update(user)
        
        log_request(request, "User updated successfully", user_id=str(user_id), admin_id=str(current_user.id))
        
        return UserProfile.from_orm(user)
        
    except IntegrityError as e:
        log_error(request, "User update failed - integrity error", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User update failed - duplicate data"
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error(request, "User update failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    request: Request,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user (admin only).
    
    Args:
        user_id: Target user ID
        request: FastAPI request object
        current_user: Current authenticated user (admin)
        db: Database session
        
    Returns:
        dict: Deletion confirmation
        
    Raises:
        HTTPException: If deletion fails
    """
    log_request(request, "Delete user", user_id=str(user_id), admin_id=str(current_user.id))
    
    try:
        # Prevent admin from deleting themselves
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        user_repo = UserRepository(db)
        
        # Get user to delete
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete user
        await user_repo.delete(user_id)
        
        log_request(request, "User deleted successfully", user_id=str(user_id), admin_id=str(current_user.id))
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(request, "User deletion failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion failed"
        )
