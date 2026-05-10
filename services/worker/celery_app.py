"""
Celery application for Artemis worker tasks.
"""

from celery import Celery

from services.worker import API_ROOT  # noqa: F401
from src.core.config import settings
from src.infrastructure.db import register_models

register_models()

celery_app = Celery(
    "artemis_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    timezone="UTC",
    imports=("services.worker.tasks",),
    beat_schedule={
        "scan-job-feed-for-all-users": {
            "task": "scan_job_feed_for_all_users",
            "schedule": settings.job_scan_interval_hours * 60 * 60,
        },
        "auto-archive-stale-submitted-applications": {
            "task": "auto_archive_stale_submitted_applications",
            # Run once daily
            "schedule": 24 * 60 * 60,
        },
    },
)