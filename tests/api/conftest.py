"""
Test configuration and fixtures for API tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.core.database import get_db
from src.core.models.base import Base


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up tables
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True
    }


@pytest.fixture
def sample_job_data():
    """Sample job data for testing."""
    return {
        "name": "Test Scraping Job",
        "description": "A test job for scraping",
        "source_url": "https://example.com",
        "scraper_type": "web",
        "priority": "medium",
        "user_id": "123e4567-e89b-12d3-a456-426614174000"
    }


@pytest.fixture
def sample_artifact_data():
    """Sample artifact data for testing."""
    return {
        "name": "Test Artifact",
        "description": "A test artifact",
        "artifact_type": "document",
        "source_url": "https://example.com/document.pdf",
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "user_id": "123e4567-e89b-12d3-a456-426614174000"
    }
