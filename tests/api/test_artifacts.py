"""
Tests for artifacts API endpoints.
"""

import pytest
from uuid import uuid4
from io import BytesIO


class TestArtifactsAPI:
    """Test suite for artifacts API endpoints."""

    def test_create_artifact_success(self, client, sample_artifact_data):
        """Test successful artifact creation."""
        response = client.post("/api/v1/artifacts/", json=sample_artifact_data)

        assert response.status_code == 200
        data = response.json()

        # Check that all fields are returned
        assert data["name"] == sample_artifact_data["name"]
        assert data["description"] == sample_artifact_data["description"]
        assert data["artifact_type"] == sample_artifact_data["artifact_type"]
        assert data["source_url"] == sample_artifact_data["source_url"]
        assert data["job_id"] == sample_artifact_data["job_id"]
        assert data["user_id"] == sample_artifact_data["user_id"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_artifact_invalid_data(self, client):
        """Test artifact creation with invalid data fails."""
        invalid_data = {
            "name": "",  # Empty name
            "source_url": "not-a-url",  # Invalid URL
            "artifact_type": "invalid_type",  # Invalid artifact type
            "job_id": "invalid-uuid",  # Invalid UUID
            "user_id": "invalid-uuid"  # Invalid UUID
        }

        response = client.post("/api/v1/artifacts/", json=invalid_data)

        assert response.status_code == 422

    def test_get_artifacts_list(self, client, sample_artifact_data):
        """Test retrieving list of artifacts."""
        # Create an artifact first
        client.post("/api/v1/artifacts/", json=sample_artifact_data)

        response = client.get("/api/v1/artifacts/")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1

        # Check that the created artifact is in the list
        artifact_found = any(artifact["name"] == sample_artifact_data["name"] for artifact in data)
        assert artifact_found

    def test_get_artifacts_pagination(self, client, sample_artifact_data):
        """Test artifacts list pagination."""
        # Create multiple artifacts
        for i in range(5):
            artifact_data = sample_artifact_data.copy()
            artifact_data["name"] = f"Artifact {i}"
            artifact_data["source_url"] = f"https://example{i}.com/document.pdf"
            client.post("/api/v1/artifacts/", json=artifact_data)

        # Test with pagination
        response = client.get("/api/v1/artifacts/?skip=0&limit=3")

        assert response.status_code == 200
        data = response.json()

        assert len(data) <= 3

    def test_get_artifact_by_id_success(self, client, sample_artifact_data):
        """Test successful artifact retrieval by ID."""
        # Create an artifact
        create_response = client.post("/api/v1/artifacts/", json=sample_artifact_data)
        artifact_id = create_response.json()["id"]

        # Get artifact by ID
        response = client.get(f"/api/v1/artifacts/{artifact_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == artifact_id
        assert data["name"] == sample_artifact_data["name"]
        assert data["source_url"] == sample_artifact_data["source_url"]

    def test_get_artifact_by_id_not_found(self, client):
        """Test artifact retrieval with non-existent ID."""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/artifacts/{fake_id}")

        assert response.status_code == 404
        assert "Artifact not found" in response.json()["detail"]

    def test_update_artifact_success(self, client, sample_artifact_data):
        """Test successful artifact update."""
        # Create an artifact
        create_response = client.post("/api/v1/artifacts/", json=sample_artifact_data)
        artifact_id = create_response.json()["id"]

        # Update artifact
        update_data = {
            "name": "Updated Artifact Name",
            "description": "Updated description",
            "artifact_type": "image"
        }
        response = client.put(f"/api/v1/artifacts/{artifact_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Updated Artifact Name"
        assert data["description"] == "Updated description"
        assert data["artifact_type"] == "image"
        assert data["source_url"] == sample_artifact_data["source_url"]  # Unchanged
        assert data["job_id"] == sample_artifact_data["job_id"]  # Unchanged

    def test_update_artifact_not_found(self, client):
        """Test artifact update with non-existent ID."""
        fake_id = str(uuid4())
        update_data = {"name": "Updated Artifact Name"}

        response = client.put(f"/api/v1/artifacts/{fake_id}", json=update_data)

        assert response.status_code == 404
        assert "Artifact not found" in response.json()["detail"]

    def test_delete_artifact_success(self, client, sample_artifact_data):
        """Test successful artifact deletion."""
        # Create an artifact
        create_response = client.post("/api/v1/artifacts/", json=sample_artifact_data)
        artifact_id = create_response.json()["id"]

        # Delete artifact
        response = client.delete(f"/api/v1/artifacts/{artifact_id}")

        assert response.status_code == 200
        assert response.json()["message"] == "Artifact deleted successfully"

        # Verify artifact is deleted
        get_response = client.get(f"/api/v1/artifacts/{artifact_id}")
        assert get_response.status_code == 404

    def test_delete_artifact_not_found(self, client):
        """Test artifact deletion with non-existent ID."""
        fake_id = str(uuid4())
        response = client.delete(f"/api/v1/artifacts/{fake_id}")

        assert response.status_code == 404
        assert "Artifact not found" in response.json()["detail"]

    def test_upload_artifact_file_missing_artifact_id(self, client):
        """Test file upload without artifact ID fails."""
        # Create a test file
        test_file = BytesIO(b"test file content")

        response = client.post(
            "/api/v1/artifacts/upload",
            files={"file": ("test.txt", test_file, "text/plain")}
        )

        assert response.status_code == 400
        assert "Artifact ID is required" in response.json()["detail"]

    def test_upload_artifact_file_artifact_not_found(self, client):
        """Test file upload for non-existent artifact fails."""
        fake_id = str(uuid4())
        test_file = BytesIO(b"test file content")

        response = client.post(
            "/api/v1/artifacts/upload",
            files={"file": ("test.txt", test_file, "text/plain")},
            data={"artifact_id": fake_id}
        )

        assert response.status_code == 404
        assert "Artifact not found" in response.json()["detail"]

    def test_download_artifact_file_not_found(self, client):
        """Test file download for non-existent artifact fails."""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/artifacts/{fake_id}/download")

        assert response.status_code == 404
        assert "Artifact not found" in response.json()["detail"]

    def test_artifact_response_structure(self, client, sample_artifact_data):
        """Test that artifact response has the expected structure."""
        # Create an artifact
        response = client.post("/api/v1/artifacts/", json=sample_artifact_data)

        assert response.status_code == 200
        data = response.json()

        # Check all required fields are present
        required_fields = [
            "id", "name", "description", "artifact_type", "source_url",
            "job_id", "user_id", "created_at", "updated_at"
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Check field types
        assert isinstance(data["id"], str)
        assert isinstance(data["name"], str)
        assert isinstance(data["description"], str)
        assert isinstance(data["artifact_type"], str)
        assert isinstance(data["source_url"], str)
        assert isinstance(data["job_id"], str)
        assert isinstance(data["user_id"], str)
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)
