from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services.user_service import UserService
from src.api.schemas.auth_schemas import UserLogin, UserRegister, Token, UserResponse
from src.api.schemas.user_schemas import User
from src.api.dependencies.auth import get_current_user, get_current_admin
from src.core.exceptions import AuthenticationError, UserAlreadyExistsError

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.

    - **email**: User's email address (must be unique)
    - **username**: User's username (must be unique, 3-50 characters)
    - **password**: User's password (minimum 8 characters)
    - **full_name**: User's full name (optional)
    """
    try:
        user_service = UserService(db)
        user = user_service.create_user(user_data)

        return UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate a user and return a JWT token.

    - **email**: User's email address
    - **password**: User's password
    """
    try:
        user_service = UserService(db)
        token = user_service.login_user(login_data)
        return token
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get information about the currently authenticated user.
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active
    )

@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_user)
):
    """
    Logout the current user (token invalidation handled client-side).
    """
    # Note: In a production system, you might want to implement token blacklisting
    # For now, we'll rely on client-side token removal
    return {"message": "Successfully logged out"}

@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    new_role: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update a user's role (admin only).

    - **user_id**: ID of the user to update
    - **new_role**: New role for the user
    """
    try:
        user_service = UserService(db)
        user = user_service.update_user_role(user_id, new_role)

        return UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.put("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Deactivate a user account (admin only).

    - **user_id**: ID of the user to deactivate
    """
    try:
        user_service = UserService(db)
        user = user_service.deactivate_user(user_id)

        return UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.put("/users/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Activate a user account (admin only).

    - **user_id**: ID of the user to activate
    """
    try:
        user_service = UserService(db)
        user = user_service.activate_user(user_id)

        return UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
