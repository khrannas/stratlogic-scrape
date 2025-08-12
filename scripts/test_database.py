#!/usr/bin/env python3
"""
Test script for database models and operations.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import db_manager, get_db
from src.core.models import User, ScrapingJob, Artifact, SystemConfiguration, AuditLog
from sqlalchemy.orm import Session
import uuid

def test_database_connection():
    """Test database connection."""
    print("Testing database connection...")

    # Test health check
    is_healthy = db_manager.health_check()
    print(f"Database health check: {'✅ PASS' if is_healthy else '❌ FAIL'}")

    if not is_healthy:
        print("❌ Database connection failed!")
        return False

    return True

def test_model_creation():
    """Test creating and querying models."""
    print("\nTesting model creation...")

    try:
        # Get database session
        db = next(get_db())

        # Test User model
        print("Testing User model...")
        test_user = User(
            username="test_user",
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User",
            role="user"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✅ User created with ID: {test_user.id}")

        # Test SystemConfiguration model
        print("Testing SystemConfiguration model...")
        test_config = SystemConfiguration(
            config_key="test_config",
            config_value="test_value",
            config_type="string",
            description="Test configuration"
        )
        db.add(test_config)
        db.commit()
        db.refresh(test_config)
        print(f"✅ SystemConfiguration created with ID: {test_config.id}")

        # Test ScrapingJob model
        print("Testing ScrapingJob model...")
        test_job = ScrapingJob(
            user_id=test_user.id,
            job_type="web",
            keywords=["test", "keywords"],
            status="pending"
        )
        db.add(test_job)
        db.commit()
        db.refresh(test_job)
        print(f"✅ ScrapingJob created with ID: {test_job.id}")

        # Test Artifact model
        print("Testing Artifact model...")
        test_artifact = Artifact(
            job_id=test_job.id,
            user_id=test_user.id,
            artifact_type="web_page",
            source_url="https://example.com",
            title="Test Artifact",
            content_hash="abc123",
            minio_path="/test/path"
        )
        db.add(test_artifact)
        db.commit()
        db.refresh(test_artifact)
        print(f"✅ Artifact created with ID: {test_artifact.id}")

        # Test AuditLog model
        print("Testing AuditLog model...")
        test_audit = AuditLog(
            user_id=test_user.id,
            action="test_action",
            resource_type="user",
            resource_id=test_user.id,
            details={"test": "data"}
        )
        db.add(test_audit)
        db.commit()
        db.refresh(test_audit)
        print(f"✅ AuditLog created with ID: {test_audit.id}")

        # Test queries
        print("\nTesting queries...")

        # Query users
        users = db.query(User).all()
        print(f"✅ Found {len(users)} users")

        # Query jobs
        jobs = db.query(ScrapingJob).all()
        print(f"✅ Found {len(jobs)} jobs")

        # Query artifacts
        artifacts = db.query(Artifact).all()
        print(f"✅ Found {len(artifacts)} artifacts")

        # Query configurations
        configs = db.query(SystemConfiguration).all()
        print(f"✅ Found {len(configs)} configurations")

        # Query audit logs
        audit_logs = db.query(AuditLog).all()
        print(f"✅ Found {len(audit_logs)} audit logs")

        # Test relationships
        print("\nTesting relationships...")
        user_jobs = test_user.scraping_jobs
        print(f"✅ User has {len(user_jobs)} jobs")

        job_artifacts = test_job.artifacts
        print(f"✅ Job has {len(job_artifacts)} artifacts")

        # Clean up test data
        print("\nCleaning up test data...")
        db.delete(test_audit)
        db.delete(test_artifact)
        db.delete(test_job)
        db.delete(test_config)
        db.delete(test_user)
        db.commit()
        print("✅ Test data cleaned up")

        db.close()
        return True

    except Exception as e:
        print(f"❌ Error testing models: {e}")
        return False

def test_database_operations():
    """Test basic database operations."""
    print("\nTesting database operations...")

    try:
        db = next(get_db())

        # Test CRUD operations
        print("Testing CRUD operations...")

        # Create
        user = User(
            username="crud_test",
            email="crud@example.com",
            password_hash="hashed_password",
            full_name="CRUD Test User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ Created user: {user.username}")

        # Read
        found_user = db.query(User).filter(User.username == "crud_test").first()
        if found_user:
            print(f"✅ Found user: {found_user.username}")
        else:
            print("❌ Failed to find user")
            return False

        # Update
        found_user.full_name = "Updated CRUD Test User"
        db.commit()
        db.refresh(found_user)
        print(f"✅ Updated user: {found_user.full_name}")

        # Delete
        db.delete(found_user)
        db.commit()
        print("✅ Deleted user")

        # Verify deletion
        deleted_user = db.query(User).filter(User.username == "crud_test").first()
        if deleted_user is None:
            print("✅ User successfully deleted")
        else:
            print("❌ User still exists after deletion")
            return False

        db.close()
        return True

    except Exception as e:
        print(f"❌ Error testing database operations: {e}")
        return False

def main():
    """Main test function."""
    print("Database Models Test")
    print("=" * 50)

    # Test database connection
    if not test_database_connection():
        print("\n❌ Database connection test failed!")
        return False

    # Test model creation
    if not test_model_creation():
        print("\n❌ Model creation test failed!")
        return False

    # Test database operations
    if not test_database_operations():
        print("\n❌ Database operations test failed!")
        return False

    print("\n" + "=" * 50)
    print("✅ All database tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
