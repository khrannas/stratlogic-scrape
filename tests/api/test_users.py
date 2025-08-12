"""
Tests for users API endpoints.
"""

import pytest
from uuid import uuid4


class TestUsersAPI:
    """Test suite for users API endpoints."""

    def test_create_user_success(self, client, sample_user_data):
        """Test successful user creation."""
        response = client.post("/api/v1/users/", json=sample_user_data)

        assert response.status_code == 200
        data = response.json()

        # Check that all fields are returned
        assert data["username"] == sample_user_data["username"]
        assert data["email"] == sample_user_data["email"]
        assert data["full_name"] == sample_user_data["full_name"]
        assert data["is_active"] == sample_user_data["is_active"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_user_duplicate_email(self, client, sample_user_data):
        """Test user creation with duplicate email fails."""
        # Create first user
        client.post("/api/v1/users/", json=sample_user_data)

        # Try to create second user with same email
        duplicate_data = sample_user_data.copy()
        duplicate_data["username"] = "different_username"
        response = client.post("/api/v1/users/", json=duplicate_data)

        assert response.status_code == 400
        assert "email already exists" in response.json()["detail"]

    def test_create_user_duplicate_username(self, client, sample_user_data):
        """Test user creation with duplicate username fails."""
        # Create first user
        client.post("/api/v1/users/", json=sample_user_data)

        # Try to create second user with same username
        duplicate_data = sample_user_data.copy()
        duplicate_data["email"] = "different@example.com"
        response = client.post("/api/v1/users/", json=duplicate_data)

        assert response.status_code == 400
        assert "username already exists" in response.json()["detail"]

    def test_create_user_invalid_data(self, client):
        """Test user creation with invalid data fails."""
        invalid_data = {
            "username": "",  # Empty username
            "email": "invalid-email",  # Invalid email
            "full_name": "Test User"
        }

        response = client.post("/api/v1/users/", json=invalid_data)

        assert response.status_code == 422

    def test_get_users_list(self, client, sample_user_data):
        """Test retrieving list of users."""
        # Create a user first
        client.post("/api/v1/users/", json=sample_user_data)

        response = client.get("/api/v1/users/")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1

        # Check that the created user is in the list
        user_found = any(user["email"] == sample_user_data["email"] for user in data)
        assert user_found

    def test_get_users_pagination(self, client, sample_user_data):
        """Test users list pagination."""
        # Create multiple users
        for i in range(5):
            user_data = sample_user_data.copy()
            user_data["username"] = f"user{i}"
            user_data["email"] = f"user{i}@example.com"
            client.post("/api/v1/users/", json=user_data)

        # Test with pagination
        response = client.get("/api/v1/users/?skip=0&limit=3")

        assert response.status_code == 200
        data = response.json()

        assert len(data) <= 3

    def test_get_user_by_id_success(self, client, sample_user_data):
        """Test successful user retrieval by ID."""
        # Create a user
        create_response = client.post("/api/v1/users/", json=sample_user_data)
        user_id = create_response.json()["id"]

        # Get user by ID
        response = client.get(f"/api/v1/users/{user_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == user_id
        assert data["username"] == sample_user_data["username"]
        assert data["email"] == sample_user_data["email"]

    def test_get_user_by_id_not_found(self, client):
        """Test user retrieval with non-existent ID."""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/users/{fake_id}")

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_update_user_success(self, client, sample_user_data):
        """Test successful user update."""
        # Create a user
        create_response = client.post("/api/v1/users/", json=sample_user_data)
        user_id = create_response.json()["id"]

        # Update user
        update_data = {
            "full_name": "Updated Name",
            "is_active": False
        }
        response = client.put(f"/api/v1/users/{user_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["full_name"] == "Updated Name"
        assert data["is_active"] == False
        assert data["username"] == sample_user_data["username"]  # Unchanged
        assert data["email"] == sample_user_data["email"]  # Unchanged

    def test_update_user_not_found(self, client):
        """Test user update with non-existent ID."""
        fake_id = str(uuid4())
        update_data = {"full_name": "Updated Name"}

        response = client.put(f"/api/v1/users/{fake_id}", json=update_data)

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]

    def test_delete_user_success(self, client, sample_user_data):
        """Test successful user deletion."""
        # Create a user
        create_response = client.post("/api/v1/users/", json=sample_user_data)
        user_id = create_response.json()["id"]

        # Delete user
        response = client.delete(f"/api/v1/users/{user_id}")

        assert response.status_code == 200
        assert response.json()["message"] == "User deleted successfully"

        # Verify user is deleted
        get_response = client.get(f"/api/v1/users/{user_id}")
        assert get_response.status_code == 404

    def test_delete_user_not_found(self, client):
        """Test user deletion with non-existent ID."""
        fake_id = str(uuid4())
        response = client.delete(f"/api/v1/users/{fake_id}")

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
