"""
Periodic worker tasks for Artemis.
"""

import logging
from uuid import UUID

from services.worker import API_ROOT  # noqa: F401
from services.worker.concurrency import AutomationConcurrencyLimiter
from src.core.config import settings
from src.domain.applications.constants import APPLICATION_STATUS_FAILED
from src.domain.applications.repository import ApplicationRepository
from src.domain.applications.factory import build_pipeline_service
from src.domain.jobs.feed_service import JobFeedService
from src.domain.jobs.repository import JobPreferencesRepository
from src.infrastructure.db.session import SessionLocal

from services.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="run_application_pipeline_async")
def run_application_pipeline_async(user_id: str, application_id: str) -> dict[str, str]:
    """Run a single application pipeline in the worker and return final status."""
    logger.info(
        "[Worker] Starting async application pipeline user_id=%s application_id=%s",
        user_id,
        application_id,
    )

    db = SessionLocal()
    limiter = AutomationConcurrencyLimiter(
        redis_url=settings.redis_url,
        global_limit=settings.automation_max_concurrent_sessions,
        per_user_limit=settings.automation_max_concurrent_sessions_per_user,
        ttl_seconds=settings.automation_session_limit_ttl_seconds,
    )
    acquired, reason = limiter.acquire(user_id=user_id)
    if not acquired:
        failure_reason = f"concurrency_limit (transient): RuntimeError: {reason}"
        logger.warning(
            "[Worker] Concurrency guard blocked pipeline user_id=%s application_id=%s reason=%s",
            user_id,
            application_id,
            reason,
        )
        try:
            application_repo = ApplicationRepository(db)
            application_repo.update_fields(
                UUID(str(application_id)),
                status=APPLICATION_STATUS_FAILED,
                failure_reason=failure_reason,
            )
        finally:
            db.close()
        raise RuntimeError(reason)

    try:
        pipeline_service = build_pipeline_service(db)
        application = pipeline_service.run_pipeline(
            user_id=UUID(str(user_id)),
            application_id=UUID(str(application_id)),
        )
        logger.info(
            "[Worker] Async pipeline complete application_id=%s status=%s",
            application_id,
            application.status,
        )
        return {
            "application_id": str(application_id),
            "status": str(application.status),
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "[Worker] Async pipeline failed application_id=%s error=%s",
            application_id,
            exc,
        )
        raise
    finally:
        limiter.release(user_id=user_id)
        db.close()


@celery_app.task(name="scan_job_feed_for_all_users")
def scan_job_feed_for_all_users() -> dict[str, int]:
    """Run the job feed scan for every user with enabled sources configured."""
    logger.info("[Worker] Starting scheduled job feed scan for all users")

    db = SessionLocal()
    try:
        preferences_repository = JobPreferencesRepository(db)
        user_ids = preferences_repository.list_user_ids_with_enabled_sources()
        logger.info("[Worker] Scheduled job feed scan will process %d user(s)", len(user_ids))
    finally:
        db.close()

    scanned_users = 0
    failed_users = 0
    total_new_jobs = 0

    for user_id in user_ids:
        try:
            new_jobs_found = JobFeedService.scan_for_user(user_id)
            scanned_users += 1
            total_new_jobs += new_jobs_found
            logger.info(
                "[Worker] Job feed scan complete for user %s: %d new job(s)",
                user_id,
                new_jobs_found,
            )
        except Exception as exc:  # noqa: BLE001
            failed_users += 1
            logger.exception("[Worker] Job feed scan failed for user %s: %s", user_id, exc)

    logger.info(
        "[Worker] Scheduled job feed scan finished: %d user(s) scanned, %d failure(s), %d new job(s)",
        scanned_users,
        failed_users,
        total_new_jobs,
    )
    return {
        "scanned_users": scanned_users,
        "failed_users": failed_users,
        "new_jobs_found": total_new_jobs,
    }