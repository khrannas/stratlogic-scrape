#!/usr/bin/env python3
"""
Seed data script for StratLogic Scraping System.
Populates the database with initial data for development and testing.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import get_db
from src.core.models import User, SystemConfiguration, AuditLog
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def seed_users():
    """Seed user data."""
    print("Seeding users...")

    db = next(get_db())

    # Check if users already exist
    existing_users = db.query(User).count()
    if existing_users > 0:
        print(f"⚠️  {existing_users} users already exist, skipping user seeding")
        db.close()
        return

    # Create admin user
    admin_user = User(
        username="admin",
        email="admin@stratlogic.id",
        password_hash=hash_password("admin123"),
        full_name="System Administrator",
        role="admin",
        is_active=True
    )
    db.add(admin_user)

    # Create test user
    test_user = User(
        username="testuser",
        email="test@stratlogic.id",
        password_hash=hash_password("test123"),
        full_name="Test User",
        role="user",
        is_active=True
    )
    db.add(test_user)

    # Create demo user
    demo_user = User(
        username="demo",
        email="demo@stratlogic.id",
        password_hash=hash_password("demo123"),
        full_name="Demo User",
        role="user",
        is_active=True
    )
    db.add(demo_user)

    db.commit()
    print("✅ Created 3 users: admin, testuser, demo")
    db.close()

def seed_system_configurations():
    """Seed system configuration data."""
    print("Seeding system configurations...")

    db = next(get_db())

    # Check if configurations already exist
    existing_configs = db.query(SystemConfiguration).count()
    if existing_configs > 0:
        print(f"⚠️  {existing_configs} configurations already exist, skipping configuration seeding")
        db.close()
        return

    # Default system configurations
    configs = [
        {
            "config_key": "max_jobs_per_user",
            "config_value": "10",
            "config_type": "integer",
            "description": "Maximum number of concurrent jobs per user"
        },
        {
            "config_key": "max_artifacts_per_job",
            "config_value": "1000",
            "config_type": "integer",
            "description": "Maximum number of artifacts per scraping job"
        },
        {
            "config_key": "default_job_timeout",
            "config_value": "3600",
            "config_type": "integer",
            "description": "Default job timeout in seconds"
        },
        {
            "config_key": "enable_audit_logging",
            "config_value": "true",
            "config_type": "boolean",
            "description": "Enable audit logging for all operations"
        },
        {
            "config_key": "allowed_file_types",
            "config_value": "['pdf', 'html', 'txt', 'doc', 'docx']",
            "config_type": "json",
            "description": "Allowed file types for artifact storage"
        },
        {
            "config_key": "max_file_size_mb",
            "config_value": "50",
            "config_type": "integer",
            "description": "Maximum file size in MB for artifact storage"
        },
        {
            "config_key": "retention_days",
            "config_value": "90",
            "config_type": "integer",
            "description": "Number of days to retain artifacts"
        },
        {
            "config_key": "enable_rate_limiting",
            "config_value": "true",
            "config_type": "boolean",
            "description": "Enable API rate limiting"
        },
        {
            "config_key": "rate_limit_requests",
            "config_value": "100",
            "config_type": "integer",
            "description": "Number of requests allowed per rate limit window"
        },
        {
            "config_key": "rate_limit_window_minutes",
            "config_value": "15",
            "config_type": "integer",
            "description": "Rate limit window in minutes"
        }
    ]

    for config_data in configs:
        config = SystemConfiguration(**config_data)
        db.add(config)

    db.commit()
    print(f"✅ Created {len(configs)} system configurations")
    db.close()

def seed_audit_logs():
    """Seed initial audit log entries."""
    print("Seeding audit logs...")

    db = next(get_db())

    # Get admin user
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        print("⚠️  Admin user not found, skipping audit log seeding")
        db.close()
        return

    # Check if audit logs already exist
    existing_logs = db.query(AuditLog).count()
    if existing_logs > 0:
        print(f"⚠️  {existing_logs} audit logs already exist, skipping audit log seeding")
        db.close()
        return

    # Create initial audit log entries
    audit_logs = [
        {
            "user_id": admin_user.id,
            "action": "system_initialized",
            "resource_type": "system",
            "resource_id": None,
            "details": {"message": "System initialized with seed data"}
        },
        {
            "user_id": admin_user.id,
            "action": "user_created",
            "resource_type": "user",
            "resource_id": admin_user.id,
            "details": {"username": admin_user.username, "role": admin_user.role}
        }
    ]

    for log_data in audit_logs:
        audit_log = AuditLog(**log_data)
        db.add(audit_log)

    db.commit()
    print(f"✅ Created {len(audit_logs)} audit log entries")
    db.close()

def verify_seed_data():
    """Verify that seed data was created successfully."""
    print("\nVerifying seed data...")

    db = next(get_db())

    # Count records
    user_count = db.query(User).count()
    config_count = db.query(SystemConfiguration).count()
    audit_count = db.query(AuditLog).count()

    print(f"✅ Users: {user_count}")
    print(f"✅ System Configurations: {config_count}")
    print(f"✅ Audit Logs: {audit_count}")

    # List users
    users = db.query(User).all()
    print("\nUsers:")
    for user in users:
        print(f"  - {user.username} ({user.email}) - {user.role}")

    # List some configurations
    configs = db.query(SystemConfiguration).limit(5).all()
    print("\nSample Configurations:")
    for config in configs:
        print(f"  - {config.config_key}: {config.config_value}")

    db.close()

def main():
    """Main seeding function."""
    print("StratLogic Scraping System - Seed Data")
    print("=" * 50)

    try:
        # Seed data in order
        seed_users()
        seed_system_configurations()
        seed_audit_logs()

        # Verify the data
        verify_seed_data()

        print("\n" + "=" * 50)
        print("✅ Seed data creation completed successfully!")
        print("\nDefault credentials:")
        print("  Admin: admin / admin123")
        print("  Test:  testuser / test123")
        print("  Demo:  demo / demo123")

        return True

    except Exception as e:
        print(f"\n❌ Error creating seed data: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
