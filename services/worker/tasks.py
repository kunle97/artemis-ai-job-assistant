"""
Periodic worker tasks for Artemis.
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from celery.exceptions import Retry

from services.worker import API_ROOT  # noqa: F401
from services.worker.concurrency import AutomationConcurrencyLimiter
from src.core.config import settings
from src.domain.applications.constants import APPLICATION_STATUS_ARCHIVED, AUTO_ARCHIVE_STALE_SUBMISSION_DAYS
from src.domain.applications.repository import ApplicationRepository
from src.domain.applications.factory import build_pipeline_service
from src.domain.jobs.feed_service import JobFeedService
from src.domain.jobs.discovery_service import JobSourceDiscoveryService, build_hosted_board_url, parse_csv_urls
from src.domain.jobs.repository import JobPreferencesRepository, JobSourceDiscoveryRepository, JobSourceRepository
from src.infrastructure.db.session import SessionLocal

from services.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="run_application_pipeline_async", bind=True, max_retries=None)
def run_application_pipeline_async(self, user_id: str, application_id: str) -> dict[str, str]:
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
        logger.warning(
            "[Worker] Concurrency guard blocked pipeline user_id=%s application_id=%s reason=%s; re-queueing",
            user_id,
            application_id,
            reason,
        )
        db.close()
        raise self.retry(
            exc=RuntimeError(reason),
            countdown=settings.automation_concurrency_retry_delay_seconds,
        )

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
    except Retry:
        raise
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


@celery_app.task(name="discover_job_sources_for_all_users")
def discover_job_sources_for_all_users() -> dict[str, int]:
    """Run ATS source discovery and safe auto-promotion for users with enabled sources."""
    logger.info("[Worker] Starting scheduled job source discovery for all users")

    db = SessionLocal()
    try:
        preferences_repository = JobPreferencesRepository(db)
        source_repository = JobSourceRepository(db)
        discovery_service = JobSourceDiscoveryService(repository=JobSourceDiscoveryRepository(db))
        user_ids = preferences_repository.list_user_ids_with_enabled_sources()
        logger.info("[Worker] Scheduled source discovery will process %d user(s)", len(user_ids))

        total_promoted = 0
        failed_users = 0

        for user_id in user_ids:
            try:
                preferences = preferences_repository.get_or_create_by_user_id(user_id)
                enabled_sources = set(preferences.enabled_sources or [])

                hosted_urls: list[str] = []
                if enabled_sources:
                    for source_row in source_repository.list_active():
                        if source_row.source not in enabled_sources:
                            continue
                        hosted_url = build_hosted_board_url(source=source_row.source, board_token=source_row.board_token)
                        if hosted_url:
                            hosted_urls.append(hosted_url)

                hosted_urls.extend(parse_csv_urls(settings.job_discovery_seed_hosted_urls))
                career_urls = parse_csv_urls(settings.job_discovery_seed_career_urls)
                hosted_urls = list(dict.fromkeys(hosted_urls))
                career_urls = list(dict.fromkeys(career_urls))

                summary = discovery_service.discover_and_promote(
                    source_repository=source_repository,
                    hosted_urls=hosted_urls,
                    career_urls=career_urls,
                    is_active=True,
                )
                total_promoted += summary["promoted_count"]
                logger.info(
                    "[Worker] Discovery complete for user %s: candidates=%d promoted=%d skipped=%d",
                    user_id,
                    summary["candidates_found"],
                    summary["promoted_count"],
                    summary["skipped_count"],
                )
            except Exception as exc:  # noqa: BLE001
                failed_users += 1
                logger.exception("[Worker] Source discovery failed for user %s: %s", user_id, exc)

        logger.info(
            "[Worker] Scheduled source discovery finished: users=%d failures=%d promoted=%d",
            len(user_ids),
            failed_users,
            total_promoted,
        )
        return {
            "scanned_users": len(user_ids),
            "failed_users": failed_users,
            "promoted_sources": total_promoted,
        }
    finally:
        db.close()


@celery_app.task(name="auto_archive_stale_submitted_applications")
def auto_archive_stale_submitted_applications() -> dict[str, int]:
    """Archive applications that have been in 'submitted' status for too long.

    Applications stuck in 'submitted' for more than AUTO_ARCHIVE_STALE_SUBMISSION_DAYS
    days are automatically moved to 'archived'. This keeps the user's application
    list tidy and reflects realistic hiring timelines.
    """
    logger.info("[Worker] Starting auto-archive of stale submitted applications")

    cutoff = datetime.now(timezone.utc) - timedelta(days=AUTO_ARCHIVE_STALE_SUBMISSION_DAYS)
    db = SessionLocal()
    archived_count = 0
    failed_count = 0

    try:
        repo = ApplicationRepository(db)
        stale = repo.list_stale_submitted(submitted_before=cutoff)
        logger.info("[Worker] Found %d stale submitted application(s) to archive", len(stale))

        for application in stale:
            try:
                repo.update_fields(application.id, status=APPLICATION_STATUS_ARCHIVED)
                archived_count += 1
                logger.info(
                    "[Worker] Auto-archived application_id=%s (submitted on %s)",
                    application.id,
                    application.updated_at,
                )
            except Exception as exc:  # noqa: BLE001
                failed_count += 1
                logger.exception(
                    "[Worker] Failed to auto-archive application_id=%s: %s",
                    application.id,
                    exc,
                )
    finally:
        db.close()

    logger.info(
        "[Worker] Auto-archive complete: archived=%d failed=%d",
        archived_count,
        failed_count,
    )
    return {"archived": archived_count, "failed": failed_count}