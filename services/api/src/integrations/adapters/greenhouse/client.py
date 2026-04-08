"""
Greenhouse API client.

Fetches raw job data from Greenhouse-hosted job boards.
"""

from __future__ import annotations

import requests


class GreenhouseClient:
    """
    Small client for Greenhouse job board APIs.
    """

    BASE_URL_TEMPLATE = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"

    def fetch_jobs(self, board_token: str) -> list[dict]:
        """
        Fetch raw jobs for a Greenhouse board token.
        """
        url = self.BASE_URL_TEMPLATE.format(board_token=board_token)
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        data = response.json()
        return data.get("jobs", [])