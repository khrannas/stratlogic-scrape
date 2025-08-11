"""
Tests for database repositories.

This module tests the repository classes and their operations.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from src.core.repositories.user import UserRepository, user_repository
from src.core.repositories.job import JobRepository, job_repository
from src.core.models import User, UserRole, ScrapingJob, JobStatus


class TestUserRepository:
    """Test UserRepository functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()
    
    @pytest.fixture
    def user_repo(self):
        """Create UserRepository instance."""
        return UserRepository()
    
    @pytest.mark.unit
    def test_get_by_username(self, user_repo, mock_db):
        """Test getting user by username."""
        mock_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = user_repo.get_by_username(mock_db, "testuser")
        
        assert result == mock_user
        mock_db.query.assert_called_once_with(User)
    
    @pytest.mark.unit
    def test_get_by_email(self, user_repo, mock_db):
        """Test getting user by email."""
        mock_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = user_repo.get_by_email(mock_db, "test@example.com")
        
        assert result == mock_user
    
    @pytest.mark.unit
    def test_get_active_users(self, user_repo, mock_db):
        """Test getting active users."""
        mock_users = [
            User(username="user1", email="user1@example.com", hashed_password="hash1"),
            User(username="user2", email="user2@example.com", hashed_password="hash2")
        ]
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = mock_users
        
        result = user_repo.get_active_users(mock_db)
        
        assert result == mock_users
        assert len(result) == 2
    
    @pytest.mark.unit
    def test_get_users_by_role(self, user_repo, mock_db):
        """Test getting users by role."""
        mock_users = [
            User(username="admin1", email="admin1@example.com", hashed_password="hash1", role=UserRole.ADMIN),
            User(username="admin2", email="admin2@example.com", hashed_password="hash2", role=UserRole.ADMIN)
        ]
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = mock_users
        
        result = user_repo.get_users_by_role(mock_db, UserRole.ADMIN)
        
        assert result == mock_users
        assert len(result) == 2
    
    @pytest.mark.unit
    def test_create_user(self, user_repo, mock_db):
        """Test creating a new user."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "hashed_password": "hashed_password",
            "full_name": "New User",
            "role": UserRole.USER
        }
        
        mock_user = User(**user_data)
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        result = user_repo.create_user(mock_db, user_data)
        
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.unit
    def test_update_user(self, user_repo, mock_db):
        """Test updating user data."""
        mock_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        
        update_data = {"full_name": "Updated Name"}
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        result = user_repo.update_user(mock_db, mock_user, update_data)
        
        assert result == mock_user
        assert mock_user.full_name == "Updated Name"
        mock_db.add.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()
    
    @pytest.mark.unit
    def test_deactivate_user(self, user_repo, mock_db):
        """Test deactivating a user."""
        mock_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        
        user_repo.get = MagicMock(return_value=mock_user)
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        
        result = user_repo.deactivate_user(mock_db, "user-id")
        
        assert result is True
        assert mock_user.is_active is False
        mock_db.add.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()
    
    @pytest.mark.unit
    def test_search_users(self, user_repo, mock_db):
        """Test searching users."""
        mock_users = [
            User(username="testuser", email="test@example.com", hashed_password="hash1"),
            User(username="testadmin", email="admin@example.com", hashed_password="hash2")
        ]
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = mock_users
        
        result = user_repo.search_users(mock_db, "test")
        
        assert result == mock_users
        assert len(result) == 2
    
    @pytest.mark.unit
    def test_get_user_stats(self, user_repo, mock_db):
        """Test getting user statistics."""
        mock_db.query.return_value.count.return_value = 10
        mock_db.query.return_value.filter.return_value.count.return_value = 8
        
        result = user_repo.get_user_stats(mock_db)
        
        assert "total_users" in result
        assert "active_users" in result
        assert "verified_users" in result
        assert "role_counts" in result


class TestJobRepository:
    """Test JobRepository functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()
    
    @pytest.fixture
    def job_repo(self):
        """Create JobRepository instance."""
        return JobRepository()
    
    @pytest.mark.unit
    def test_get_jobs_by_user(self, job_repo, mock_db):
        """Test getting jobs by user ID."""
        mock_jobs = [
            ScrapingJob(user_id="user1", job_type="web", title="Job 1"),
            ScrapingJob(user_id="user1", job_type="paper", title="Job 2")
        ]
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = mock_jobs
        
        result = job_repo.get_jobs_by_user(mock_db, "user1")
        
        assert result == mock_jobs
        assert len(result) == 2
    
    @pytest.mark.unit
    def test_get_jobs_by_status(self, job_repo, mock_db):
        """Test getting jobs by status."""
        mock_jobs = [
            ScrapingJob(user_id="user1", job_type="web", title="Job 1", status=JobStatus.COMPLETED),
            ScrapingJob(user_id="user2", job_type="paper", title="Job 2", status=JobStatus.COMPLETED)
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_jobs
        
        result = job_repo.get_jobs_by_status(mock_db, JobStatus.COMPLETED)
        
        assert result == mock_jobs
        assert len(result) == 2
    
    @pytest.mark.unit
    def test_get_running_jobs(self, job_repo, mock_db):
        """Test getting running jobs."""
        mock_jobs = [
            ScrapingJob(user_id="user1", job_type="web", title="Job 1", status=JobStatus.RUNNING)
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_jobs
        
        result = job_repo.get_running_jobs(mock_db)
        
        assert result == mock_jobs
        assert len(result) == 1
    
    @pytest.mark.unit
    def test_create_job(self, job_repo, mock_db):
        """Test creating a new job."""
        job_data = {
            "user_id": "user1",
            "job_type": "web",
            "title": "Test Job",
            "description": "Test description",
            "keywords": ["test", "web"]
        }
        
        mock_job = ScrapingJob(**job_data)
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        result = job_repo.create_job(mock_db, job_data)
        
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.unit
    def test_update_job_status(self, job_repo, mock_db):
        """Test updating job status."""
        mock_job = ScrapingJob(
            user_id="user1",
            job_type="web",
            title="Test Job",
            status=JobStatus.PENDING
        )
        
        job_repo.get = MagicMock(return_value=mock_job)
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        
        result = job_repo.update_job_status(mock_db, "job-id", JobStatus.RUNNING)
        
        assert result is True
        assert mock_job.status == JobStatus.RUNNING
        assert mock_job.started_at is not None
        mock_db.add.assert_called_once_with(mock_job)
        mock_db.commit.assert_called_once()
    
    @pytest.mark.unit
    def test_update_job_progress(self, job_repo, mock_db):
        """Test updating job progress."""
        mock_job = ScrapingJob(
            user_id="user1",
            job_type="web",
            title="Test Job",
            progress=0,
            total_items=0,
            processed_items=0
        )
        
        job_repo.get = MagicMock(return_value=mock_job)
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        
        result = job_repo.update_job_progress(mock_db, "job-id", 5, 10, 1)
        
        assert result is True
        assert mock_job.processed_items == 5
        assert mock_job.total_items == 10
        assert mock_job.failed_items == 1
        assert mock_job.progress == 50
        mock_db.add.assert_called_once_with(mock_job)
        mock_db.commit.assert_called_once()
    
    @pytest.mark.unit
    def test_cancel_job(self, job_repo, mock_db):
        """Test canceling a job."""
        job_repo.update_job_status = MagicMock(return_value=True)
        
        result = job_repo.cancel_job(mock_db, "job-id")
        
        assert result is True
        job_repo.update_job_status.assert_called_once_with(mock_db, "job-id", JobStatus.CANCELLED)
    
    @pytest.mark.unit
    def test_retry_job(self, job_repo, mock_db):
        """Test retrying a failed job."""
        mock_job = ScrapingJob(
            user_id="user1",
            job_type="web",
            title="Test Job",
            status=JobStatus.FAILED,
            error_message="Test error"
        )
        
        job_repo.get = MagicMock(return_value=mock_job)
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        
        result = job_repo.retry_job(mock_db, "job-id")
        
        assert result is True
        assert mock_job.status == JobStatus.PENDING
        assert mock_job.error_message is None
        assert mock_job.progress == 0
        mock_db.add.assert_called_once_with(mock_job)
        mock_db.commit.assert_called_once()
    
    @pytest.mark.unit
    def test_search_jobs(self, job_repo, mock_db):
        """Test searching jobs."""
        mock_jobs = [
            ScrapingJob(user_id="user1", job_type="web", title="Test Job 1"),
            ScrapingJob(user_id="user2", job_type="paper", title="Test Job 2")
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_jobs
        
        result = job_repo.search_jobs(mock_db, "test")
        
        assert result == mock_jobs
        assert len(result) == 2
    
    @pytest.mark.unit
    def test_get_job_stats(self, job_repo, mock_db):
        """Test getting job statistics."""
        mock_db.query.return_value.count.return_value = 10
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        
        result = job_repo.get_job_stats(mock_db)
        
        assert "total_jobs" in result
        assert "status_counts" in result
        assert "type_counts" in result
    
    @pytest.mark.unit
    def test_cleanup_old_jobs(self, job_repo, mock_db):
        """Test cleaning up old jobs."""
        from datetime import timedelta
        
        old_job = ScrapingJob(
            user_id="user1",
            job_type="web",
            title="Old Job",
            status=JobStatus.COMPLETED,
            updated_at=datetime.now(timezone.utc) - timedelta(days=100)
        )
        
        mock_db.query.return_value.filter.return_value.all.return_value = [old_job]
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None
        
        result = job_repo.cleanup_old_jobs(mock_db, days=90)
        
        assert result == 1
        mock_db.delete.assert_called_once_with(old_job)
        mock_db.commit.assert_called_once()


class TestRepositoryIntegration:
    """Integration tests for repositories."""
    
    @pytest.mark.integration
    def test_user_repository_global_instance(self):
        """Test global user repository instance."""
        assert user_repository is not None
        assert isinstance(user_repository, UserRepository)
        assert user_repository.model == User
    
    @pytest.mark.integration
    def test_job_repository_global_instance(self):
        """Test global job repository instance."""
        assert job_repository is not None
        assert isinstance(job_repository, JobRepository)
        assert job_repository.model == ScrapingJob
