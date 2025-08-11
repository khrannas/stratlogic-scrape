"""
Error handling middleware for the StratLogic Scraping System.

This module provides comprehensive error handling middleware for FastAPI,
including global exception handlers, error response standardization,
and error monitoring.
"""

import traceback
import uuid
from typing import Any, Dict, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.exceptions import ExceptionMiddleware

from ...core.exceptions import (
    StratLogicException, get_exception_details, get_error_status_code,
    is_retryable_error
)
from ...services.logging_service import get_logger


logger = get_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive error handling."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and handle any errors."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        try:
            # Add request ID to headers for tracking
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as exc:
            # Log the error with request context
            await self._log_error(request, exc, request_id)
            
            # Return standardized error response
            return await self._create_error_response(request, exc, request_id)
    
    async def _log_error(self, request: Request, exc: Exception, request_id: str):
        """Log error with comprehensive context."""
        error_details = get_exception_details(exc)
        
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "error": error_details,
            "retryable": is_retryable_error(exc),
            "traceback": traceback.format_exc() if logger.isEnabledFor("DEBUG") else None
        }
        
        if isinstance(exc, StratLogicException):
            logger.error("StratLogic exception occurred", extra=log_data)
        else:
            logger.error("Unexpected exception occurred", extra=log_data)
    
    async def _create_error_response(self, request: Request, exc: Exception, request_id: str) -> JSONResponse:
        """Create standardized error response."""
        status_code = get_error_status_code(exc)
        
        if isinstance(exc, StratLogicException):
            error_data = exc.to_dict()
        else:
            error_data = {
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            }
        
        # Add request tracking information
        error_data["request_id"] = request_id
        error_data["timestamp"] = str(uuid.uuid1().time)
        
        # Add retry information for retryable errors
        if is_retryable_error(exc):
            error_data["retryable"] = True
            error_data["retry_after"] = 60  # seconds
        
        return JSONResponse(
            status_code=status_code,
            content=error_data,
            headers={"X-Request-ID": request_id}
        )


class ValidationErrorHandler:
    """Handler for request validation errors."""
    
    @staticmethod
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        error_data = {
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {
                "errors": exc.errors(),
                "body": exc.body
            },
            "request_id": request_id,
            "timestamp": str(uuid.uuid1().time)
        }
        
        logger.warning("Request validation failed", extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "validation_errors": exc.errors()
        })
        
        return JSONResponse(
            status_code=422,
            content=error_data,
            headers={"X-Request-ID": request_id}
        )


class HTTPExceptionHandler:
    """Handler for HTTP exceptions."""
    
    @staticmethod
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        error_data = {
            "error": "HTTP_ERROR",
            "message": exc.detail,
            "details": {
                "status_code": exc.status_code
            },
            "request_id": request_id,
            "timestamp": str(uuid.uuid1().time)
        }
        
        logger.info("HTTP exception occurred", extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "status_code": exc.status_code,
            "detail": exc.detail
        })
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_data,
            headers={"X-Request-ID": request_id}
        )


class RetryMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic retry of retryable operations."""
    
    def __init__(self, app, max_retries: int = 3, retry_delay: float = 1.0):
        super().__init__(app)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    async def dispatch(self, request: Request, call_next):
        """Process request with retry logic for retryable errors."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await call_next(request)
                return response
                
            except Exception as exc:
                if not is_retryable_error(exc) or attempt == self.max_retries:
                    # Don't retry non-retryable errors or after max attempts
                    raise
                
                # Log retry attempt
                logger.warning(f"Retry attempt {attempt + 1}/{self.max_retries} for retryable error", extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "attempt": attempt + 1,
                    "max_retries": self.max_retries,
                    "error": get_exception_details(exc)
                })
                
                # Wait before retry (exponential backoff)
                import asyncio
                await asyncio.sleep(self.retry_delay * (2 ** attempt))


