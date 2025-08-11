"""Security service for authentication, authorization, and monitoring."""

import json
import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

import redis
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.models import User, UserRole
from ..core.models.security import (
    SecurityEvent, SecurityEventType, SecurityLevel, SecurityAlert, 
    AlertStatus, ApiKey, UserSession, RateLimit, DataAccessLog
)
from ..auth.password import verify_password

logger = logging.getLogger(__name__)


class SecurityService:
    """Service for security operations and monitoring."""
    
    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client
        self.settings = get_settings()
        
        # Rate limiting configuration
        self.rate_limits = {
            "default": {"requests": 100, "window": 3600},
            "auth": {"requests": 10, "window": 300},
            "api": {"requests": 1000, "window": 3600},
            "search": {"requests": 50, "window": 300},
            "admin": {"requests": 500, "window": 3600},
        }
    
    async def authenticate_user(self, username: str, password: str, ip_address: str, user_agent: str) -> Optional[User]:
        """Authenticate user with security logging."""
        try:
            query = text("SELECT * FROM users WHERE username = :username AND is_active = true")
            result = await self.db.execute(query, {"username": username})
            user_data = result.fetchone()
            
            if not user_data or not verify_password(password, user_data.hashed_password):
                await self._log_security_event(
                    SecurityEventType.LOGIN_FAILED,
                    user_data.id if user_data else None,
                    ip_address,
                    user_agent,
                    {"username": username}
                )
                return None
            
            await self._log_security_event(
                SecurityEventType.LOGIN_SUCCESS,
                user_data.id,
                ip_address,
                user_agent,
                {"username": username}
            )
            
            return User(**dict(user_data))
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None
    
    async def check_permissions(self, user: User, required_permissions: List[str]) -> bool:
        """Check if user has required permissions."""
        role_permissions = {
            UserRole.ADMIN: ["*"],
            UserRole.MODERATOR: ["read:all", "write:own", "delete:own", "moderate:content"],
            UserRole.USER: ["read:own", "write:own", "delete:own", "create:jobs"],
            UserRole.VIEWER: ["read:own"]
        }
        
        user_permissions = role_permissions.get(user.role, [])
        return "*" in user_permissions or all(perm in user_permissions for perm in required_permissions)
    
    async def check_rate_limit(self, user_id: Optional[UUID], ip_address: str, endpoint: str) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limiting."""
        try:
            limit_config = self.rate_limits.get(endpoint, self.rate_limits["default"])
            key = f"rate_limit:{user_id or ip_address}:{endpoint}"
            
            current_count = int(self.redis.get(key) or 0)
            
            if current_count >= limit_config["requests"]:
                await self._log_security_event(
                    SecurityEventType.RATE_LIMIT_EXCEEDED,
                    user_id,
                    ip_address,
                    None,
                    {"endpoint": endpoint}
                )
                return False, {"limit_exceeded": True}
            
            self.redis.incr(key)
            self.redis.expire(key, limit_config["window"])
            
            return True, {"current_count": current_count + 1, "limit": limit_config["requests"]}
            
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            return True, {"error": str(e)}
    
    async def create_user_session(self, user_id: UUID, ip_address: str, user_agent: str) -> str:
        """Create user session."""
        try:
            session_token = secrets.token_urlsafe(32)
            session_hash = hashlib.sha256(session_token.encode()).hexdigest()
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            session = UserSession(
                user_id=user_id,
                session_token=session_hash,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at,
                last_activity_at=datetime.utcnow()
            )
            
            self.db.add(session)
            await self.db.commit()
            
            # Store in Redis
            session_data = {"user_id": str(user_id), "expires_at": expires_at.isoformat()}
            self.redis.setex(f"session:{session_hash}", 86400, json.dumps(session_data))
            
            return session_token
            
        except Exception as e:
            logger.error(f"Session creation error: {str(e)}")
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to create session")
    
    async def validate_session(self, session_token: str) -> Optional[User]:
        """Validate user session."""
        try:
            session_hash = hashlib.sha256(session_token.encode()).hexdigest()
            
            # Check Redis
            session_data = self.redis.get(f"session:{session_hash}")
            if session_data:
                session_data = json.loads(session_data)
                if datetime.fromisoformat(session_data["expires_at"]) > datetime.utcnow():
                    query = text("SELECT * FROM users WHERE id = :user_id AND is_active = true")
                    result = await self.db.execute(query, {"user_id": session_data["user_id"]})
                    user_data = result.fetchone()
                    return User(**dict(user_data)) if user_data else None
            
            return None
            
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
            return None
    
    async def log_data_access(self, user_id: UUID, resource_type: str, resource_id: UUID, action: str, ip_address: str, user_agent: str):
        """Log data access."""
        try:
            access_log = DataAccessLog(
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.db.add(access_log)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Data access logging error: {str(e)}")
            await self.db.rollback()
    
    async def get_security_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get security events."""
        try:
            query = text("""
                SELECT se.*, u.username 
                FROM security_events se
                LEFT JOIN users u ON se.user_id = u.id
                ORDER BY se.created_at DESC 
                LIMIT :limit
            """)
            result = await self.db.execute(query, {"limit": limit})
            return [dict(event) for event in result.fetchall()]
        except Exception as e:
            logger.error(f"Security events retrieval error: {str(e)}")
            return []
    
    async def _log_security_event(self, event_type: str, user_id: Optional[UUID], ip_address: Optional[str], user_agent: Optional[str], event_data: Dict[str, Any]):
        """Log security event."""
        try:
            event = SecurityEvent(
                event_type=event_type,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                event_data=json.dumps(event_data),
                security_level=SecurityLevel.HIGH if event_type in ["login_failed", "rate_limit_exceeded"] else SecurityLevel.LOW
            )
            
            self.db.add(event)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Security event logging error: {str(e)}")
            await self.db.rollback()


async def get_security_service(db: AsyncSession, redis_client: redis.Redis) -> SecurityService:
    """Get security service instance."""
    return SecurityService(db, redis_client)
