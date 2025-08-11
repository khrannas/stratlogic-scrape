"""
Custom exception classes for the StratLogic Scraping System.

This module defines custom exceptions for different types of errors
that can occur in the system, providing standardized error handling
and meaningful error messages.
"""

from typing import Any, Dict, Optional
from uuid import UUID


class StratLogicException(Exception):
    """Base exception class for all StratLogic exceptions."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


# Authentication and Authorization Exceptions
class AuthenticationError(StratLogicException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: Dict[str, Any] = None):
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class AuthorizationError(StratLogicException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, message: str = "Insufficient permissions", details: Dict[str, Any] = None):
        super().__init__(message, "AUTHORIZATION_ERROR", details)


class SessionExpiredError(StratLogicException):
    """Raised when user session has expired."""
    
    def __init__(self, message: str = "Session has expired", details: Dict[str, Any] = None):
        super().__init__(message, "SESSION_EXPIRED", details)


# Database Exceptions
class DatabaseError(StratLogicException):
    """Base class for database-related errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "DATABASE_ERROR", details)


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    
    def __init__(self, message: str = "Database connection failed", details: Dict[str, Any] = None):
        super().__init__(message, details)


class DatabaseQueryError(DatabaseError):
    """Raised when database query fails."""
    
    def __init__(self, message: str = "Database query failed", details: Dict[str, Any] = None):
        super().__init__(message, details)


class RecordNotFoundError(DatabaseError):
    """Raised when a requested record is not found."""
    
    def __init__(self, resource_type: str, resource_id: str, details: Dict[str, Any] = None):
        message = f"{resource_type} with id {resource_id} not found"
        super().__init__(message, details or {"resource_type": resource_type, "resource_id": resource_id})


# Storage Exceptions
class StorageError(StratLogicException):
    """Base class for storage-related errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "STORAGE_ERROR", details)


class MinIOError(StorageError):
    """Raised when MinIO operations fail."""
    
    def __init__(self, message: str = "MinIO operation failed", details: Dict[str, Any] = None):
        super().__init__(message, details)


class FileNotFoundError(StorageError):
    """Raised when a file is not found in storage."""
    
    def __init__(self, file_path: str, details: Dict[str, Any] = None):
        message = f"File not found: {file_path}"
        super().__init__(message, details or {"file_path": file_path})


class FileUploadError(StorageError):
    """Raised when file upload fails."""
    
    def __init__(self, message: str = "File upload failed", details: Dict[str, Any] = None):
        super().__init__(message, details)


# Scraping Exceptions
class ScrapingError(StratLogicException):
    """Base class for scraping-related errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "SCRAPING_ERROR", details)


class WebScrapingError(ScrapingError):
    """Raised when web scraping fails."""
    
    def __init__(self, url: str, message: str = "Web scraping failed", details: Dict[str, Any] = None):
        super().__init__(message, details or {"url": url})


class PaperScrapingError(ScrapingError):
    """Raised when paper scraping fails."""
    
    def __init__(self, paper_id: str, message: str = "Paper scraping failed", details: Dict[str, Any] = None):
        super().__init__(message, details or {"paper_id": paper_id})


class GovernmentScrapingError(ScrapingError):
    """Raised when government document scraping fails."""
    
    def __init__(self, document_url: str, message: str = "Government document scraping failed", details: Dict[str, Any] = None):
        super().__init__(message, details or {"document_url": document_url})


# Search and Content Processing Exceptions
class SearchError(StratLogicException):
    """Base class for search-related errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "SEARCH_ERROR", details)


class ContentProcessingError(StratLogicException):
    """Raised when content processing fails."""
    
    def __init__(self, message: str = "Content processing failed", details: Dict[str, Any] = None):
        super().__init__(message, "CONTENT_PROCESSING_ERROR", details)


class EmbeddingError(StratLogicException):
    """Raised when text embedding generation fails."""
    
    def __init__(self, message: str = "Text embedding generation failed", details: Dict[str, Any] = None):
        super().__init__(message, "EMBEDDING_ERROR", details)


# Rate Limiting and Security Exceptions
class RateLimitError(StratLogicException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, endpoint: str, limit: int, window: int, details: Dict[str, Any] = None):
        message = f"Rate limit exceeded for {endpoint}"
        super().__init__(message, "RATE_LIMIT_ERROR", details or {
            "endpoint": endpoint,
            "limit": limit,
            "window": window
        })


class SecurityError(StratLogicException):
    """Base class for security-related errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "SECURITY_ERROR", details)


