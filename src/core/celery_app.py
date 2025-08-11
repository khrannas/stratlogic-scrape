"""
Celery application configuration for background task processing.

This module configures Celery for handling asynchronous tasks
like web scraping, file processing, and data analysis.
"""

from celery import Celery
from .config import settings

# Create Celery app
celery_app = Celery(
    "stratlogic",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.services.job_scheduler",
        "src.scrapers.web_scraper.tasks",
        "src.scrapers.paper_scraper.tasks",
        "src.scrapers.government_scraper.tasks",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=settings.celery_accept_content,
    timezone=settings.celery_timezone,
    enable_utc=settings.celery_enable_utc,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    beat_schedule={
        "cleanup-old-jobs": {
            "task": "src.services.job_scheduler.cleanup_old_jobs",
            "schedule": 3600.0,  # Every hour
        },
        "health-check": {
            "task": "src.services.job_scheduler.health_check",
            "schedule": 300.0,  # Every 5 minutes
        },
    },
)

# Optional: Configure task routing
celery_app.conf.task_routes = {
    "src.scrapers.*": {"queue": "scraping"},
    "src.services.*": {"queue": "services"},
    "src.storage.*": {"queue": "storage"},
}

if __name__ == "__main__":
    celery_app.start()
