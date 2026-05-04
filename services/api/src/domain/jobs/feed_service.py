"""
Job feed service.

Scans all ATS boards configured in a user's JobPreferences and persists new jobs.
This service is intentionally separate from JobService to avoid bloat.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.orm import Session

from src.domain.jobs.models import Job
from src.domain.jobs.repository import JobPreferencesRepository, JobRepository
from src.domain.jobs.source_registry import JOB_SOURCE_REGISTRY
from src.integrations.adapters.registry import get_adapter

logger = logging.getLogger(__name__)

_MAX_WORKERS = 10


class JobFeedService:
    """Scans all registered ATS boards for a user and ingests new jobs.

    Mirrors career-ops' scan.mjs logic but as a Python service callable
    from both an API route and a background worker.
    """

    def __init__(self, user_id, db: Session):
        self.user_id = user_id
        self.db = db
        self._preferences_repo = JobPreferencesRepository(db)
        self._job_repo = JobRepository(db)

    def scan(self) -> list[Job]:
        """Run a full feed scan for the user.

        Flow:
        1. Load user's JobPreferences.
        2. For each enabled_source, collect board tokens from JOB_SOURCE_REGISTRY.
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

        # Build (source, board_token) work items from the registry
        work_items: list[tuple[str, str]] = []
        for source in enabled_sources:
            for _company_key, company_config in JOB_SOURCE_REGISTRY.get(source, {}).items():
                work_items.append((source, company_config["board_token"]))

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

        # Filter → deduplicate → persist
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

            # DB dedup — skip jobs already ingested in a previous scan
            if self._job_repo.get_by_source_and_source_job_id(
                source=job_data["source"],
                source_job_id=job_data["source_job_id"],
            ):
                continue

            job = self._job_repo.create(**job_data)
            new_jobs.append(job)

        logger.info(
            "[JobFeedService] Scan complete for user %s: %d new job(s) stored",
            self.user_id,
            len(new_jobs),
        )
        return new_jobs

    def get_feed(self, skip: int = 0, limit: int = 20) -> tuple[list, int]:
        """Return a paginated, preference-filtered view of the job pool.

        Filters are applied at read time against the user's current preferences.
        Returns (page_jobs, total_matching_count).
        """
        logger.info("[JobFeedService] Loading feed for user %s (skip=%d, limit=%d)", self.user_id, skip, limit)

        preferences = self._preferences_repo.get_or_create_by_user_id(self.user_id)
        jobs = self._job_repo.list_active_by_sources(preferences.enabled_sources or [])
        filtered = self._apply_preference_filters(jobs, preferences)

        total = len(filtered)
        page = filtered[skip : skip + limit]

        logger.info("[JobFeedService] Feed for user %s: %d total match, returning %d", self.user_id, total, len(page))
        return page, total

    def _apply_preference_filters(self, jobs: list, preferences) -> list:
        """Apply user preference keyword and attribute filters to a list of jobs."""
        title_keywords = [t.lower() for t in (preferences.target_titles or [])]
        positive_keywords = [k.lower() for k in (preferences.positive_keywords or [])]
        negative_keywords = [k.lower() for k in (preferences.negative_keywords or [])]

        filtered = []
        for job in jobs:
            title_lower = (job.title or "").lower()
            desc_lower = (job.description or "").lower()
            searchable = f"{title_lower} {desc_lower}"

            if title_keywords and not any(kw in title_lower for kw in title_keywords):
                continue
            # Check positive_keywords against title and description. Title is always present
            # so this filter always runs. If there is no description, the title alone is checked.
            if positive_keywords and not any(kw in searchable for kw in positive_keywords):
                continue
            if negative_keywords and any(kw in searchable for kw in negative_keywords):
                continue
            if preferences.remote_only and (job.workplace_type or "").lower() != "remote":
                continue
            # Only exclude when the job explicitly advertises a salary below the minimum.
            # Jobs with no salary data are kept — absence of data is not disqualifying.
            if preferences.salary_min and job.salary_min is not None and job.salary_min < preferences.salary_min:
                continue

            filtered.append(job)
        return filtered

    def _fetch_board(self, source: str, board_token: str) -> list[dict]:
        """Fetch normalized jobs from a single board via the appropriate adapter."""
        adapter = get_adapter(source)
        return adapter.search_jobs(board_token=board_token)
