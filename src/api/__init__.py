"""
API module for StratLogic Scraping System.

This module provides FastAPI routes, dependencies, and middleware
for the RESTful API endpoints.
"""

from .dependencies import get_db, get_current_user, get_current_active_user, require_role
from .middleware import add_correlation_id, log_request

__all__ = [
    "get_db",
    "get_current_user", 
    "get_current_active_user",
    "require_role",
    "add_correlation_id",
    "log_request",
]
