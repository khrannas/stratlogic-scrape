"""
Tests for API endpoints.

This module tests the basic API endpoints and functionality.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestAPIEndpoints:
    """Test API endpoints."""
    
    @pytest.mark.unit
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Welcome to StratLogic Scraping System"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    @pytest.mark.unit
    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        with patch('src.main.check_database_connection', return_value=True):
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["version"] == "1.0.0"
            assert "services" in data
    
    @pytest.mark.unit
    def test_health_check_database_failure(self, client):
        """Test health check endpoint with database failure."""
        with patch('src.main.check_database_connection', return_value=False):
            response = client.get("/health")
            assert response.status_code == 503
            
            data = response.json()
            assert data["status"] == "unhealthy"
    
    @pytest.mark.unit
    def test_info_endpoint(self, client):
        """Test info endpoint."""
        response = client.get("/info")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "StratLogic Scraping System"
        assert data["version"] == "1.0.0"
        assert "features" in data
        assert len(data["features"]) > 0
    
    @pytest.mark.unit
    def test_docs_endpoint(self, client):
        """Test API documentation endpoint."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.unit
    def test_redoc_endpoint(self, client):
        """Test ReDoc documentation endpoint."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestAPIErrorHandling:
    """Test API error handling."""
    
    @pytest.mark.unit
    def test_404_error(self, client):
        """Test 404 error handling."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data
        assert data["status_code"] == 404
    
    @pytest.mark.unit
    def test_500_error(self, client):
        """Test 500 error handling."""
        with patch('src.main.check_database_connection', side_effect=Exception("Test error")):
            response = client.get("/health")
            assert response.status_code == 503
            
            data = response.json()
            assert "error" in data
            assert data["status_code"] == 503


class TestAPIMiddleware:
    """Test API middleware."""
    
    @pytest.mark.unit
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/")
        assert response.status_code == 200
        
        # Check CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    @pytest.mark.unit
    def test_content_type_json(self, client):
        """Test JSON content type headers."""
        response = client.get("/")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
