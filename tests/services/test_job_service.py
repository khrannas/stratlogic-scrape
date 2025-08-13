from sqlalchemy.orm import Session
import pytest

from src.services.job_service import job_service
from src.api.schemas import job_schemas
from src.core.models.user import User

def test_create_and_get_job(db_session: Session, test_user: User):
    """
    Test creating and retrieving a scraping job.
    """
    job_in = job_schemas.ScrapingJobCreate(
        user_id=test_user.id,
        job_type="web_scraper",
        keywords=["test", "pytest"],
        configurations=[
            job_schemas.JobConfigurationCreate(config_key="depth", config_value="2")
        ]
    )

    created_job = job_service.create_job(db=db_session, job_in=job_in)

    assert created_job is not None
    assert created_job.job_type == "web_scraper"
    assert created_job.user_id == test_user.id
    assert len(created_job.configurations) == 1
    assert created_job.configurations[0].config_key == "depth"

    retrieved_job = job_service.get_job(db=db_session, job_id=created_job.id)

    assert retrieved_job is not None
    assert retrieved_job.id == created_job.id
    assert retrieved_job.keywords == ["test", "pytest"]
