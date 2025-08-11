"""
Authentication routes for StratLogic Scraping System.

This module provides endpoints for user registration, login, logout,
and password management.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ...core.models import User, UserRole
from ...core.repositories.user import UserRepository
from ...auth.jwt import create_access_token, create_user_session, invalidate_user_session
from ...auth.password import hash_password, verify_password, validate_password_strength
from ...auth.models import (
    UserCreate, UserLogin, UserResponse, Token, AuthResponse,
    PasswordChange, PasswordReset, PasswordResetConfirm
)
from ..dependencies import get_db, get_current_active_user
from ..middleware import log_request, log_error
from ...core.utils import get_logger

# Get logger
logger = get_logger(__name__)

# Create router
router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> AuthResponse:
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        request: FastAPI request object
        db: Database session
        
    Returns:
        AuthResponse: User and token data
        
    Raises:
        HTTPException: If registration fails
    """
    log_request(request, "User registration attempt", username=user_data.username, email=user_data.email)
    
    try:
        # Validate password strength
        if not validate_password_strength(user_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet strength requirements"
            )
        
        # Create user repository
        user_repo = UserRepository(db)
        
        # Check if username already exists
        existing_user = await user_repo.get_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        existing_user = await user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = hash_password(user_data.password)
        user = User(
            id=uuid4(),
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=UserRole.USER,
            is_active=True,
            is_verified=False,
            last_login=datetime.now(timezone.utc)
        )
        
        # Save user to database
        await user_repo.create(user)
        
        # Create access token
        token_data = {"sub": str(user.id)}
        access_token = create_access_token(data=token_data)
        
        # Create user session
        await create_user_session(user.id, access_token, db)
        
        # Create response
        token_response = Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=24 * 60 * 60,  # 24 hours in seconds
            user_id=user.id
        )
        
        user_response = UserResponse.from_orm(user)
        
        log_request(request, "User registration successful", user_id=str(user.id))
        
        return AuthResponse(
            user=user_response,
            token=token_response,
            message="User registered successfully"
        )
        
    except IntegrityError as e:
        log_error(request, "User registration failed - integrity error", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User registration failed - duplicate data"
        )
    except Exception as e:
        log_error(request, "User registration failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User registration failed"
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    user_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> AuthResponse:
    """
    Authenticate user and return access token.
    
    Args:
        user_data: User login credentials
        request: FastAPI request object
        db: Database session
        
    Returns:
        AuthResponse: User and token data
        
    Raises:
        HTTPException: If authentication fails
    """
    log_request(request, "User login attempt", username=user_data.username)
    
    try:
        # Create user repository
        user_repo = UserRepository(db)
        
        # Find user by username or email
        user = await user_repo.get_by_username(user_data.username)
        if not user:
            user = await user_repo.get_by_email(user_data.username)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Verify password
        if not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is inactive"
            )
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await user_repo.update(user)
        
        # Create access token
        token_data = {"sub": str(user.id)}
        access_token = create_access_token(data=token_data)
        
        # Create user session
        await create_user_session(user.id, access_token, db)
        
        # Create response
        token_response = Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=24 * 60 * 60,  # 24 hours in seconds
            user_id=user.id
        )
        
        user_response = UserResponse.from_orm(user)
        
        log_request(request, "User login successful", user_id=str(user.id))
        
        return AuthResponse(
            user=user_response,
            token=token_response,
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(request, "User login failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user and invalidate session.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Logout confirmation
    """
    try:
        # Get token from request
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
            # Invalidate session
            await invalidate_user_session(token, db)
        
        log_request(request, "User logout successful", user_id=str(current_user.id))
        
        return {"message": "Logout successful"}
        
    except Exception as e:
        log_error(request, "User logout failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password.
    
    Args:
        password_data: Password change data
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Password change confirmation
    """
    log_request(request, "Password change attempt", user_id=str(current_user.id))
    
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password strength
        if not validate_password_strength(password_data.new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password does not meet strength requirements"
            )
        
        # Hash new password
        new_hashed_password = hash_password(password_data.new_password)
        
        # Update user password
        user_repo = UserRepository(db)
        current_user.hashed_password = new_hashed_password
        await user_repo.update(current_user)
        
        log_request(request, "Password change successful", user_id=str(current_user.id))
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(request, "Password change failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/refresh")
async def refresh_token(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Refresh access token.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Token: New access token
    """
    log_request(request, "Token refresh attempt", user_id=str(current_user.id))
    
    try:
        # Create new access token
        token_data = {"sub": str(current_user.id)}
        access_token = create_access_token(data=token_data)
        
        # Create new user session
        await create_user_session(current_user.id, access_token, db)
        
        # Create response
        token_response = Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=24 * 60 * 60,  # 24 hours in seconds
            user_id=current_user.id
        )
        
        log_request(request, "Token refresh successful", user_id=str(current_user.id))
        
        return token_response
        
    except Exception as e:
        log_error(request, "Token refresh failed", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )
