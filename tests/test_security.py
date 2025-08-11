"""
Tests for security functionality.

This module contains comprehensive tests for security models, service, and API routes.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

from src.services.security_service import SecurityService
from src.core.models.security import (
    SecurityEvent, SecurityEventType, SecurityLevel, SecurityAlert, 
    AlertStatus, ApiKey, UserSession, RateLimit, DataAccessLog
)
from src.core.models import User, UserRole


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis_client = MagicMock()
    redis_client.get.return_value = None
    redis_client.incr.return_value = 1
    redis_client.setex.return_value = True
    redis_client.delete.return_value = 1
    return redis_client


@pytest.fixture
def security_service(mock_db, mock_redis):
    """Create security service with mocked dependencies."""
    return SecurityService(mock_db, mock_redis)


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$test_hash",
        role=UserRole.USER,
        is_active=True
    )


class TestSecurityService:
    """Test cases for SecurityService."""
    
    async def test_authenticate_user_success(self, security_service, sample_user):
        """Test successful user authentication."""
        # Mock user data
        mock_row = MagicMock()
        mock_row.id = sample_user.id
        mock_row.username = sample_user.username
        mock_row.email = sample_user.email
        mock_row.hashed_password = sample_user.hashed_password
        mock_row.role = sample_user.role
        mock_row.is_active = sample_user.is_active
        
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        security_service.db.execute.return_value = mock_result
        
        # Mock password verification
        with patch('src.services.security_service.verify_password', return_value=True):
            user = await security_service.authenticate_user(
                "testuser", "password123", "192.168.1.1", "test-agent"
            )
        
        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        
        # Verify security event was logged
        security_service.db.add.assert_called()
        security_service.db.commit.assert_called()
    
    async def test_authenticate_user_failure(self, security_service):
        """Test failed user authentication."""
        # Mock no user found
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        security_service.db.execute.return_value = mock_result
        
        user = await security_service.authenticate_user(
            "nonexistent", "password123", "192.168.1.1", "test-agent"
        )
        
        assert user is None
        
        # Verify security event was logged
        security_service.db.add.assert_called()
        security_service.db.commit.assert_called()
    
    async def test_check_permissions_admin(self, security_service, sample_user):
        """Test permission checking for admin user."""
        sample_user.role = UserRole.ADMIN
        
        has_permissions = await security_service.check_permissions(
            sample_user, ["read:all", "write:all"]
        )
        
        assert has_permissions is True
    
    async def test_check_permissions_user(self, security_service, sample_user):
        """Test permission checking for regular user."""
        sample_user.role = UserRole.USER
        
        has_permissions = await security_service.check_permissions(
            sample_user, ["read:own", "write:own"]
        )
        
        assert has_permissions is True
        
        # Test insufficient permissions
        has_permissions = await security_service.check_permissions(
            sample_user, ["read:all", "admin:access"]
        )
        
        assert has_permissions is False
    
    async def test_check_rate_limit_allowed(self, security_service):
        """Test rate limiting when request is allowed."""
        security_service.redis.get.return_value = "5"  # Current count
        security_service.redis.incr.return_value = 6
        
        allowed, details = await security_service.check_rate_limit(
            uuid4(), "192.168.1.1", "api"
        )
        
        assert allowed is True
        assert details["current_count"] == 6
        assert details["limit"] == 1000  # API limit
    
    async def test_check_rate_limit_exceeded(self, security_service):
        """Test rate limiting when limit is exceeded."""
        security_service.redis.get.return_value = "1000"  # At limit
        
        allowed, details = await security_service.check_rate_limit(
            uuid4(), "192.168.1.1", "api"
        )
        
        assert allowed is False
        assert details["limit_exceeded"] is True
        
        # Verify security event was logged
        security_service.db.add.assert_called()
        security_service.db.commit.assert_called()
    
    async def test_create_user_session(self, security_service, sample_user):
        """Test user session creation."""
        session_token = await security_service.create_user_session(
            sample_user.id, "192.168.1.1", "test-agent"
        )
        
        assert session_token is not None
        assert len(session_token) > 32  # Should be a secure token
        
        # Verify session was stored in database
        security_service.db.add.assert_called()
        security_service.db.commit.assert_called()
        
        # Verify session was stored in Redis
        security_service.redis.setex.assert_called()
    
    async def test_validate_session_valid(self, security_service, sample_user):
        """Test session validation with valid session."""
        # Mock Redis session data
        session_data = {
            "user_id": str(sample_user.id),
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        security_service.redis.get.return_value = json.dumps(session_data)
        
        # Mock user data
        mock_row = MagicMock()
        mock_row.id = sample_user.id
        mock_row.username = sample_user.username
        mock_row.email = sample_user.email
        mock_row.hashed_password = sample_user.hashed_password
        mock_row.role = sample_user.role
        mock_row.is_active = sample_user.is_active
        
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        security_service.db.execute.return_value = mock_result
        
        user = await security_service.validate_session("valid_session_token")
        
        assert user is not None
        assert user.username == sample_user.username
    
    async def test_validate_session_expired(self, security_service):
        """Test session validation with expired session."""
        # Mock expired session data
        session_data = {
            "user_id": str(uuid4()),
            "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()
        }
        security_service.redis.get.return_value = json.dumps(session_data)
        
        user = await security_service.validate_session("expired_session_token")
        
        assert user is None
    
    async def test_validate_session_invalid(self, security_service):
        """Test session validation with invalid session."""
        security_service.redis.get.return_value = None
        
        user = await security_service.validate_session("invalid_session_token")
        
        assert user is None
    
    async def test_log_data_access(self, security_service, sample_user):
        """Test data access logging."""
        await security_service.log_data_access(
            sample_user.id,
            "artifact",
            uuid4(),
            "read",
            "192.168.1.1",
            "test-agent"
        )
        
        # Verify access log was created
        security_service.db.add.assert_called()
        security_service.db.commit.assert_called()
    
    async def test_get_security_events(self, security_service):
        """Test retrieving security events."""
        # Mock security events data
        mock_row1 = MagicMock()
        mock_row1.id = str(uuid4())
        mock_row1.event_type = "login_success"
        mock_row1.user_id = str(uuid4())
        mock_row1.username = "testuser"
        mock_row1.ip_address = "192.168.1.1"
        mock_row1.security_level = "low"
        mock_row1.created_at = datetime.utcnow()
        
        mock_row2 = MagicMock()
        mock_row2.id = str(uuid4())
        mock_row2.event_type = "login_failed"
        mock_row2.user_id = None
        mock_row2.username = None
        mock_row2.ip_address = "192.168.1.2"
        mock_row2.security_level = "high"
        mock_row2.created_at = datetime.utcnow()
        
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row1, mock_row2]
        security_service.db.execute.return_value = mock_result
        
        events = await security_service.get_security_events(limit=10)
        
        assert len(events) == 2
        assert events[0]["event_type"] == "login_success"
        assert events[1]["event_type"] == "login_failed"
    
    async def test_log_security_event(self, security_service):
        """Test security event logging."""
        await security_service._log_security_event(
            "login_success",
            uuid4(),
            "192.168.1.1",
            "test-agent",
            {"username": "testuser"}
        )
        
        # Verify event was created
        security_service.db.add.assert_called()
        security_service.db.commit.assert_called()


class TestSecurityModels:
    """Test cases for security models."""
    
    def test_security_event_model(self):
        """Test SecurityEvent model creation."""
        user_id = uuid4()
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user_id=user_id,
            ip_address="192.168.1.1",
            user_agent="test-agent",
            event_data='{"username": "testuser"}',
            security_level=SecurityLevel.LOW
        )
        
        assert event.event_type == SecurityEventType.LOGIN_SUCCESS
        assert event.user_id == user_id
        assert event.ip_address == "192.168.1.1"
        assert event.security_level == SecurityLevel.LOW
    
    def test_api_key_model(self):
        """Test ApiKey model creation."""
        user_id = uuid4()
        api_key = ApiKey(
            user_id=user_id,
            name="Test API Key",
            key_hash="test_hash",
            permissions='["read:own", "write:own"]',
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        assert api_key.user_id == user_id
        assert api_key.name == "Test API Key"
        assert api_key.is_active is True
    
    def test_user_session_model(self):
        """Test UserSession model creation."""
        user_id = uuid4()
        session = UserSession(
            user_id=user_id,
            session_token="test_session_hash",
            ip_address="192.168.1.1",
            user_agent="test-agent",
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            last_activity_at=datetime.utcnow()
        )
        
        assert session.user_id == user_id
        assert session.session_token == "test_session_hash"
        assert session.is_active is True
    
    def test_security_alert_model(self):
        """Test SecurityAlert model creation."""
        alert = SecurityAlert(
            alert_type="suspicious_activity",
            title="Multiple Failed Logins",
            description="User has multiple failed login attempts",
            security_level=SecurityLevel.HIGH,
            status=AlertStatus.OPEN,
            ip_address="192.168.1.1"
        )
        
        assert alert.alert_type == "suspicious_activity"
        assert alert.security_level == SecurityLevel.HIGH
        assert alert.status == AlertStatus.OPEN
    
    def test_rate_limit_model(self):
        """Test RateLimit model creation."""
        rate_limit = RateLimit(
            user_id=uuid4(),
            ip_address="192.168.1.1",
            endpoint="api",
            request_count=100,
            window_start=datetime.utcnow(),
            window_end=datetime.utcnow() + timedelta(hours=1),
            is_blocked=False
        )
        
        assert rate_limit.ip_address == "192.168.1.1"
        assert rate_limit.endpoint == "api"
        assert rate_limit.request_count == 100
        assert rate_limit.is_blocked is False
    
    def test_data_access_log_model(self):
        """Test DataAccessLog model creation."""
        user_id = uuid4()
        resource_id = uuid4()
        access_log = DataAccessLog(
            user_id=user_id,
            resource_type="artifact",
            resource_id=resource_id,
            action="read",
            ip_address="192.168.1.1",
            user_agent="test-agent"
        )
        
        assert access_log.user_id == user_id
        assert access_log.resource_type == "artifact"
        assert access_log.resource_id == resource_id
        assert access_log.action == "read"


class TestSecurityEnums:
    """Test cases for security enums."""
    
    def test_security_event_type_enum(self):
        """Test SecurityEventType enum values."""
        assert SecurityEventType.LOGIN_SUCCESS == "login_success"
        assert SecurityEventType.LOGIN_FAILED == "login_failed"
        assert SecurityEventType.RATE_LIMIT_EXCEEDED == "rate_limit_exceeded"
        assert SecurityEventType.SECURITY_ALERT == "security_alert"
    
    def test_security_level_enum(self):
        """Test SecurityLevel enum values."""
        assert SecurityLevel.LOW == "low"
        assert SecurityLevel.MEDIUM == "medium"
        assert SecurityLevel.HIGH == "high"
        assert SecurityLevel.CRITICAL == "critical"
    
    def test_alert_status_enum(self):
        """Test AlertStatus enum values."""
        assert AlertStatus.OPEN == "open"
        assert AlertStatus.INVESTIGATING == "investigating"
        assert AlertStatus.RESOLVED == "resolved"
        assert AlertStatus.FALSE_POSITIVE == "false_positive"


class TestSecurityIntegration:
    """Integration tests for security functionality."""
    
    @pytest.mark.asyncio
    async def test_full_authentication_workflow(self, security_service, sample_user):
        """Test complete authentication workflow."""
        # Mock user data
        mock_row = MagicMock()
        mock_row.id = sample_user.id
        mock_row.username = sample_user.username
        mock_row.email = sample_user.email
        mock_row.hashed_password = sample_user.hashed_password
        mock_row.role = sample_user.role
        mock_row.is_active = sample_user.is_active
        
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        security_service.db.execute.return_value = mock_result
        
        # Test authentication
        with patch('src.services.security_service.verify_password', return_value=True):
            user = await security_service.authenticate_user(
                "testuser", "password123", "192.168.1.1", "test-agent"
            )
        
        assert user is not None
        
        # Test session creation
        session_token = await security_service.create_user_session(
            user.id, "192.168.1.1", "test-agent"
        )
        
        assert session_token is not None
        
        # Test session validation
        session_data = {
            "user_id": str(user.id),
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        security_service.redis.get.return_value = json.dumps(session_data)
        
        validated_user = await security_service.validate_session(session_token)
        
        assert validated_user is not None
        assert validated_user.id == user.id
    
    @pytest.mark.asyncio
    async def test_rate_limiting_workflow(self, security_service):
        """Test complete rate limiting workflow."""
        # Test initial rate limit check
        security_service.redis.get.return_value = "0"
        security_service.redis.incr.return_value = 1
        
        allowed, details = await security_service.check_rate_limit(
            uuid4(), "192.168.1.1", "auth"
        )
        
        assert allowed is True
        assert details["current_count"] == 1
        assert details["limit"] == 10  # Auth limit
        
        # Test rate limit exceeded
        security_service.redis.get.return_value = "10"
        
        allowed, details = await security_service.check_rate_limit(
            uuid4(), "192.168.1.1", "auth"
        )
        
        assert allowed is False
        assert details["limit_exceeded"] is True
    
    @pytest.mark.asyncio
    async def test_permission_checking_workflow(self, security_service):
        """Test complete permission checking workflow."""
        # Test admin permissions
        admin_user = User(
            id=uuid4(),
            username="admin",
            email="admin@example.com",
            hashed_password="hash",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        has_permissions = await security_service.check_permissions(
            admin_user, ["read:all", "write:all", "admin:access"]
        )
        
        assert has_permissions is True
        
        # Test user permissions
        regular_user = User(
            id=uuid4(),
            username="user",
            email="user@example.com",
            hashed_password="hash",
            role=UserRole.USER,
            is_active=True
        )
        
        has_permissions = await security_service.check_permissions(
            regular_user, ["read:own", "write:own"]
        )
        
        assert has_permissions is True
        
        # Test insufficient permissions
        has_permissions = await security_service.check_permissions(
            regular_user, ["read:all", "admin:access"]
        )
        
        assert has_permissions is False
