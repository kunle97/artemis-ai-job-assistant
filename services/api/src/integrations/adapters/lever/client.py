"""
Lever API client.

Fetches raw job data from Lever-hosted job boards via the public postings API.
"""

from __future__ import annotations

import requests


class LeverClient:
    """Small client for the Lever public postings API."""

    BASE_URL_TEMPLATE = "https://api.lever.co/v0/postings/{board_token}"

    def fetch_jobs(self, board_token: str) -> list[dict]:
        """Fetch raw jobs for a Lever board token.

        The Lever API returns a JSON array directly (not wrapped in a dict).
        Raises ``requests.HTTPError`` on non-2xx responses.
        """
        url = self.BASE_URL_TEMPLATE.format(board_token=board_token)
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        data = response.json()
        return data if isinstance(data, list) else []
