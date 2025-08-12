"""
Custom exception classes for the StratLogic Scraper API.
"""

from typing import Any, Dict, Optional


class StratLogicException(Exception):
    """Base exception class for StratLogic Scraper API."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class UserNotFoundException(StratLogicException):
    """Raised when a user is not found."""

    def __init__(self, user_id: str):
        super().__init__(
            message=f"User with ID {user_id} not found",
            status_code=404,
            details={"user_id": user_id}
        )


class UserAlreadyExistsException(StratLogicException):
    """Raised when trying to create a user that already exists."""

    def __init__(self, email: str = None, username: str = None):
        message = "User already exists"
        if email:
            message = f"User with email {email} already exists"
        elif username:
            message = f"User with username {username} already exists"

        super().__init__(
            message=message,
            status_code=400,
            details={"email": email, "username": username}
        )


class JobNotFoundException(StratLogicException):
    """Raised when a job is not found."""

    def __init__(self, job_id: str):
        super().__init__(
            message=f"Job with ID {job_id} not found",
            status_code=404,
            details={"job_id": job_id}
        )


class JobStateException(StratLogicException):
    """Raised when trying to perform an invalid operation on a job."""

    def __init__(self, job_id: str, current_state: str, required_state: str = None):
        message = f"Invalid operation for job {job_id} in state {current_state}"
        if required_state:
            message = f"Job {job_id} must be in state {required_state}, but is in {current_state}"

        super().__init__(
            message=message,
            status_code=400,
            details={
                "job_id": job_id,
                "current_state": current_state,
                "required_state": required_state
            }
        )


class ArtifactNotFoundException(StratLogicException):
    """Raised when an artifact is not found."""

    def __init__(self, artifact_id: str):
        super().__init__(
            message=f"Artifact with ID {artifact_id} not found",
            status_code=404,
            details={"artifact_id": artifact_id}
        )


class StorageException(StratLogicException):
    """Raised when there's an error with file storage operations."""

    def __init__(self, operation: str, details: str):
        super().__init__(
            message=f"Storage error during {operation}: {details}",
            status_code=500,
            details={"operation": operation, "details": details}
        )


class ValidationException(StratLogicException):
    """Raised when input validation fails."""

    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Validation error for field '{field}': {message}",
            status_code=422,
            details={"field": field, "message": message}
        )


class DatabaseException(StratLogicException):
    """Raised when there's a database operation error."""

    def __init__(self, operation: str, details: str):
        super().__init__(
            message=f"Database error during {operation}: {details}",
            status_code=500,
            details={"operation": operation, "details": details}
        )