class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """Middleware for circuit breaker pattern implementation."""
    
    def __init__(self, app, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        super().__init__(app)
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def dispatch(self, request: Request, call_next):
        """Process request with circuit breaker logic."""
        if self.circuit_state == "OPEN":
            if self._should_attempt_reset():
                self.circuit_state = "HALF_OPEN"
            else:
                return await self._create_circuit_open_response(request)
        
        try:
            response = await call_next(request)
            
            if self.circuit_state == "HALF_OPEN":
                self._reset_circuit()
            
            return response
            
        except Exception as exc:
            if is_retryable_error(exc):
                self._record_failure()
                
                if self.failure_count >= self.failure_threshold:
                    self.circuit_state = "OPEN"
                    self.last_failure_time = uuid.uuid1().time
            
            raise
    
    def _record_failure(self):
        """Record a failure for circuit breaker."""
        self.failure_count += 1
        self.last_failure_time = uuid.uuid1().time
    
    def _reset_circuit(self):
        """Reset circuit breaker to closed state."""
        self.circuit_state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if not self.last_failure_time:
            return True
        
        current_time = uuid.uuid1().time
        time_since_failure = (current_time - self.last_failure_time) / 1e7  # Convert to seconds
        
        return time_since_failure >= self.recovery_timeout
    
    async def _create_circuit_open_response(self, request: Request) -> JSONResponse:
        """Create response when circuit is open."""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        error_data = {
            "error": "CIRCUIT_BREAKER_OPEN",
            "message": "Service temporarily unavailable due to high error rate",
            "details": {
                "failure_count": self.failure_count,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout
            },
            "request_id": request_id,
            "timestamp": str(uuid.uuid1().time),
            "retryable": True,
            "retry_after": int(self.recovery_timeout)
        }
        
        return JSONResponse(
            status_code=503,
            content=error_data,
            headers={"X-Request-ID": request_id, "Retry-After": str(int(self.recovery_timeout))}
        )


def setup_error_handling(app):
    """Setup comprehensive error handling for the FastAPI application."""
    
    # Add custom exception handlers
    app.add_exception_handler(RequestValidationError, ValidationErrorHandler.handle_validation_error)
    app.add_exception_handler(HTTPException, HTTPExceptionHandler.handle_http_exception)
    app.add_exception_handler(StarletteHTTPException, HTTPExceptionHandler.handle_http_exception)
    
    # Add custom exception handler for StratLogic exceptions
    @app.exception_handler(StratLogicException)
    async def handle_stratlogic_exception(request: Request, exc: StratLogicException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        error_data = exc.to_dict()
        error_data["request_id"] = request_id
        error_data["timestamp"] = str(uuid.uuid1().time)
        
        if is_retryable_error(exc):
            error_data["retryable"] = True
            error_data["retry_after"] = 60
        
        logger.error("StratLogic exception handled", extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "error": error_data
        })
        
        return JSONResponse(
            status_code=get_error_status_code(exc),
            content=error_data,
            headers={"X-Request-ID": request_id}
        )
    
    # Add global exception handler for unexpected errors
    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        error_data = {
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {},
            "request_id": request_id,
            "timestamp": str(uuid.uuid1().time)
        }
        
        logger.error("Unexpected exception handled", extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "error": get_exception_details(exc),
            "traceback": traceback.format_exc()
        })
        
        return JSONResponse(
            status_code=500,
            content=error_data,
            headers={"X-Request-ID": request_id}
        )


# Utility functions for error handling
def create_error_response(
    error_code: str,
    message: str,
    status_code: int = 500,
    details: Dict[str, Any] = None,
    request_id: str = None
) -> JSONResponse:
    """Create a standardized error response."""
    error_data = {
        "error": error_code,
        "message": message,
        "details": details or {},
        "timestamp": str(uuid.uuid1().time)
    }
    
    if request_id:
        error_data["request_id"] = request_id
    
    return JSONResponse(
        status_code=status_code,
        content=error_data,
        headers={"X-Request-ID": request_id} if request_id else {}
    )


def log_request_error(request: Request, exc: Exception, context: Dict[str, Any] = None):
    """Log request error with context."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    log_data = {
        "request_id": request_id,
        "method": request.method,
        "url": str(request.url),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "error": get_exception_details(exc)
    }
    
    if context:
        log_data.update(context)
    
    logger.error("Request error occurred", extra=log_data)
