"""
Job service.

Coordinates adapters, board-token resolution, and persistence.
"""

import logging

from src.domain.jobs.repository import JobPreferencesRepository, JobRepository, JobSourceRepository
from src.domain.jobs.schemas import JobPreferencesUpsertRequest, JobSearchRequest
from src.domain.jobs.helpers import filter_job_by_title, resolve_board_tokens
from src.integrations.adapters.registry import get_adapter

logger = logging.getLogger(__name__)


class JobService:
    def __init__(
        self,
        repository: JobRepository,
        preferences_repository: JobPreferencesRepository | None = None,
        job_source_repository: JobSourceRepository | None = None,
    ):
        self.repository = repository
        self.preferences_repository = preferences_repository
        self.job_source_repository = job_source_repository

    def _build_source_map(self, source: str) -> dict[str, dict]:
        if self.job_source_repository is None:
            return {}

        source_map: dict[str, dict] = {}
        for entry in self.job_source_repository.list_active():
            if entry.source != source:
                continue
            source_map[entry.company_key] = {
                "board_token": entry.board_token,
                "display_name": entry.display_name,
            }

        return source_map

    def search_and_store_jobs(
        self,
        payload: JobSearchRequest,
        user_id=None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list, int]:
        adapter = get_adapter(payload.source)
        source_map: dict[str, dict] = {}
        if not payload.board_token:
            source_map = self._build_source_map(payload.source)

        board_tokens = resolve_board_tokens(
            payload,
            source_map=source_map,
        )

        positive_keywords: list[str] = []
        negative_keywords: list[str] = []
        if user_id is not None and self.preferences_repository is not None:
            preferences = self.preferences_repository.get_or_create_by_user_id(user_id)
            positive_keywords = preferences.positive_keywords or []
            negative_keywords = preferences.negative_keywords or []
            logger.info(
                "[JobService] Applying title filters for user %s (%d positive, %d negative)",
                user_id,
                len(positive_keywords),
                len(negative_keywords),
            )

        stored_jobs = []
        seen_job_keys = set()

        for board_token in board_tokens:
            jobs = adapter.search_jobs(
                board_token=board_token,
                query=payload.query,
                location=payload.location,
            )

            for job_data in jobs:
                job_key = (job_data["source"], job_data["source_job_id"])
                if job_key in seen_job_keys:
                    continue

                if not filter_job_by_title(
                    title=job_data.get("title") or "",
                    positive=positive_keywords,
                    negative=negative_keywords,
                ):
                    continue

                stored_job = self.repository.get_or_create(**job_data)
                stored_jobs.append(stored_job)
                seen_job_keys.add(job_key)

        total = len(stored_jobs)
        return stored_jobs[skip : skip + limit], total

    def list_jobs(self):
        return self.repository.list_all()

    def list_jobs_paginated(self, skip: int = 0, limit: int = 20) -> tuple[list, int]:
        return self.repository.list_paginated(skip=skip, limit=limit)

    def get_preferences_for_user(self, user_id):
        if self.preferences_repository is None:
            raise ValueError("preferences_repository is required")

        logger.info("[JobService] Loading job preferences for user %s", user_id)
        preferences = self.preferences_repository.get_or_create_by_user_id(user_id)
        logger.info("[JobService] Job preferences ready for user %s", user_id)
        return preferences

    def upsert_preferences_for_user(self, user_id, payload: JobPreferencesUpsertRequest):
        if self.preferences_repository is None:
            raise ValueError("preferences_repository is required")

        logger.info("[JobService] Upserting job preferences for user %s", user_id)
        preferences = self.preferences_repository.upsert(user_id, payload)
        logger.info(
            "[JobService] Job preferences updated for user %s with %s target titles and %s sources",
            user_id,
            len(preferences.target_titles or []),
            len(preferences.enabled_sources or []),
        )
        return preferences