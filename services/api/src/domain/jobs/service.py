"""
Job service.

Coordinates adapters, board-token resolution, and persistence.
"""

from src.domain.jobs.repository import JobRepository
from src.domain.jobs.schemas import JobSearchRequest
from src.domain.jobs.source_registry import JOB_SOURCE_REGISTRY
from src.integrations.adapters.registry import get_adapter


class JobService:
    def __init__(self, repository: JobRepository):
        self.repository = repository

    def search_and_store_jobs(self, payload: JobSearchRequest):
        adapter = get_adapter(payload.source)
        board_tokens = self._resolve_board_tokens(payload)

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

    def _resolve_board_tokens(self, payload: JobSearchRequest) -> list[str]:
        """
        Resolve one or more board tokens from the request using:
        1. direct board_token
        2. company_name via registry
        3. company_names via registry
        """
        if payload.board_token:
            return [payload.board_token]

        source_map = JOB_SOURCE_REGISTRY.get(payload.source, {})

        resolved_tokens = []

        if payload.company_name:
            resolved_tokens.append(
                self._lookup_company_board_token(
                    source=payload.source,
                    company_name=payload.company_name,
                    source_map=source_map,
                )
            )

        for company_name in payload.company_names:
            resolved_tokens.append(
                self._lookup_company_board_token(
                    source=payload.source,
                    company_name=company_name,
                    source_map=source_map,
                )
            )

        deduped_tokens = []
        for token in resolved_tokens:
            if token not in deduped_tokens:
                deduped_tokens.append(token)

        if deduped_tokens:
            return deduped_tokens

        raise ValueError(
            "Provide board_token, company_name, or company_names for job search."
        )

    def _lookup_company_board_token(
        self,
        source: str,
        company_name: str,
        source_map: dict,
    ) -> str:
        company_key = company_name.lower()

        if company_key in source_map:
            return source_map[company_key]["board_token"]

        raise ValueError(
            f"Unknown company '{company_name}' for source '{source}'."
        )