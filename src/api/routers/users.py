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
    Create a new user account.

    This endpoint allows you to register a new user in the system. The user will be created
    with the provided information and a unique ID will be generated.

    **Request Body:**
    - `username`: Unique username for the account
    - `email`: Valid email address (must be unique)
    - `full_name`: User's full name
    - `is_active`: Whether the user account is active (default: True)

    **Returns:**
    - User object with generated ID and timestamps

    **Raises:**
    - 400: If user with same email or username already exists
    - 422: If request body validation fails
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
    Retrieve a list of users with pagination support.

    This endpoint returns a paginated list of all users in the system. You can control
    the number of results returned and the starting point for pagination.

    **Query Parameters:**
    - `skip`: Number of records to skip (default: 0)
    - `limit`: Maximum number of records to return (default: 100, max: 1000)

    **Returns:**
    - List of user objects

    **Example:**
    ```
    GET /api/v1/users?skip=0&limit=10
    ```
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
    Retrieve a specific user by their unique ID.

    This endpoint returns detailed information about a single user identified by their ID.

    **Path Parameters:**
    - `user_id`: Unique identifier of the user (UUID format)

    **Returns:**
    - User object with complete details

    **Raises:**
    - 404: If user with the specified ID is not found

    **Example:**
    ```
    GET /api/v1/users/123e4567-e89b-12d3-a456-426614174000
    ```
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
    Update an existing user's information.

    This endpoint allows you to modify user details. Only the fields provided in the
    request body will be updated; other fields will remain unchanged.

    **Path Parameters:**
    - `user_id`: Unique identifier of the user to update (UUID format)

    **Request Body:**
    - `username`: New username (optional)
    - `email`: New email address (optional)
    - `full_name`: New full name (optional)
    - `is_active`: New active status (optional)

    **Returns:**
    - Updated user object

    **Raises:**
    - 404: If user with the specified ID is not found
    - 422: If request body validation fails

    **Example:**
    ```
    PUT /api/v1/users/123e4567-e89b-12d3-a456-426614174000
    {
        "full_name": "John Doe Updated",
        "is_active": false
    }
    ```
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
    Delete a user account permanently.

    This endpoint removes a user from the system. This action is irreversible and will
    delete all associated data for the user.

    **Path Parameters:**
    - `user_id`: Unique identifier of the user to delete (UUID format)

    **Returns:**
    - Success message confirming deletion

    **Raises:**
    - 404: If user with the specified ID is not found

    **Example:**
    ```
    DELETE /api/v1/users/123e4567-e89b-12d3-a456-426614174000
    ```

    **Response:**
    ```json
    {
        "message": "User deleted successfully"
    }
    ```
    """
    user = user_service.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_service.delete_user(db, user_id=user_id)
    return {"message": "User deleted successfully"}
