"""
Ashby adapter.

Fetches and normalizes jobs from Ashby-hosted job boards.
"""

from __future__ import annotations

import requests

from src.integrations.adapters.base import JobSourceAdapter
from src.integrations.adapters.ashby.client import AshbyClient


class AshbyAdapter(JobSourceAdapter):
    """Ashby job source adapter."""

    def __init__(self):
        self.client = AshbyClient()

    def search_jobs(
        self,
        board_token: str | None = None,
        query: str | None = None,
        location: str | None = None,
    ) -> list[dict]:
        """Fetch and normalize jobs from an Ashby board."""
        if not board_token:
            raise ValueError("board_token is required for Ashby job searches.")

        try:
            raw_jobs = self.client.fetch_jobs(board_token=board_token)
        except requests.HTTPError as exc:
            raise ValueError(
                f"Unable to fetch Ashby jobs for board token: {board_token}"
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
        """Convert an Ashby job into Artemis' normalized job shape."""
        salary_min, salary_max, currency = _extract_compensation(raw_job)
        workplace_type = _infer_workplace_type(raw_job)
        description = (
            raw_job.get("descriptionPlain")
            or raw_job.get("description")
            or raw_job.get("jobDescription")
            or None
        )

        return {
            "source": "ashby",
            "source_job_id": str(raw_job.get("id") or ""),
            "title": raw_job.get("title") or "Untitled Job",
            "company_name": board_token,
            "location": raw_job.get("location") or None,
            "workplace_type": workplace_type,
            "description": description,
            "apply_url": raw_job.get("jobUrl") or "",
            "salary_min": salary_min,
            "salary_max": salary_max,
            "currency": currency,
            "is_active": True,
        }


def _infer_workplace_type(raw_job: dict) -> str | None:
    candidates = [
        raw_job.get("workplaceType"),
        raw_job.get("employmentType"),
        raw_job.get("location"),
    ]
    haystack = " ".join(str(value) for value in candidates if value).lower()
    if "remote" in haystack:
        return "remote"
    if "hybrid" in haystack:
        return "hybrid"
    if any(token in haystack for token in ["on-site", "onsite", "in-office", "office"]):
        return "on-site"
    return None


def _extract_compensation(raw_job: dict) -> tuple[int | None, int | None, str | None]:
    """Extract salary_min, salary_max, currency from an Ashby job dict.

    Ashby nests compensation under ``compensation.summaryComponents``.
    Returns ``(None, None, None)`` if the field is absent or unparseable.
    """
    compensation = raw_job.get("compensation")
    if not compensation:
        return None, None, None

    components = compensation.get("summaryComponents") or []
    if not components:
        return None, None, None

    # Use the first component — covers most single-range roles
    component = components[0]
    salary_min = component.get("minValue")
    salary_max = component.get("maxValue")
    currency = component.get("currency")

    # Coerce to int if floats are returned (e.g. 120000.0)
    if salary_min is not None:
        salary_min = int(salary_min)
    if salary_max is not None:
        salary_max = int(salary_max)

    return salary_min, salary_max, currency or None
