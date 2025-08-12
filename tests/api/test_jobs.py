"""
Tests for jobs API endpoints.
"""

import pytest
from uuid import uuid4


class TestJobsAPI:
    """Test suite for jobs API endpoints."""

    def test_create_job_success(self, client, sample_job_data):
        """Test successful job creation."""
        response = client.post("/api/v1/jobs/", json=sample_job_data)

        assert response.status_code == 200
        data = response.json()

        # Check that all fields are returned
        assert data["name"] == sample_job_data["name"]
        assert data["description"] == sample_job_data["description"]
        assert data["source_url"] == sample_job_data["source_url"]
        assert data["scraper_type"] == sample_job_data["scraper_type"]
        assert data["priority"] == sample_job_data["priority"]
        assert data["user_id"] == sample_job_data["user_id"]
        assert "id" in data
        assert "status" in data
        assert "progress" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_job_invalid_data(self, client):
        """Test job creation with invalid data fails."""
        invalid_data = {
            "name": "",  # Empty name
            "source_url": "not-a-url",  # Invalid URL
            "scraper_type": "invalid_type",  # Invalid scraper type
            "user_id": "invalid-uuid"  # Invalid UUID
        }

        response = client.post("/api/v1/jobs/", json=invalid_data)

        assert response.status_code == 422

    def test_get_jobs_list(self, client, sample_job_data):
        """Test retrieving list of jobs."""
        # Create a job first
        client.post("/api/v1/jobs/", json=sample_job_data)

        response = client.get("/api/v1/jobs/")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1

        # Check that the created job is in the list
        job_found = any(job["name"] == sample_job_data["name"] for job in data)
        assert job_found

    def test_get_jobs_pagination(self, client, sample_job_data):
        """Test jobs list pagination."""
        # Create multiple jobs
        for i in range(5):
            job_data = sample_job_data.copy()
            job_data["name"] = f"Job {i}"
            job_data["source_url"] = f"https://example{i}.com"
            client.post("/api/v1/jobs/", json=job_data)

        # Test with pagination
        response = client.get("/api/v1/jobs/?skip=0&limit=3")

        assert response.status_code == 200
        data = response.json()

        assert len(data) <= 3

    def test_get_job_by_id_success(self, client, sample_job_data):
        """Test successful job retrieval by ID."""
        # Create a job
        create_response = client.post("/api/v1/jobs/", json=sample_job_data)
        job_id = create_response.json()["id"]

        # Get job by ID
        response = client.get(f"/api/v1/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == job_id
        assert data["name"] == sample_job_data["name"]
        assert data["source_url"] == sample_job_data["source_url"]

    def test_get_job_by_id_not_found(self, client):
        """Test job retrieval with non-existent ID."""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/jobs/{fake_id}")

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    def test_update_job_success(self, client, sample_job_data):
        """Test successful job update."""
        # Create a job
        create_response = client.post("/api/v1/jobs/", json=sample_job_data)
        job_id = create_response.json()["id"]

        # Update job
        update_data = {
            "name": "Updated Job Name",
            "description": "Updated description",
            "priority": "high"
        }
        response = client.put(f"/api/v1/jobs/{job_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Updated Job Name"
        assert data["description"] == "Updated description"
        assert data["priority"] == "high"
        assert data["source_url"] == sample_job_data["source_url"]  # Unchanged
        assert data["scraper_type"] == sample_job_data["scraper_type"]  # Unchanged

    def test_update_job_not_found(self, client):
        """Test job update with non-existent ID."""
        fake_id = str(uuid4())
        update_data = {"name": "Updated Job Name"}

        response = client.put(f"/api/v1/jobs/{fake_id}", json=update_data)

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    def test_delete_job_success(self, client, sample_job_data):
        """Test successful job deletion."""
        # Create a job
        create_response = client.post("/api/v1/jobs/", json=sample_job_data)
        job_id = create_response.json()["id"]

        # Delete job
        response = client.delete(f"/api/v1/jobs/{job_id}")

        assert response.status_code == 200
        assert response.json()["message"] == "Job deleted successfully"

        # Verify job is deleted
        get_response = client.get(f"/api/v1/jobs/{job_id}")
        assert get_response.status_code == 404

    def test_delete_job_not_found(self, client):
        """Test job deletion with non-existent ID."""
        fake_id = str(uuid4())
        response = client.delete(f"/api/v1/jobs/{fake_id}")

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    def test_get_job_status_success(self, client, sample_job_data):
        """Test successful job status retrieval."""
        # Create a job
        create_response = client.post("/api/v1/jobs/", json=sample_job_data)
        job_id = create_response.json()["id"]

        # Get job status
        response = client.get(f"/api/v1/jobs/{job_id}/status")

        assert response.status_code == 200
        data = response.json()

        # Check status response structure
        assert data["job_id"] == job_id
        assert "status" in data
        assert "progress" in data
        assert "created_at" in data
        assert "updated_at" in data

        # Check data types
        assert isinstance(data["status"], str)
        assert isinstance(data["progress"], (int, float))

    def test_get_job_status_not_found(self, client):
        """Test job status retrieval with non-existent ID."""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/jobs/{fake_id}/status")

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    def test_job_status_response_structure(self, client, sample_job_data):
        """Test that job status response has the expected structure."""
        # Create a job
        create_response = client.post("/api/v1/jobs/", json=sample_job_data)
        job_id = create_response.json()["id"]

        # Get job status
        response = client.get(f"/api/v1/jobs/{job_id}/status")

        assert response.status_code == 200
        data = response.json()

        # Check all required fields are present
        required_fields = ["job_id", "status", "progress", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Check field types
        assert isinstance(data["job_id"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["progress"], (int, float))
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)
