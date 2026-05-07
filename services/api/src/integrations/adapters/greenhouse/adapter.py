"""
Greenhouse adapter.

Fetches and normalizes jobs from Greenhouse-hosted job boards.
"""

from __future__ import annotations

import requests

from src.integrations.adapters.base import JobSourceAdapter
from src.integrations.adapters.greenhouse.client import GreenhouseClient


class GreenhouseAdapter(JobSourceAdapter):
    """
    Greenhouse job source adapter.
    """

    def __init__(self):
        self.client = GreenhouseClient()

    def search_jobs(
        self,
        board_token: str | None = None,
        query: str | None = None,
        location: str | None = None,
    ) -> list[dict]:
        """
        Fetch and normalize jobs from a Greenhouse board.
        """
        if not board_token:
            raise ValueError("board_token is required for greenhouse job searches.")

        try:
            raw_jobs = self.client.fetch_jobs(board_token=board_token)
        except requests.HTTPError as exc:
            raise ValueError(f"Unable to fetch Greenhouse jobs for board token: {board_token}")

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
        """
        Convert a Greenhouse job into Artemis' normalized job shape.
        """
        location_data = raw_job.get("location") or {}
        metadata = raw_job.get("metadata") or []
        location_name = location_data.get("name")

        workplace_type = _infer_workplace_type(location_name, metadata)
        description = raw_job.get("content") or raw_job.get("description") or None

        return {
            "source": "greenhouse",
            "source_job_id": str(raw_job.get("id")),
            "title": raw_job.get("title") or "Untitled Job",
            "company_name": board_token,
            "location": location_name,
            "workplace_type": workplace_type,
            "description": description,
            "apply_url": raw_job.get("absolute_url") or "",
            "salary_min": None,
            "salary_max": None,
            "currency": None,
            "is_active": True,
        }


def _infer_workplace_type(location_name: str | None, metadata: list[dict]) -> str | None:
    candidates: list[str] = []
    if location_name:
        candidates.append(location_name)

    for item in metadata:
        if not isinstance(item, dict):
            continue
        value = item.get("value")
        if isinstance(value, str):
            candidates.append(value)

    haystack = " ".join(candidates).lower()
    if "remote" in haystack:
        return "remote"
    if "hybrid" in haystack:
        return "hybrid"
    if any(token in haystack for token in ["on-site", "onsite", "in-office", "office"]):
        return "on-site"
    return None