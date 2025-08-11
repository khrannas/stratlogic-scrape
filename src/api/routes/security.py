"""
Security API routes for the StratLogic Scraping System.

This module provides endpoints for security monitoring, alerts, and management.
"""

from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...auth.jwt import get_current_user
from ...core.models import User
from ...services.security_service import SecurityService, get_security_service

router = APIRouter(prefix="/security", tags=["security"])


class SecurityEventResponse(BaseModel):
    """Response model for security events."""
    id: str
    event_type: str
    user_id: str = None
    username: str = None
    ip_address: str = None
    security_level: str
    created_at: str


class SecurityAlertResponse(BaseModel):
    """Response model for security alerts."""
    id: str
    alert_type: str
    title: str
    description: str = None
    security_level: str
    status: str
    user_id: str = None
    ip_address: str = None
    created_at: str


class RateLimitResponse(BaseModel):
    """Response model for rate limiting."""
    limit_exceeded: bool
    current_count: int = None
    limit: int = None
    remaining: int = None


class SecurityStatsResponse(BaseModel):
    """Response model for security statistics."""
    total_events: int
    events_by_type: Dict[str, int]
    events_by_level: Dict[str, int]
    recent_alerts: int
    active_sessions: int


@router.get("/events", response_model=List[SecurityEventResponse])
async def get_security_events(
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    security_service: SecurityService = Depends(get_security_service)
) -> List[SecurityEventResponse]:
    """
    Get security events for monitoring.
    
    This endpoint provides access to security event logs for monitoring
    and audit purposes. Only accessible by admin users.
    """
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        events = await security_service.get_security_events(limit=limit)
        return [SecurityEventResponse(**event) for event in events]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve security events: {str(e)}")


@router.get("/alerts", response_model=List[SecurityAlertResponse])
async def get_security_alerts(
    status: str = None,
    security_level: str = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    security_service: SecurityService = Depends(get_security_service)
) -> List[SecurityAlertResponse]:
    """
    Get security alerts.
    
    This endpoint provides access to security alerts and notifications.
    Only accessible by admin and moderator users.
    """
    if current_user.role.value not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Admin or moderator access required")
    
    try:
        # This would be implemented in the security service
        # For now, return empty list as placeholder
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve security alerts: {str(e)}")


@router.get("/stats", response_model=SecurityStatsResponse)
async def get_security_stats(
    current_user: User = Depends(get_current_user),
    security_service: SecurityService = Depends(get_security_service)
) -> SecurityStatsResponse:
    """
    Get security statistics.
    
    This endpoint provides security statistics and metrics for monitoring.
    Only accessible by admin users.
    """
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # This would be implemented in the security service
        # For now, return placeholder data
        return SecurityStatsResponse(
            total_events=0,
            events_by_type={},
            events_by_level={},
            recent_alerts=0,
            active_sessions=0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve security stats: {str(e)}")


@router.post("/rate-limit/check", response_model=RateLimitResponse)
async def check_rate_limit(
    endpoint: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    security_service: SecurityService = Depends(get_security_service)
) -> RateLimitResponse:
    """
    Check rate limiting for current user.
    
    This endpoint allows checking the current rate limit status for a user.
    """
    try:
        client_ip = request.client.host
        allowed, details = await security_service.check_rate_limit(
            current_user.id, client_ip, endpoint
        )
        
        return RateLimitResponse(
            limit_exceeded=not allowed,
            current_count=details.get("current_count"),
            limit=details.get("limit"),
            remaining=details.get("remaining")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rate limit check failed: {str(e)}")


@router.post("/session/create")
async def create_session(
    request: Request,
    current_user: User = Depends(get_current_user),
    security_service: SecurityService = Depends(get_security_service)
) -> Dict[str, str]:
    """
    Create a new user session.
    
    This endpoint creates a new session for the authenticated user.
    """
    try:
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        
        session_token = await security_service.create_user_session(
            current_user.id, client_ip, user_agent
        )
        
        return {"session_token": session_token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session creation failed: {str(e)}")


@router.post("/session/validate")
async def validate_session(
    session_token: str,
    security_service: SecurityService = Depends(get_security_service)
) -> Dict[str, Any]:
    """
    Validate a user session.
    
    This endpoint validates a session token and returns user information.
    """
    try:
        user = await security_service.validate_session(session_token)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid session token")
        
        return {
            "valid": True,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role.value
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session validation failed: {str(e)}")


@router.post("/data-access/log")
async def log_data_access(
    resource_type: str,
    resource_id: str,
    action: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    security_service: SecurityService = Depends(get_security_service)
) -> Dict[str, str]:
    """
    Log data access for audit trail.
    
    This endpoint logs data access events for security monitoring.
    """
    try:
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        
        await security_service.log_data_access(
            current_user.id, resource_type, resource_id, action, client_ip, user_agent
        )
        
        return {"status": "logged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data access logging failed: {str(e)}")


@router.get("/permissions/check")
async def check_permissions(
    required_permissions: str,
    current_user: User = Depends(get_current_user),
    security_service: SecurityService = Depends(get_security_service)
) -> Dict[str, bool]:
    """
    Check if current user has required permissions.
    
    This endpoint checks if the authenticated user has the specified permissions.
    """
    try:
        permissions = [p.strip() for p in required_permissions.split(",")]
        has_permissions = await security_service.check_permissions(current_user, permissions)
        
        return {"has_permissions": has_permissions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Permission check failed: {str(e)}")
