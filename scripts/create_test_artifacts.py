#!/usr/bin/env python3
"""
Create test artifacts for development and testing.
"""

import sys
import os
import uuid
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import get_db
from src.core.models import User, ScrapingJob, Artifact

def create_test_artifacts():
    """Create test artifacts for different source types."""
    print("Creating test artifacts...")

    db = next(get_db())

    # Get a test user
    user = db.query(User).filter(User.username == "testuser").first()
    if not user:
        print("❌ Test user not found")
        db.close()
        return

    # Check if artifacts already exist
    existing_artifacts = db.query(Artifact).count()
    if existing_artifacts > 0:
        print(f"⚠️  {existing_artifacts} artifacts already exist, skipping artifact creation")
        db.close()
        return

    # Create test scraping jobs
    jobs = []
    job_types = ["web_scraper", "paper_scraper", "government_scraper"]

    for job_type in job_types:
        job = ScrapingJob(
            user_id=user.id,
            job_type=job_type,
            keywords=["test", "sample"],
            max_results=5,
            status="completed",
            progress=100,
            total_items=5,
            completed_items=5,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db.add(job)
        jobs.append(job)

    db.commit()  # Commit to get job IDs

    # Create test artifacts for each job
    test_artifacts = [
        {
            "title": "Sample Web Page Content",
            "source_url": "https://example.com/sample-page",
            "artifact_type": "web_page",
            "content_hash": "abc123hash",
            "file_size": 1024,
            "mime_type": "text/html",
            "minio_path": "/artifacts/web/sample-page.html",
            "is_public": True
        },
        {
            "title": "Research Paper on AI",
            "source_url": "https://arxiv.org/abs/2023.12345",
            "artifact_type": "research_paper",
            "content_hash": "def456hash",
            "file_size": 2048,
            "mime_type": "application/pdf",
            "minio_path": "/artifacts/papers/ai-research.pdf",
            "is_public": True
        },
        {
            "title": "Government Report on Technology",
            "source_url": "https://www.gov.uk/report/tech-2023",
            "artifact_type": "government_document",
            "content_hash": "ghi789hash",
            "file_size": 3072,
            "mime_type": "application/pdf",
            "minio_path": "/artifacts/gov/tech-report.pdf",
            "is_public": True
        },
        {
            "title": "Another Web Article",
            "source_url": "https://techcrunch.com/article-2023",
            "artifact_type": "web_page",
            "content_hash": "jkl012hash",
            "file_size": 1536,
            "mime_type": "text/html",
            "minio_path": "/artifacts/web/techcrunch-article.html",
            "is_public": False
        },
        {
            "title": "Academic Paper on Machine Learning",
            "source_url": "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=123456",
            "artifact_type": "research_paper",
            "content_hash": "mno345hash",
            "file_size": 4096,
            "mime_type": "application/pdf",
            "minio_path": "/artifacts/papers/ml-paper.pdf",
            "is_public": True
        }
    ]

    # Create artifacts and assign them to jobs
    for i, artifact_data in enumerate(test_artifacts):
        job_index = i % len(jobs)
        artifact = Artifact(
            job_id=jobs[job_index].id,
            user_id=user.id,
            **artifact_data
        )
        db.add(artifact)

    db.commit()
    print(f"✅ Created {len(test_artifacts)} test artifacts")
    db.close()

def verify_artifacts():
    """Verify that artifacts were created successfully."""
    print("\nVerifying artifacts...")

    db = next(get_db())

    # Count artifacts
    artifact_count = db.query(Artifact).count()
    job_count = db.query(ScrapingJob).count()

    print(f"✅ Artifacts: {artifact_count}")
    print(f"✅ Jobs: {job_count}")

    # List artifacts with their job types
    artifacts = db.query(Artifact).join(ScrapingJob).all()
    print("\nArtifacts:")
    for artifact in artifacts:
        print(f"  - {artifact.title} ({artifact.job.job_type})")

    db.close()

def main():
    """Main function."""
    print("StratLogic Scraping System - Test Artifacts")
    print("=" * 50)

    try:
        create_test_artifacts()
        verify_artifacts()

        print("\n" + "=" * 50)
        print("✅ Test artifacts creation completed successfully!")

        return True

    except Exception as e:
        print(f"\n❌ Error creating test artifacts: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
