"""
API middleware for StratLogic Scraping System.

This module provides middleware for request logging, correlation IDs,
and other cross-cutting concerns.
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import ASGIApp

from ..core.utils import get_logger

# Get logger
logger = get_logger(__name__)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation ID to requests."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Add correlation ID to request and response."""
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        
        # Add to request state
        request.state.correlation_id = correlation_id
        
        # Add to response headers
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Log request and response details."""
        # Start time
        start_time = time.time()
        
        # Get correlation ID
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        
        # Log request
        logger.info(
            "HTTP Request",
            correlation_id=correlation_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                "HTTP Response",
                correlation_id=correlation_id,
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                duration=duration,
            )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                "HTTP Error",
                correlation_id=correlation_id,
                method=request.method,
                url=str(request.url),
                error=str(e),
                duration=duration,
            )
            
            raise


def add_correlation_id(request: Request) -> str:
    """
    Get correlation ID from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Correlation ID
    """
    return getattr(request.state, "correlation_id", "unknown")


def log_request(request: Request, message: str, **kwargs):
    """
    Log request with correlation ID.
    
    Args:
        request: FastAPI request object
        message: Log message
        **kwargs: Additional log fields
    """
    correlation_id = add_correlation_id(request)
    logger.info(message, correlation_id=correlation_id, **kwargs)


def log_error(request: Request, message: str, error: Exception, **kwargs):
    """
    Log error with correlation ID.
    
    Args:
        request: FastAPI request object
        message: Log message
        error: Exception object
        **kwargs: Additional log fields
    """
    correlation_id = add_correlation_id(request)
    logger.error(
        message,
        correlation_id=correlation_id,
        error=str(error),
        error_type=type(error).__name__,
        **kwargs
    )
