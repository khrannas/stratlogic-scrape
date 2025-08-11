"""
API routes for StratLogic Scraping System.

This module contains all FastAPI route handlers organized by functionality.
"""

from .auth import router as auth_router
from .users import router as users_router
from .jobs import router as jobs_router
from .artifacts import router as artifacts_router
from .monitoring import router as monitoring_router
from .search import router as search_router
from .performance import router as performance_router
from .security import router as security_router
from .content_processing import router as content_processing_router

__all__ = [
    "auth_router",
    "users_router",
    "jobs_router",
    "artifacts_router",
    "monitoring_router",
    "search_router",
    "performance_router",
    "security_router",
    "content_processing_router",
]
