"""
Database seeding script for StratLogic Scraping System.

This script creates initial data for the database including:
- Default admin user
- System configuration
- Sample data for testing
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.orm import Session
from passlib.context import CryptContext

from core.database import SessionLocal, create_tables
from core.models import User, UserRole, SystemConfig, JobStatus, ScrapingJob, Artifact, ArtifactType
from core.config import settings
from core.utils import get_logger

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_admin_user(db: Session) -> User:
    """Create default admin user."""
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            logger.info("Admin user already exists")
            return existing_admin
        
        admin_user = User(
            username="admin",
            email="admin@stratlogic.com",
            hashed_password=hash_password("admin123"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info("Created admin user: admin/admin123")
        return admin_user
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating admin user: {e}")
        raise


def create_test_user(db: Session) -> User:
    """Create a test user."""
    try:
        # Check if test user already exists
        existing_user = db.query(User).filter(User.username == "testuser").first()
        if existing_user:
            logger.info("Test user already exists")
            return existing_user
        
        test_user = User(
            username="testuser",
            email="test@stratlogic.com",
            hashed_password=hash_password("test123"),
            full_name="Test User",
            role=UserRole.USER,
            is_active=True,
            is_verified=True
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        logger.info("Created test user: testuser/test123")
        return test_user
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating test user: {e}")
        raise


def create_system_config(db: Session):
    """Create system configuration."""
    try:
        configs = [
            {
                "key": "system_name",
                "value": "StratLogic Scraping System",
                "description": "System name"
            },
            {
                "key": "system_version",
                "value": "1.0.0",
                "description": "System version"
            },
            {
                "key": "max_file_size",
                "value": "104857600",
                "description": "Maximum file size in bytes (100MB)"
            },
            {
                "key": "allowed_file_types",
                "value": "pdf,doc,docx,txt,html,json",
                "description": "Comma-separated list of allowed file types"
            },
            {
                "key": "default_language",
                "value": "en",
                "description": "Default language for content processing"
            },
            {
                "key": "max_concurrent_jobs",
                "value": "5",
                "description": "Maximum number of concurrent scraping jobs per user"
            },
            {
                "key": "job_timeout_minutes",
                "value": "30",
                "description": "Job timeout in minutes"
            },
            {
                "key": "retention_days",
                "value": "90",
                "description": "Number of days to retain artifacts"
            },
            {
                "key": "scraping_delay",
                "value": "1",
                "description": "Delay between scraping requests in seconds"
            },
            {
                "key": "max_concurrent_scrapers",
                "value": "5",
                "description": "Maximum number of concurrent scrapers"
            }
        ]
        
        for config_data in configs:
            existing = db.query(SystemConfig).filter(SystemConfig.key == config_data["key"]).first()
            if not existing:
                config = SystemConfig(**config_data)
                db.add(config)
        
        db.commit()
        logger.info("Created system configuration")
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating system configuration: {e}")
        raise


def create_sample_jobs(db: Session, admin_user: User, test_user: User):
    """Create sample scraping jobs."""
    try:
        sample_jobs = [
            {
                "user_id": admin_user.id,
                "job_type": "web",
                "title": "Sample Web Scraping Job",
                "description": "A sample web scraping job for testing",
                "keywords": ["python", "web scraping", "data extraction"],
                "status": JobStatus.COMPLETED,
                "progress": 100,
                "total_items": 10,
                "processed_items": 10,
                "failed_items": 0
            },
            {
                "user_id": test_user.id,
                "job_type": "paper",
                "title": "Sample Paper Scraping Job",
                "description": "A sample academic paper scraping job",
                "keywords": ["machine learning", "AI", "research"],
                "status": JobStatus.RUNNING,
                "progress": 50,
                "total_items": 20,
                "processed_items": 10,
                "failed_items": 0
            },
            {
                "user_id": test_user.id,
                "job_type": "government",
                "title": "Sample Government Document Job",
                "description": "A sample government document scraping job",
                "keywords": ["policy", "regulations", "government"],
                "status": JobStatus.PENDING,
                "progress": 0,
                "total_items": 0,
                "processed_items": 0,
                "failed_items": 0
            }
        ]
        
        for job_data in sample_jobs:
            existing = db.query(ScrapingJob).filter(
                ScrapingJob.title == job_data["title"]
            ).first()
            
            if not existing:
                job = ScrapingJob(**job_data)
                db.add(job)
        
        db.commit()
        logger.info("Created sample scraping jobs")
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating sample jobs: {e}")
        raise


def create_sample_artifacts(db: Session, admin_user: User):
    """Create sample artifacts."""
    try:
        # Get the completed job
        completed_job = db.query(ScrapingJob).filter(
            ScrapingJob.status == JobStatus.COMPLETED
        ).first()
        
        if not completed_job:
            logger.info("No completed job found, skipping sample artifacts")
            return
        
        sample_artifacts = [
            {
                "job_id": completed_job.id,
                "artifact_type": ArtifactType.WEB_PAGE,
                "title": "Python Web Scraping Guide",
                "description": "A comprehensive guide to web scraping with Python",
                "source_url": "https://example.com/python-scraping-guide",
                "file_size": 1024000,
                "mime_type": "text/html",
                "content_text": "This is a sample web page content about Python web scraping...",
                "keywords": ["python", "web scraping", "tutorial"],
                "tags": ["tutorial", "beginner", "python"]
            },
            {
                "job_id": completed_job.id,
                "artifact_type": ArtifactType.PDF,
                "title": "Data Extraction Techniques",
                "description": "Advanced techniques for data extraction",
                "source_url": "https://example.com/data-extraction.pdf",
                "file_size": 2048000,
                "mime_type": "application/pdf",
                "content_text": "This is a sample PDF content about data extraction techniques...",
                "keywords": ["data extraction", "techniques", "advanced"],
                "tags": ["advanced", "pdf", "data"]
            }
        ]
        
        for artifact_data in sample_artifacts:
            existing = db.query(Artifact).filter(
                Artifact.title == artifact_data["title"]
            ).first()
            
            if not existing:
                artifact = Artifact(**artifact_data)
                db.add(artifact)
        
        db.commit()
        logger.info("Created sample artifacts")
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating sample artifacts: {e}")
        raise


def main():
    """Main seeding function."""
    logger.info("Starting database seeding...")
    
    try:
        # Create tables if they don't exist
        create_tables()
        logger.info("Database tables created/verified")
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Create users
            admin_user = create_admin_user(db)
            test_user = create_test_user(db)
            
            # Create system configuration
            create_system_config(db)
            
            # Create sample data
            create_sample_jobs(db, admin_user, test_user)
            create_sample_artifacts(db, admin_user)
            
            logger.info("Database seeding completed successfully!")
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
