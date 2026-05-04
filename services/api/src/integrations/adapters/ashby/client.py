"""
Ashby API client.

Fetches raw job data from Ashby-hosted job boards via the public posting API.
"""

from __future__ import annotations

import requests


class AshbyClient:
    """Small client for the Ashby public posting API."""

    BASE_URL_TEMPLATE = (
        "https://api.ashbyhq.com/posting-api/job-board/{board_token}"
        "?includeCompensation=true"
    )

    def fetch_jobs(self, board_token: str) -> list[dict]:
        """Fetch raw jobs for an Ashby board token.

        Returns the ``jobs`` list from the API response.
        Raises ``requests.HTTPError`` on non-2xx responses.
        """
        url = self.BASE_URL_TEMPLATE.format(board_token=board_token)
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        data = response.json()
        return data.get("jobs", [])
