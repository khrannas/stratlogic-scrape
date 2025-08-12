"""
Tests for API error handling.
"""

import pytest
from uuid import uuid4


class TestErrorHandling:
    """Test suite for API error handling."""

    def test_validation_error_response_format(self, client):
        """Test that validation errors return proper format."""
        # Test with invalid user data
        invalid_user_data = {
            "username": "",  # Empty username
            "email": "invalid-email",  # Invalid email format
            "full_name": "Test User"
        }

        response = client.post("/api/v1/users/", json=invalid_user_data)

        assert response.status_code == 422
        data = response.json()

        # Check error response structure
        assert "error" in data
        assert data["error"] == True
        assert "message" in data
        assert data["message"] == "Validation error"
        assert "details" in data
        assert "status_code" in data
        assert data["status_code"] == 422

    def test_not_found_error_response_format(self, client):
        """Test that not found errors return proper format."""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/users/{fake_id}")

        assert response.status_code == 404
        data = response.json()

        # Check error response structure
        assert "error" in data
        assert data["error"] == True
        assert "message" in data
        assert "User not found" in data["message"]
        assert "status_code" in data
        assert data["status_code"] == 404

    def test_bad_request_error_response_format(self, client):
        """Test that bad request errors return proper format."""
        # Try to create user with duplicate email
        user_data = {
            "username": "testuser1",
            "email": "test@example.com",
            "full_name": "Test User 1"
        }

        # Create first user
        client.post("/api/v1/users/", json=user_data)

        # Try to create second user with same email
        duplicate_data = {
            "username": "testuser2",
            "email": "test@example.com",  # Same email
            "full_name": "Test User 2"
        }

        response = client.post("/api/v1/users/", json=duplicate_data)

        assert response.status_code == 400
        data = response.json()

        # Check error response structure
        assert "error" in data
        assert data["error"] == True
        assert "message" in data
        assert "email already exists" in data["message"]
        assert "status_code" in data
        assert data["status_code"] == 400

    def test_invalid_uuid_format(self, client):
        """Test that invalid UUID format returns proper error."""
        invalid_uuid = "not-a-uuid"
        response = client.get(f"/api/v1/users/{invalid_uuid}")

        assert response.status_code == 422
        data = response.json()

        assert "error" in data
        assert data["error"] == True
        assert "message" in data
        assert "Validation error" in data["message"]

    def test_malformed_json_request(self, client):
        """Test that malformed JSON requests return proper error."""
        headers = {"Content-Type": "application/json"}
        response = client.post("/api/v1/users/", data="invalid json", headers=headers)

        assert response.status_code == 422
        data = response.json()

        assert "error" in data
        assert data["error"] == True
        assert "message" in data
        assert "Validation error" in data["message"]

    def test_method_not_allowed(self, client):
        """Test that unsupported HTTP methods return proper error."""
        # Try to use PATCH method which is not implemented
        response = client.patch("/api/v1/users/")

        assert response.status_code == 405
        data = response.json()

        assert "error" in data
        assert data["error"] == True
        assert "message" in data
        assert "Method Not Allowed" in data["message"]

    def test_invalid_url_path(self, client):
        """Test that invalid URL paths return proper error."""
        response = client.get("/api/v1/invalid-endpoint/")

        assert response.status_code == 404
        data = response.json()

        assert "error" in data
        assert data["error"] == True
        assert "message" in data
        assert "Not Found" in data["message"]

    def test_job_validation_errors(self, client):
        """Test job creation validation errors."""
        invalid_job_data = {
            "name": "",  # Empty name
            "source_url": "not-a-url",  # Invalid URL
            "scraper_type": "invalid_type",  # Invalid scraper type
            "priority": "invalid_priority"  # Invalid priority
        }

        response = client.post("/api/v1/jobs/", json=invalid_job_data)

        assert response.status_code == 422
        data = response.json()

        assert "error" in data
        assert data["error"] == True
        assert "message" in data
        assert "Validation error" in data["message"]
        assert "details" in data

    def test_artifact_validation_errors(self, client):
        """Test artifact creation validation errors."""
        invalid_artifact_data = {
            "name": "",  # Empty name
            "source_url": "not-a-url",  # Invalid URL
            "artifact_type": "invalid_type",  # Invalid artifact type
            "job_id": "invalid-uuid",  # Invalid UUID
            "user_id": "invalid-uuid"  # Invalid UUID
        }

        response = client.post("/api/v1/artifacts/", json=invalid_artifact_data)

        assert response.status_code == 422
        data = response.json()

        assert "error" in data
        assert data["error"] == True
        assert "message" in data
        assert "Validation error" in data["message"]
        assert "details" in data

    def test_pagination_validation_errors(self, client):
        """Test pagination parameter validation errors."""
        # Test with negative skip value
        response = client.get("/api/v1/users/?skip=-1")

        assert response.status_code == 422
        data = response.json()

        assert "error" in data
        assert data["error"] == True
        assert "message" in data
        assert "Validation error" in data["message"]

        # Test with negative limit value
        response = client.get("/api/v1/users/?limit=-1")

        assert response.status_code == 422
        data = response.json()

        assert "error" in data
        assert data["error"] == True
        assert "message" in data
        assert "Validation error" in data["message"]
