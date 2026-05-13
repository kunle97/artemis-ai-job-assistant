"""
Job feed service.

Scans all ATS boards configured in a user's JobPreferences and persists new jobs.
This service is intentionally separate from JobService to avoid bloat.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.orm import Session

from src.domain.applications.constants import (
    APPLICATION_STATUS_AWAITING_SUBMISSION,
    APPLICATION_STATUS_FILLED,
    APPLICATION_STATUS_FILLING,
    APPLICATION_STATUS_INSPECTED,
    APPLICATION_STATUS_INSPECTING,
    APPLICATION_STATUS_NEEDS_REVIEW,
    APPLICATION_STATUS_PLANNED,
    APPLICATION_STATUS_PLANNING,
    APPLICATION_STATUS_QUEUED,
    APPLICATION_STATUS_READY,
)
from src.domain.applications.repository import ApplicationRepository
from src.domain.jobs.models import Job, JobFeedStatus
from src.domain.jobs.repository import (
    JobPreferencesRepository,
    JobRepository,
    JobSourceRepository,
    JobUserFeedRepository,
)
from src.domain.jobs.helpers import matches_job_location
from src.infrastructure.db.session import SessionLocal
from src.integrations.adapters.registry import get_adapter

logger = logging.getLogger(__name__)

_MAX_WORKERS = 10

_IN_PROGRESS_APPLICATION_STATUSES = {
    APPLICATION_STATUS_NEEDS_REVIEW,
    APPLICATION_STATUS_READY,
    APPLICATION_STATUS_QUEUED,
    APPLICATION_STATUS_INSPECTING,
    APPLICATION_STATUS_INSPECTED,
    APPLICATION_STATUS_PLANNING,
    APPLICATION_STATUS_PLANNED,
    APPLICATION_STATUS_FILLING,
    APPLICATION_STATUS_FILLED,
    APPLICATION_STATUS_AWAITING_SUBMISSION,
}


class JobFeedService:
    """Scans all registered ATS boards for a user and ingests new jobs.

    Mirrors career-ops' scan.mjs logic but as a Python service callable
    from both an API route and a background worker.
    """

    def __init__(self, user_id, db: Session):
        self.user_id = user_id
        self.db = db
        self._application_repo = ApplicationRepository(db)
        self._preferences_repo = JobPreferencesRepository(db)
        self._job_repo = JobRepository(db)
        self._job_source_repo = JobSourceRepository(db)
        self._user_feed_repo = JobUserFeedRepository(db)

    @classmethod
    def scan_for_user(cls, user_id) -> int:
        """Run a feed scan for one user using a managed DB session."""
        logger.info("[JobFeedService] Running managed feed scan for user %s", user_id)
        db = SessionLocal()
        try:
            service = cls(user_id=user_id, db=db)
            new_jobs = service.scan()
            return len(new_jobs)
        finally:
            db.close()

    def scan(self) -> list[Job]:
        """Run a full feed scan for the user.

        Flow:
        1. Load user's JobPreferences.
        2. For each enabled source, collect active board tokens from job_sources.
        3. Fetch all boards concurrently (max 10 workers).
        4. Apply title keyword filter from target_titles.
        5. Dedup in-memory and against DB.
        6. Persist and return only newly created Job records.
        """
        logger.info("[JobFeedService] Starting feed scan for user %s", self.user_id)

        preferences = self._preferences_repo.get_or_create_by_user_id(self.user_id)
        enabled_sources: list[str] = preferences.enabled_sources or []
        title_keywords: list[str] = [
            t.lower() for t in (preferences.target_titles or [])
        ]

        logger.info(
            "[JobFeedService] User %s: %d enabled source(s), %d title keyword(s)",
            self.user_id,
            len(enabled_sources),
            len(title_keywords),
        )

        if not enabled_sources:
            logger.info(
                "[JobFeedService] No enabled sources configured for user %s",
                self.user_id,
            )
            return []

        # Build (source, board_token) work items from DB-backed job sources.
        work_items: list[tuple[str, str]] = []
        active_job_sources = self._job_source_repo.list_active()
        enabled_source_set = set(enabled_sources)
        for job_source in active_job_sources:
            if enabled_source_set and job_source.source not in enabled_source_set:
                continue
            work_items.append((job_source.source, job_source.board_token))

        if not work_items:
            logger.info(
                "[JobFeedService] No boards to scan for user %s", self.user_id
            )
            return []

        # Concurrently fetch all boards (matches career-ops CONCURRENCY = 10)
        all_normalized: list[dict] = []
        with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
            futures = {
                executor.submit(self._fetch_board, source, board_token): (source, board_token)
                for source, board_token in work_items
            }
            for future in as_completed(futures):
                source, board_token = futures[future]
                try:
                    jobs = future.result()
                    all_normalized.extend(jobs)
                    logger.info(
                        "[JobFeedService] Fetched %d job(s) from %s/%s",
                        len(jobs),
                        source,
                        board_token,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "[JobFeedService] Board fetch failed for %s/%s: %s",
                        source,
                        board_token,
                        exc,
                    )

        # Filter → deduplicate → persist per-user feed links
        new_jobs: list[Job] = []
        seen_keys: set[tuple[str, str]] = set()

        for job_data in all_normalized:
            # Apply title keyword filter (any target_title substring match)
            if title_keywords:
                title_lower = (job_data.get("title") or "").lower()
                if not any(kw in title_lower for kw in title_keywords):
                    continue

            # In-memory dedup (two boards may surface the same job)
            job_key = (job_data["source"], job_data["source_job_id"])
            if job_key in seen_keys:
                continue
            seen_keys.add(job_key)

            job = self._job_repo.get_or_create(**job_data)
            _, created = self._user_feed_repo.get_or_create(
                user_id=self.user_id,
                job_id=job.id,
                status=JobFeedStatus.NEW,
            )
            if created:
                new_jobs.append(job)

        logger.info(
            "[JobFeedService] Scan complete for user %s: %d new job(s) stored",
            self.user_id,
            len(new_jobs),
        )
        return new_jobs

    def get_feed(
        self,
        skip: int = 0,
        limit: int | None = 20,
        query: str | None = None,
        sort: str = "newest",
        sources: set[str] | None = None,
    ) -> tuple[list, int]:
        """Return a paginated, preference-filtered view of the job pool.

        Filters are applied at read time against the user's current preferences.
        Returns (page_jobs, total_matching_count).
        """
        logger.info(
            "[JobFeedService] Loading feed for user %s (skip=%d, limit=%s, query=%s, sort=%s)",
            self.user_id,
            skip,
            limit,
            query,
            sort,
        )

        preferences = self._preferences_repo.get_or_create_by_user_id(self.user_id)
        feed_rows = self._user_feed_repo.list_for_user(self.user_id)
        feed_rows = self._exclude_in_progress_application_jobs(feed_rows)
        filtered = self._apply_preference_filters(feed_rows, preferences)

        if sources:
            filtered = [job for job in filtered if (job.source or "").lower() in sources]

        if query:
            normalized_query = query.strip().lower()
            filtered = [
                job for job in filtered
                if normalized_query in " ".join(
                    part for part in [
                        job.title or "",
                        job.company_name or "",
                        job.description or "",
                        job.location or "",
                        job.source or "",
                    ] if part
                ).lower()
            ]

        if sort == "salary_high":
            filtered.sort(key=lambda job: (job.salary_max or job.salary_min or 0), reverse=True)
        elif sort == "salary_low":
            filtered.sort(key=lambda job: (job.salary_min or job.salary_max or 0))
        else:
            filtered.sort(key=lambda job: job.created_at, reverse=True)

        total = len(filtered)
        if limit is None:
            page = filtered[skip:]
        else:
            page = filtered[skip : skip + limit]

        logger.info("[JobFeedService] Feed for user %s: %d total match, returning %d", self.user_id, total, len(page))
        return page, total

    def _exclude_in_progress_application_jobs(self, feed_rows: list) -> list:
        """Hide feed jobs that already have an in-progress application for this user."""
        job_ids = [row.job_id for row in feed_rows if getattr(row, "job_id", None) is not None]
        applications = self._application_repo.list_by_user_and_job_ids(
            user_id=self.user_id,
            job_ids=job_ids,
        )
        in_progress_job_ids = {
            application.job_id
            for application in applications
            if (application.status or "").strip().lower() in _IN_PROGRESS_APPLICATION_STATUSES
        }
        return [row for row in feed_rows if row.job_id not in in_progress_job_ids]

    def _apply_preference_filters(self, jobs: list, preferences) -> list:
        """Apply user preference keyword and attribute filters to feed-linked jobs."""
        title_keywords = [t.lower() for t in (preferences.target_titles or [])]
        positive_keywords = [k.lower() for k in (preferences.positive_keywords or [])]
        negative_keywords = [k.lower() for k in (preferences.negative_keywords or [])]
        preferred_locations = preferences.locations or []
        enabled_sources = set(preferences.enabled_sources or [])

        filtered = []
        for feed_row in jobs:
            job = feed_row.job
            if job is None:
                continue
            if enabled_sources and job.source not in enabled_sources:
                continue
            title_lower = (job.title or "").lower()
            desc_lower = (job.description or "").lower()
            searchable = f"{title_lower} {desc_lower}"

            if title_keywords and not any(kw in title_lower for kw in title_keywords):
                continue
            # Positive keywords are matched against title only. Title is always present
            # and descriptions are rarely populated from ATS listing APIs. Checking only
            # the title keeps the filter meaningful and consistent regardless of description availability.
            if positive_keywords and not any(kw in title_lower for kw in positive_keywords):
                continue
            if negative_keywords and any(kw in searchable for kw in negative_keywords):
                continue
            if not matches_job_location(job.location, preferred_locations):
                continue
            if preferences.remote_only and (job.workplace_type or "").lower() != "remote":
                continue
            # Only exclude when the job explicitly advertises a salary below the minimum.
            # Jobs with no salary data are kept — absence of data is not disqualifying.
            if preferences.salary_min and job.salary_min is not None and job.salary_min < preferences.salary_min:
                continue

            filtered.append(job)
        return filtered

    def update_feed_status(self, job_id, status: JobFeedStatus):
        """Update a per-user feed status for an already-linked job."""
        logger.info(
            "[JobFeedService] Updating feed status for user %s job %s -> %s",
            self.user_id,
            job_id,
            status,
        )
        return self._user_feed_repo.update_status(
            user_id=self.user_id,
            job_id=job_id,
            status=status,
        )

    def mark_jobs_as_seen(self, job_ids: list) -> int:
        """Mark NEW feed entries as SEEN after they are delivered to the client once."""
        return self._user_feed_repo.mark_new_as_seen_for_user_and_job_ids(
            user_id=self.user_id,
            job_ids=job_ids,
        )

    def _fetch_board(self, source: str, board_token: str) -> list[dict]:
        """Fetch normalized jobs from a single board via the appropriate adapter."""
        adapter = get_adapter(source)
        return adapter.search_jobs(board_token=board_token)
