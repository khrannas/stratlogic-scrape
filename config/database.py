"""
Database configuration module.

This module contains database-specific configuration and utilities.
"""

from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator

from ..src.core.config import settings


def create_database_engine():
    """Create database engine with appropriate configuration."""
    return create_engine(
        settings.database_url,
        poolclass=StaticPool,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=settings.debug,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
    )


def create_session_factory(engine):
    """Create session factory for database operations."""
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )


@contextmanager
def get_database_session():
    """Get database session as context manager."""
    engine = create_database_engine()
    SessionLocal = create_session_factory(engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def check_database_health():
    """Check database health and connectivity."""
    try:
        with get_database_session() as session:
            session.execute("SELECT 1")
        return True
    except Exception:
        return False


def get_database_info():
    """Get database connection information."""
    return {
        "url": settings.database_url.replace(settings.postgres_password, "***"),
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
    }
