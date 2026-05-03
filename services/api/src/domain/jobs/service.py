"""
Job service.

Coordinates adapters, board-token resolution, and persistence.
"""

from src.domain.jobs.repository import JobRepository
from src.domain.jobs.schemas import JobSearchRequest
from src.domain.jobs.helpers import resolve_board_tokens
from src.integrations.adapters.registry import get_adapter


class JobService:
    def __init__(self, repository: JobRepository):
        self.repository = repository

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