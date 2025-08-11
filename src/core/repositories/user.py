"""
User repository for database operations.

This module provides the UserRepository class for user-related database operations.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .base import BaseRepository
from ..models import User, UserRole
from ..utils import get_logger

logger = get_logger(__name__)


class UserRepository(BaseRepository[User, dict, dict]):
    """Repository for User model operations."""
    
    def __init__(self):
        """Initialize UserRepository."""
        super().__init__(User)
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            db: Database session
            username: Username to search for
            
        Returns:
            User instance or None
        """
        return self.get_by_field(db, "username", username)
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            db: Database session
            email: Email to search for
            
        Returns:
            User instance or None
        """
        return self.get_by_field(db, "email", email)
    
    def get_active_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all active users.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of active users
        """
        try:
            return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    def get_users_by_role(self, db: Session, role: UserRole, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get users by role.
        
        Args:
            db: Database session
            role: User role to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of users with specified role
        """
        try:
            return db.query(User).filter(User.role == role).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting users by role {role}: {e}")
            return []
    
    def create_user(self, db: Session, user_data: dict) -> Optional[User]:
        """
        Create a new user.
        
        Args:
            db: Database session
            user_data: User data dictionary
            
        Returns:
            Created user instance or None
        """
        try:
            user = User(**user_data)
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {e}")
            return None
    
    def update_user(self, db: Session, user: User, update_data: dict) -> Optional[User]:
        """
        Update user data.
        
        Args:
            db: Database session
            user: User instance to update
            update_data: Data to update
            
        Returns:
            Updated user instance or None
        """
        try:
            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user: {e}")
            return None
    
    def deactivate_user(self, db: Session, user_id: str) -> bool:
        """
        Deactivate a user.
        
        Args:
            db: Database session
            user_id: User ID to deactivate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            user = self.get(db, user_id)
            if user:
                user.is_active = False
                db.add(user)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error deactivating user {user_id}: {e}")
            return False
    
    def activate_user(self, db: Session, user_id: str) -> bool:
        """
        Activate a user.
        
        Args:
            db: Database session
            user_id: User ID to activate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            user = self.get(db, user_id)
            if user:
                user.is_active = True
                db.add(user)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error activating user {user_id}: {e}")
            return False
    
    def verify_user(self, db: Session, user_id: str) -> bool:
        """
        Verify a user account.
        
        Args:
            db: Database session
            user_id: User ID to verify
            
        Returns:
            True if successful, False otherwise
        """
        try:
            user = self.get(db, user_id)
            if user:
                user.is_verified = True
                db.add(user)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error verifying user {user_id}: {e}")
            return False
    
    def update_last_login(self, db: Session, user_id: str) -> bool:
        """
        Update user's last login timestamp.
        
        Args:
            db: Database session
            user_id: User ID to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from datetime import datetime, timezone
            user = self.get(db, user_id)
            if user:
                user.last_login = datetime.now(timezone.utc)
                db.add(user)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating last login for user {user_id}: {e}")
            return False
    
    def search_users(
        self, 
        db: Session, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """
        Search users by username, email, or full name.
        
        Args:
            db: Database session
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching users
        """
        try:
            search_pattern = f"%{search_term}%"
            return db.query(User).filter(
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.full_name.ilike(search_pattern)
                )
            ).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error searching users with term '{search_term}': {e}")
            return []
    
    def get_user_stats(self, db: Session) -> dict:
        """
        Get user statistics.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with user statistics
        """
        try:
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.is_active == True).count()
            verified_users = db.query(User).filter(User.is_verified == True).count()
            
            role_counts = {}
            for role in UserRole:
                count = db.query(User).filter(User.role == role).count()
                role_counts[role.value] = count
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "verified_users": verified_users,
                "role_counts": role_counts
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {
                "total_users": 0,
                "active_users": 0,
                "verified_users": 0,
                "role_counts": {}
            }


# Global user repository instance
user_repository = UserRepository()
