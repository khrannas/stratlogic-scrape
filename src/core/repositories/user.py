"""
User repository for database operations.

This module provides the UserRepository class for user-related database operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..models import User, UserRole
from ..utils import get_logger

logger = get_logger(__name__)


class UserRepository(BaseRepository[User, dict, dict]):
    """Repository for User model operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize UserRepository with database session."""
        super().__init__(User, db)
        self.db = db
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User instance or None
        """
        try:
            result = await self.db.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: Email to search for
            
        Returns:
            User instance or None
        """
        try:
            result = await self.db.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User instance or None
        """
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    async def create(self, user: User) -> User:
        """
        Create a new user.
        
        Args:
            user: User instance to create
            
        Returns:
            Created user instance
        """
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating user: {e}")
            raise
    
    async def update(self, user: User) -> User:
        """
        Update user.
        
        Args:
            user: User instance to update
            
        Returns:
            Updated user instance
        """
        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating user: {e}")
            raise
    
    async def delete(self, user_id: UUID) -> bool:
        """
        Delete user.
        
        Args:
            user_id: User ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            user = await self.get_by_id(user_id)
            if user:
                await self.db.delete(user)
                await self.db.commit()
                return True
            return False
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """
        List users with filters.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Search term for username, email, or full name
            role: Filter by user role
            is_active: Filter by active status
            
        Returns:
            List of users
        """
        try:
            query = select(User)
            
            # Apply filters
            if search:
                search_pattern = f"%{search}%"
                query = query.where(
                    or_(
                        User.username.ilike(search_pattern),
                        User.email.ilike(search_pattern),
                        User.full_name.ilike(search_pattern)
                    )
                )
            
            if role:
                query = query.where(User.role == role)
            
            if is_active is not None:
                query = query.where(User.is_active == is_active)
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []
    
    async def get_user_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get user statistics.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user statistics
        """
        try:
            # Get total jobs
            from ..models import ScrapingJob, JobStatus
            total_jobs = await self.db.execute(
                select(ScrapingJob).where(ScrapingJob.user_id == user_id)
            )
            total_jobs = len(total_jobs.scalars().all())
            
            # Get completed jobs
            completed_jobs = await self.db.execute(
                select(ScrapingJob).where(
                    and_(ScrapingJob.user_id == user_id, ScrapingJob.status == JobStatus.COMPLETED)
                )
            )
            completed_jobs = len(completed_jobs.scalars().all())
            
            # Get failed jobs
            failed_jobs = await self.db.execute(
                select(ScrapingJob).where(
                    and_(ScrapingJob.user_id == user_id, ScrapingJob.status == JobStatus.FAILED)
                )
            )
            failed_jobs = len(failed_jobs.scalars().all())
            
            # Get total artifacts
            from ..models import Artifact
            total_artifacts = await self.db.execute(
                select(Artifact).where(Artifact.user_id == user_id)
            )
            total_artifacts = len(total_artifacts.scalars().all())
            
            # Calculate total storage used
            total_storage = await self.db.execute(
                select(Artifact.file_size).where(Artifact.user_id == user_id)
            )
            total_storage_used = sum([size for size in total_storage.scalars().all() if size])
            
            return {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "total_artifacts": total_artifacts,
                "total_storage_used": total_storage_used,
                "last_activity": None  # TODO: Implement last activity tracking
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats for {user_id}: {e}")
            return {
                "total_jobs": 0,
                "completed_jobs": 0,
                "failed_jobs": 0,
                "total_artifacts": 0,
                "total_storage_used": 0,
                "last_activity": None
            }
