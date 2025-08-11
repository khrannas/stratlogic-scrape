"""
API routes for StratLogic Scraping System.

This module contains all FastAPI route handlers organized by functionality.
"""

from .auth import router as auth_router
from .users import router as users_router
from .jobs import router as jobs_router
from .artifacts import router as artifacts_router

__all__ = [
    "auth_router",
    "users_router", 
    "jobs_router",
    "artifacts_router",
]
