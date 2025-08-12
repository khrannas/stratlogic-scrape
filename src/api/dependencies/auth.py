from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import verify_token
from src.core.models.user import User
from src.api.schemas.auth_schemas import TokenData
from src.core.exceptions import AuthenticationError, AuthorizationError

# Security scheme for JWT tokens
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise AuthenticationError("Invalid authentication token")

    user_id: str = payload.get("sub")
    if user_id is None:
        raise AuthenticationError("Invalid authentication token")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise AuthenticationError("User not found")

    if not user.is_active:
        raise AuthenticationError("User account is disabled")

    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user"""
    if not current_user.is_active:
        raise AuthenticationError("User account is disabled")
    return current_user

def get_current_user_token_data(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Get token data from JWT token"""
    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise AuthenticationError("Invalid authentication token")

    user_id: str = payload.get("sub")
    email: str = payload.get("email")
    role: str = payload.get("role")

    if user_id is None:
        raise AuthenticationError("Invalid authentication token")

    return TokenData(user_id=user_id, email=email, role=role)

def require_role(required_role: str):
    """Dependency to require a specific role"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role and current_user.role != "admin":
            raise AuthorizationError(f"Role '{required_role}' required")
        return current_user
    return role_checker

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin role"""
    if current_user.role != "admin":
        raise AuthorizationError("Admin role required")
    return current_user

def require_user_or_admin(user_id: str, current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require either the user themselves or admin role"""
    if current_user.id != user_id and current_user.role != "admin":
        raise AuthorizationError("Access denied")
    return current_user

# Convenience functions for common role requirements
get_current_admin = require_admin
get_current_user_role = require_role("user")
get_current_moderator = require_role("moderator")
