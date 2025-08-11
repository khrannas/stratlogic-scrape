"""
Security middleware for the StratLogic Scraping System.

This module provides middleware for rate limiting, security headers,
request validation, and CORS security.
"""

import time
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response as StarletteResponse

from ...services.security_service import SecurityService, get_security_service
from ...core.database import get_async_session
from ...core.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Add Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""
    
    def __init__(self, app, redis_client):
        super().__init__(app)
        self.redis = redis_client
        self.settings = get_settings()
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for certain paths
        if request.url.path in ["/docs", "/redoc", "/openapi.json", "/health"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host
        
        # Determine endpoint type for rate limiting
        endpoint = self._get_endpoint_type(request.url.path)
        
        # Check rate limit
        allowed = await self._check_rate_limit(client_ip, endpoint)
        
        if not allowed:
            return StarletteResponse(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": "3600"}
            )
        
        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self._get_rate_limit(endpoint))
        response.headers["X-RateLimit-Remaining"] = str(self._get_remaining_requests(client_ip, endpoint))
        
        return response
    
    def _get_endpoint_type(self, path: str) -> str:
        """Determine endpoint type for rate limiting."""
        if path.startswith("/api/v1/auth"):
            return "auth"
        elif path.startswith("/api/v1/search"):
            return "search"
        elif path.startswith("/api/v1/admin"):
            return "admin"
        else:
            return "api"
    
    def _get_rate_limit(self, endpoint: str) -> int:
        """Get rate limit for endpoint type."""
        limits = {
            "auth": 10,
            "search": 50,
            "admin": 500,
            "api": 1000
        }
        return limits.get(endpoint, 100)
    
    async def _check_rate_limit(self, client_ip: str, endpoint: str) -> bool:
        """Check if request is within rate limit."""
        try:
            key = f"rate_limit:{client_ip}:{endpoint}"
            limit = self._get_rate_limit(endpoint)
            
            current_count = self.redis.get(key)
            current_count = int(current_count) if current_count else 0
            
            if current_count >= limit:
                return False
            
            self.redis.incr(key)
            self.redis.expire(key, 3600)  # 1 hour window
            
            return True
            
        except Exception:
            # If Redis is unavailable, allow request
            return True
    
    def _get_remaining_requests(self, client_ip: str, endpoint: str) -> int:
        """Get remaining requests for client."""
        try:
            key = f"rate_limit:{client_ip}:{endpoint}"
            limit = self._get_rate_limit(endpoint)
            current_count = int(self.redis.get(key) or 0)
            return max(0, limit - current_count)
        except Exception:
            return 0


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for request validation and sanitization."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Validate request size
        if request.headers.get("content-length"):
            content_length = int(request.headers["content-length"])
            if content_length > 10 * 1024 * 1024:  # 10MB limit
                raise HTTPException(status_code=413, detail="Request too large")
        
        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith(("application/json", "multipart/form-data", "application/x-www-form-urlencoded")):
                raise HTTPException(status_code=400, detail="Invalid content type")
        
        # Check for suspicious headers
        suspicious_headers = ["x-forwarded-for", "x-real-ip", "x-forwarded-host"]
        for header in suspicious_headers:
            if header in request.headers:
                # Log suspicious header but don't block
                print(f"Suspicious header detected: {header}")
        
        return await call_next(request)


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for security event logging."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        
        # Log request start
        await self._log_request_start(request)
        
        try:
            response = await call_next(request)
            
            # Log successful request
            await self._log_request_success(request, response, time.time() - start_time)
            
            return response
            
        except Exception as e:
            # Log failed request
            await self._log_request_failure(request, e, time.time() - start_time)
            raise
    
    async def _log_request_start(self, request: Request):
        """Log request start for security monitoring."""
        try:
            # This would integrate with the security service
            # For now, just print for debugging
            print(f"Request started: {request.method} {request.url.path} from {request.client.host}")
        except Exception:
            pass
    
    async def _log_request_success(self, request: Request, response: Response, duration: float):
        """Log successful request."""
        try:
            # This would integrate with the security service
            # For now, just print for debugging
            print(f"Request completed: {request.method} {request.url.path} - {response.status_code} in {duration:.3f}s")
        except Exception:
            pass
    
    async def _log_request_failure(self, request: Request, error: Exception, duration: float):
        """Log failed request."""
        try:
            # This would integrate with the security service
            # For now, just print for debugging
            print(f"Request failed: {request.method} {request.url.path} - {str(error)} in {duration:.3f}s")
        except Exception:
            pass


class CORSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for CORS security configuration."""
    
    def __init__(self, app, allowed_origins: list = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["http://localhost:3000", "https://localhost:3000"]
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # Add CORS headers
        origin = request.headers.get("origin")
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
        else:
            response.headers["Access-Control-Allow-Origin"] = "null"
        
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "3600"
        
        return response


def setup_security_middleware(app, redis_client):
    """Setup all security middleware."""
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, redis_client=redis_client)
    app.add_middleware(RequestValidationMiddleware)
    app.add_middleware(SecurityLoggingMiddleware)
    app.add_middleware(CORSecurityMiddleware)
