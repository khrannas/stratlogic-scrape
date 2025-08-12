"""
Tests for health check endpoint.
"""

import pytest
from datetime import datetime


def test_health_check(client):
    """Test that health check endpoint returns healthy status."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["message"] == "StratLogic Scraper API is running"
    assert "timestamp" in data

    # Verify timestamp is valid ISO format
    try:
        datetime.fromisoformat(data["timestamp"])
    except ValueError:
        pytest.fail("Timestamp is not in valid ISO format")


def test_root_endpoint(client):
    """Test that root endpoint returns welcome message."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert data["message"] == "Welcome to StratLogic Scraper API"


def test_health_check_response_structure(client):
    """Test that health check response has the expected structure."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Check all required fields are present
    required_fields = ["status", "message", "timestamp"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Check field types
    assert isinstance(data["status"], str)
    assert isinstance(data["message"], str)
    assert isinstance(data["timestamp"], str)
