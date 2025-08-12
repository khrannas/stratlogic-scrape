from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.schemas import user_schemas
from src.services import user_service
from src.core.database import get_db

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post("/", response_model=user_schemas.User)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: user_schemas.UserCreate,
):
    """
    Create new user.
    """
    user = user_service.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = user_service.get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = user_service.create_user(db, user_in=user_in)
    return user

@router.get("/", response_model=list[user_schemas.User])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve users.
    """
    users = user_service.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=user_schemas.User)
def read_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
):
    """
    Get user by ID.
    """
    user = user_service.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=user_schemas.User)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    user_in: user_schemas.UserUpdate,
):
    """
    Update user.
    """
    user = user_service.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = user_service.update_user(db, db_obj=user, obj_in=user_in)
    return user

@router.delete("/{user_id}")
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
):
    """
    Delete user.
    """
    user = user_service.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_service.delete_user(db, user_id=user_id)
    return {"message": "User deleted successfully"}
