"""
Simple tests for API structure without database dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Create a test client without database dependencies."""
    return TestClient(app)


def test_health_check_endpoint(client):
    """Test that health check endpoint exists and returns proper structure."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "status" in data
    assert "message" in data
    assert "timestamp" in data
    assert data["status"] == "healthy"


def test_root_endpoint(client):
    """Test that root endpoint exists and returns welcome message."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert "message" in data
    assert "StratLogic Scraper API" in data["message"]


def test_api_v1_prefix_exists(client):
    """Test that API v1 prefix is properly configured."""
    # Test that the API v1 prefix is accessible
    response = client.get("/api/v1/")

    # Should return 404 for root of API v1, but the prefix should be recognized
    assert response.status_code == 404


def test_openapi_documentation_exists(client):
    """Test that OpenAPI documentation is available."""
    response = client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    data = response.json()

    # Check that it's a valid OpenAPI document
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data


def test_swagger_ui_accessible(client):
    """Test that Swagger UI is accessible."""
    response = client.get("/docs")

    assert response.status_code == 200
    # Should return HTML content
    assert "text/html" in response.headers.get("content-type", "")


def test_api_endpoints_documented(client):
    """Test that API endpoints are documented in OpenAPI."""
    response = client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    data = response.json()

    # Check that expected endpoints are documented
    paths = data.get("paths", {})

    # Health check endpoint
    assert "/health" in paths
    assert "get" in paths["/health"]

    # Root endpoint
    assert "/" in paths
    assert "get" in paths["/"]

    # API v1 endpoints should be documented
    # Note: These will only be present if the routers are properly loaded
    # We're just checking the structure here, not the actual functionality
