"""
Unit tests for the Lever adapter and client.

Covers: normal case, empty results, HTTP error,
        query/location filtering, get_adapter registry lookup.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.integrations.adapters.lever.client import LeverClient
from src.integrations.adapters.lever.adapter import LeverAdapter
from src.integrations.adapters.registry import get_adapter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_JOB = {
    "id": "abc-111",
    "text": "Software Engineer",
    "hostedUrl": "https://jobs.lever.co/acme/abc-111",
    "categories": {
        "location": "Remote",
    },
}

SECOND_JOB = {
    "id": "def-222",
    "text": "Staff Engineer",
    "hostedUrl": "https://jobs.lever.co/acme/def-222",
    "categories": {
        "location": "New York, NY",
    },
}

LEVER_RESPONSE = [MINIMAL_JOB, SECOND_JOB]


# ---------------------------------------------------------------------------
# LeverClient
# ---------------------------------------------------------------------------

class TestLeverClient:
    def test_fetch_jobs_returns_job_list(self):
        mock_response = MagicMock()
        mock_response.json.return_value = LEVER_RESPONSE
        mock_response.raise_for_status = MagicMock()

        with patch("src.integrations.adapters.lever.client.requests.get", return_value=mock_response):
            client = LeverClient()
            jobs = client.fetch_jobs("acme")

        assert len(jobs) == 2
        assert jobs[0]["id"] == "abc-111"

    def test_fetch_jobs_empty_board(self):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        with patch("src.integrations.adapters.lever.client.requests.get", return_value=mock_response):
            client = LeverClient()
            jobs = client.fetch_jobs("acme")

        assert jobs == []

    def test_fetch_jobs_raises_on_http_error(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404")

        with patch("src.integrations.adapters.lever.client.requests.get", return_value=mock_response):
            client = LeverClient()
            with pytest.raises(requests.HTTPError):
                client.fetch_jobs("does-not-exist")

    def test_fetch_jobs_non_list_response_returns_empty(self):
        """Guard against malformed API responses that are not a list."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "not found"}
        mock_response.raise_for_status = MagicMock()

        with patch("src.integrations.adapters.lever.client.requests.get", return_value=mock_response):
            client = LeverClient()
            jobs = client.fetch_jobs("acme")

        assert jobs == []


# ---------------------------------------------------------------------------
# LeverAdapter.search_jobs
# ---------------------------------------------------------------------------

class TestLeverAdapter:
    def _make_adapter(self, raw_jobs: list[dict]) -> LeverAdapter:
        adapter = LeverAdapter()
        adapter.client = MagicMock()
        adapter.client.fetch_jobs.return_value = raw_jobs
        return adapter

    def test_search_jobs_normal_case(self):
        adapter = self._make_adapter([MINIMAL_JOB, SECOND_JOB])
        jobs = adapter.search_jobs(board_token="acme")

        assert len(jobs) == 2
        job = jobs[0]
        assert job["source"] == "lever"
        assert job["source_job_id"] == "abc-111"
        assert job["title"] == "Software Engineer"
        assert job["company_name"] == "acme"
        assert job["location"] == "Remote"
        assert job["apply_url"] == "https://jobs.lever.co/acme/abc-111"
        assert job["salary_min"] is None
        assert job["salary_max"] is None

    def test_search_jobs_empty_board(self):
        adapter = self._make_adapter([])
        jobs = adapter.search_jobs(board_token="acme")
        assert jobs == []

    def test_search_jobs_raises_on_missing_board_token(self):
        adapter = LeverAdapter()
        with pytest.raises(ValueError, match="board_token is required"):
            adapter.search_jobs()

    def test_search_jobs_wraps_http_error(self):
        adapter = LeverAdapter()
        adapter.client = MagicMock()
        adapter.client.fetch_jobs.side_effect = requests.HTTPError("404")

        with pytest.raises(ValueError, match="Unable to fetch Lever jobs"):
            adapter.search_jobs(board_token="bad-token")

    def test_search_jobs_filters_by_query(self):
        adapter = self._make_adapter([MINIMAL_JOB, SECOND_JOB])
        jobs = adapter.search_jobs(board_token="acme", query="Staff")

        assert len(jobs) == 1
        assert jobs[0]["title"] == "Staff Engineer"

    def test_search_jobs_filters_by_location(self):
        adapter = self._make_adapter([MINIMAL_JOB, SECOND_JOB])
        jobs = adapter.search_jobs(board_token="acme", location="New York")

        assert len(jobs) == 1
        assert jobs[0]["title"] == "Staff Engineer"

    def test_normalize_job_missing_categories(self):
        raw_job = {
            "id": "xyz-999",
            "text": "Backend Engineer",
            "hostedUrl": "https://jobs.lever.co/acme/xyz-999",
        }
        adapter = LeverAdapter()
        normalized = adapter._normalize_job(raw_job, board_token="acme")

        assert normalized["location"] is None
        assert normalized["source_job_id"] == "xyz-999"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_get_adapter_returns_lever_adapter(self):
        adapter = get_adapter("lever")
        assert isinstance(adapter, LeverAdapter)

    def test_get_adapter_lever_case_insensitive(self):
        adapter = get_adapter("Lever")
        assert isinstance(adapter, LeverAdapter)
