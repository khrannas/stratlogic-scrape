import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.core.models.user import User
from src.core.security import get_password_hash
from tests.api.conftest import get_test_db

client = TestClient(app)

@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User"
    }

@pytest.fixture
def test_user(db: Session, test_user_data):
    """Create a test user in the database"""
    user = User(
        email=test_user_data["email"],
        username=test_user_data["username"],
        password_hash=get_password_hash(test_user_data["password"]),
        full_name=test_user_data["full_name"],
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def admin_user(db: Session):
    """Create an admin user in the database"""
    user = User(
        email="admin@example.com",
        username="admin",
        password_hash=get_password_hash("adminpassword123"),
        full_name="Admin User",
        role="admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

class TestUserRegistration:
    def test_register_user_success(self, test_user_data):
        """Test successful user registration"""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["username"] == test_user_data["username"]
        assert data["full_name"] == test_user_data["full_name"]
        assert data["role"] == "user"
        assert data["is_active"] is True
        assert "password" not in data

    def test_register_user_duplicate_email(self, test_user, test_user_data):
        """Test registration with duplicate email"""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_register_user_invalid_data(self):
        """Test registration with invalid data"""
        invalid_data = {
            "email": "invalid-email",
            "username": "ab",  # Too short
            "password": "123",  # Too short
            "full_name": "Test User"
        }
        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422

class TestUserLogin:
    def test_login_success(self, test_user, test_user_data):
        """Test successful user login"""
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_invalid_credentials(self, test_user):
        """Test login with invalid credentials"""
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "testpassword123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

class TestProtectedEndpoints:
    def test_get_current_user_with_valid_token(self, test_user, test_user_data):
        """Test accessing protected endpoint with valid token"""
        # First login to get token
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]

        # Use token to access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["username"] == test_user_data["username"]

    def test_get_current_user_without_token(self):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403

    def test_get_current_user_with_invalid_token(self):
        """Test accessing protected endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

class TestAdminEndpoints:
    def test_update_user_role_admin_success(self, admin_user, test_user):
        """Test admin updating user role"""
        # Login as admin
        login_data = {
            "email": "admin@example.com",
            "password": "adminpassword123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]

        # Update user role
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put(
            f"/api/v1/auth/users/{test_user.id}/role",
            json={"new_role": "moderator"},
            headers=headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["role"] == "moderator"

    def test_update_user_role_non_admin(self, test_user, test_user_data):
        """Test non-admin trying to update user role"""
        # Login as regular user
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]

        # Try to update user role
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put(
            f"/api/v1/auth/users/{test_user.id}/role",
            json={"new_role": "moderator"},
            headers=headers
        )
        assert response.status_code == 403
        assert "Admin role required" in response.json()["detail"]

    def test_deactivate_user_admin_success(self, admin_user, test_user):
        """Test admin deactivating user"""
        # Login as admin
        login_data = {
            "email": "admin@example.com",
            "password": "adminpassword123"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]

        # Deactivate user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.put(
            f"/api/v1/auth/users/{test_user.id}/deactivate",
            headers=headers
        )
        assert response.status_code == 200

        data = response.json()
        assert data["is_active"] is False

class TestLogout:
    def test_logout_success(self, test_user, test_user_data):
        """Test user logout"""
        # First login to get token
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        token = login_response.json()["access_token"]

        # Logout
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
