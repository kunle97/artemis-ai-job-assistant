"""
Lever adapter.

Fetches and normalizes jobs from Lever-hosted job boards.
"""

from __future__ import annotations

import requests

from src.integrations.adapters.base import JobSourceAdapter
from src.integrations.adapters.lever.client import LeverClient


class LeverAdapter(JobSourceAdapter):
    """Lever job source adapter."""

    def __init__(self):
        self.client = LeverClient()

    def search_jobs(
        self,
        board_token: str | None = None,
        query: str | None = None,
        location: str | None = None,
    ) -> list[dict]:
        """Fetch and normalize jobs from a Lever board."""
        if not board_token:
            raise ValueError("board_token is required for Lever job searches.")

        try:
            raw_jobs = self.client.fetch_jobs(board_token=board_token)
        except requests.HTTPError as exc:
            raise ValueError(
                f"Unable to fetch Lever jobs for board token: {board_token}"
            ) from exc

        normalized_jobs = []
        query_lower = query.lower() if query else None
        location_lower = location.lower() if location else None

        for raw_job in raw_jobs:
            normalized = self._normalize_job(raw_job, board_token=board_token)

            if query_lower and query_lower not in normalized["title"].lower():
                continue

            if location_lower:
                normalized_location = (normalized.get("location") or "").lower()
                if location_lower not in normalized_location:
                    continue

            normalized_jobs.append(normalized)

        return normalized_jobs

    def _normalize_job(self, raw_job: dict, board_token: str) -> dict:
        """Convert a Lever job into Artemis' normalized job shape."""
        categories = raw_job.get("categories") or {}

        return {
            "source": "lever",
            "source_job_id": str(raw_job.get("id") or ""),
            "title": raw_job.get("text") or "Untitled Job",
            "company_name": board_token,
            "location": categories.get("location") or None,
            "workplace_type": None,
            "description": None,
            "apply_url": raw_job.get("hostedUrl") or "",
            "salary_min": None,
            "salary_max": None,
            "currency": None,
            "is_active": True,
        }
