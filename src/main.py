"""
Main FastAPI application for StratLogic Scraping System.

This module contains the main FastAPI application with all routes,
middleware, and configuration.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
from contextlib import asynccontextmanager

from .core.config import settings
from .core.database import check_database_connection
from .core.utils import get_logger

# Get logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting StratLogic Scraping System")
    
    # Check database connection
    if not check_database_connection():
        logger.error("Database connection failed")
        raise RuntimeError("Database connection failed")
    
    logger.info("Database connection successful")
    
    yield
    
    # Shutdown
    logger.info("Shutting down StratLogic Scraping System")


# Create FastAPI app
app = FastAPI(
    title="StratLogic Scraping System",
    description="A comprehensive web scraping system for collecting, processing, and storing data from multiple sources",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts,
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to StratLogic Scraping System",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        db_healthy = check_database_connection()
        
        health_status = {
            "status": "healthy" if db_healthy else "unhealthy",
            "timestamp": "2024-01-01T00:00:00Z",  # TODO: Use actual timestamp
            "services": {
                "database": "healthy" if db_healthy else "unhealthy",
                "redis": "unknown",  # TODO: Add Redis health check
                "minio": "unknown",  # TODO: Add MinIO health check
            },
            "version": "1.0.0",
        }
        
        status_code = 200 if db_healthy else 503
        return JSONResponse(content=health_status, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z",
            },
            status_code=503,
        )


@app.get("/info")
async def info():
    """System information endpoint."""
    return {
        "name": "StratLogic Scraping System",
        "version": "1.0.0",
        "description": "Comprehensive web scraping system for multiple data sources",
        "environment": settings.environment,
        "debug": settings.debug,
        "features": [
            "Web scraping with Playwright",
            "Academic paper scraping",
            "Government document scraping",
            "MinIO object storage",
            "PostgreSQL metadata storage",
            "Redis caching",
            "Celery background tasks",
            "RESTful API",
        ],
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler."""
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500},
    )


# Import and include routers
from .api.routes import auth_router, users_router, jobs_router, artifacts_router
from .api.middleware import CorrelationIDMiddleware, RequestLoggingMiddleware

# Add middleware
app.add_middleware(CorrelationIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Include API routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(jobs_router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(artifacts_router, prefix="/api/v1/artifacts", tags=["artifacts"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.reload,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
    )
