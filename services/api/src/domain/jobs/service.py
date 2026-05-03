"""
Job service.

Coordinates adapters, board-token resolution, and persistence.
"""

import logging

from src.domain.jobs.repository import JobPreferencesRepository, JobRepository
from src.domain.jobs.schemas import JobPreferencesUpsertRequest, JobSearchRequest
from src.domain.jobs.helpers import resolve_board_tokens
from src.integrations.adapters.registry import get_adapter

logger = logging.getLogger(__name__)


class JobService:
    def __init__(
        self,
        repository: JobRepository,
        preferences_repository: JobPreferencesRepository | None = None,
    ):
        self.repository = repository
        self.preferences_repository = preferences_repository

    def search_and_store_jobs(self, payload: JobSearchRequest):
        adapter = get_adapter(payload.source)
        board_tokens = resolve_board_tokens(payload)

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

                stored_job = self.repository.get_or_create(**job_data)
                stored_jobs.append(stored_job)
                seen_job_keys.add(job_key)

        return stored_jobs

    def list_jobs(self):
        return self.repository.list_all()

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