class SuspiciousActivityError(SecurityError):
    """Raised when suspicious activity is detected."""
    
    def __init__(self, activity_type: str, message: str = "Suspicious activity detected", details: Dict[str, Any] = None):
        super().__init__(message, details or {"activity_type": activity_type})


# Validation Exceptions
class ValidationError(StratLogicException):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "VALIDATION_ERROR", details or {"field": field})


class ConfigurationError(StratLogicException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, config_key: str, message: str = "Configuration error", details: Dict[str, Any] = None):
        super().__init__(message, "CONFIGURATION_ERROR", details or {"config_key": config_key})


# External Service Exceptions
class ExternalServiceError(StratLogicException):
    """Base class for external service errors."""
    
    def __init__(self, service_name: str, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details or {"service_name": service_name})


class APIError(ExternalServiceError):
    """Raised when external API calls fail."""
    
    def __init__(self, api_name: str, status_code: int = None, message: str = "API call failed", details: Dict[str, Any] = None):
        super().__init__(api_name, message, details or {"status_code": status_code})


# Monitoring and Health Check Exceptions
class HealthCheckError(StratLogicException):
    """Raised when health check fails."""
    
    def __init__(self, service_name: str, message: str = "Health check failed", details: Dict[str, Any] = None):
        super().__init__(message, "HEALTH_CHECK_ERROR", details or {"service_name": service_name})


class MonitoringError(StratLogicException):
    """Raised when monitoring operations fail."""
    
    def __init__(self, message: str = "Monitoring operation failed", details: Dict[str, Any] = None):
        super().__init__(message, "MONITORING_ERROR", details)


# Job and Task Exceptions
class JobError(StratLogicException):
    """Base class for job-related errors."""
    
    def __init__(self, job_id: UUID, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "JOB_ERROR", details or {"job_id": str(job_id)})


class JobNotFoundError(JobError):
    """Raised when a job is not found."""
    
    def __init__(self, job_id: UUID, details: Dict[str, Any] = None):
        super().__init__(job_id, f"Job with id {job_id} not found", details)


class JobExecutionError(JobError):
    """Raised when job execution fails."""
    
    def __init__(self, job_id: UUID, message: str = "Job execution failed", details: Dict[str, Any] = None):
        super().__init__(job_id, message, details)


# Utility Functions
def get_exception_details(exception: Exception) -> Dict[str, Any]:
    """Extract details from an exception for logging and monitoring."""
    if isinstance(exception, StratLogicException):
        return {
            "error_code": exception.error_code,
            "message": exception.message,
            "details": exception.details,
            "exception_type": exception.__class__.__name__
        }
    else:
        return {
            "error_code": "UNKNOWN_ERROR",
            "message": str(exception),
            "details": {},
            "exception_type": exception.__class__.__name__
        }


def is_retryable_error(exception: Exception) -> bool:
    """Determine if an error is retryable."""
    retryable_exceptions = [
        DatabaseConnectionError,
        ExternalServiceError,
        APIError,
        JobExecutionError
    ]
    
    return any(isinstance(exception, exc_type) for exc_type in retryable_exceptions)


def get_error_status_code(exception: Exception) -> int:
    """Get appropriate HTTP status code for an exception."""
    if isinstance(exception, AuthenticationError):
        return 401
    elif isinstance(exception, AuthorizationError):
        return 403
    elif isinstance(exception, RecordNotFoundError):
        return 404
    elif isinstance(exception, ValidationError):
        return 400
    elif isinstance(exception, RateLimitError):
        return 429
    elif isinstance(exception, ConfigurationError):
        return 500
    elif isinstance(exception, (DatabaseError, StorageError, ScrapingError)):
        return 500
    else:
        return 500
