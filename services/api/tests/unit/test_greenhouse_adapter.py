"""
Unit tests for the Greenhouse adapter and client.

Covers: normal case, empty board, HTTP error,
        query/location filtering, get_adapter registry lookup.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.integrations.adapters.greenhouse.client import GreenhouseClient
from src.integrations.adapters.greenhouse.adapter import GreenhouseAdapter
from src.integrations.adapters.registry import get_adapter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_JOB = {
    "id": 12345,
    "title": "Software Engineer",
    "absolute_url": "https://boards.greenhouse.io/acme/jobs/12345",
    "location": {"name": "Remote"},
    "content": None,
    "metadata": [],
}

SECOND_JOB = {
    "id": 67890,
    "title": "Staff Engineer",
    "absolute_url": "https://boards.greenhouse.io/acme/jobs/67890",
    "location": {"name": "New York, NY"},
    "content": None,
    "metadata": [],
}

GREENHOUSE_RESPONSE = {"jobs": [MINIMAL_JOB, SECOND_JOB]}
EMPTY_RESPONSE = {"jobs": []}


# ---------------------------------------------------------------------------
# GreenhouseClient
# ---------------------------------------------------------------------------

class TestGreenhouseClient:
    def test_fetch_jobs_returns_job_list(self):
        mock_response = MagicMock()
        mock_response.json.return_value = GREENHOUSE_RESPONSE
        mock_response.raise_for_status = MagicMock()

        with patch("src.integrations.adapters.greenhouse.client.requests.get", return_value=mock_response):
            client = GreenhouseClient()
            jobs = client.fetch_jobs("acme")

        assert len(jobs) == 2
        assert jobs[0]["id"] == 12345

    def test_fetch_jobs_empty_board(self):
        mock_response = MagicMock()
        mock_response.json.return_value = EMPTY_RESPONSE
        mock_response.raise_for_status = MagicMock()

        with patch("src.integrations.adapters.greenhouse.client.requests.get", return_value=mock_response):
            client = GreenhouseClient()
            jobs = client.fetch_jobs("acme")

        assert jobs == []

    def test_fetch_jobs_raises_on_http_error(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404")

        with patch("src.integrations.adapters.greenhouse.client.requests.get", return_value=mock_response):
            client = GreenhouseClient()
            with pytest.raises(requests.HTTPError):
                client.fetch_jobs("does-not-exist")

    def test_fetch_jobs_url_contains_board_token(self):
        mock_response = MagicMock()
        mock_response.json.return_value = EMPTY_RESPONSE
        mock_response.raise_for_status = MagicMock()

        with patch("src.integrations.adapters.greenhouse.client.requests.get", return_value=mock_response) as mock_get:
            client = GreenhouseClient()
            client.fetch_jobs("mytoken")

        called_url = mock_get.call_args[0][0]
        assert "mytoken" in called_url


# ---------------------------------------------------------------------------
# GreenhouseAdapter.search_jobs
# ---------------------------------------------------------------------------

class TestGreenhouseAdapter:
    def _make_adapter(self, raw_jobs: list[dict]) -> GreenhouseAdapter:
        adapter = GreenhouseAdapter()
        adapter.client = MagicMock()
        adapter.client.fetch_jobs.return_value = raw_jobs
        return adapter

    def test_search_jobs_normal_case(self):
        adapter = self._make_adapter([MINIMAL_JOB, SECOND_JOB])
        jobs = adapter.search_jobs(board_token="acme")

        assert len(jobs) == 2
        job = jobs[0]
        assert job["source"] == "greenhouse"
        assert job["source_job_id"] == "12345"
        assert job["title"] == "Software Engineer"
        assert job["company_name"] == "acme"
        assert job["location"] == "Remote"
        assert job["apply_url"] == "https://boards.greenhouse.io/acme/jobs/12345"

    def test_search_jobs_empty_board(self):
        adapter = self._make_adapter([])
        jobs = adapter.search_jobs(board_token="acme")
        assert jobs == []

    def test_search_jobs_raises_on_missing_board_token(self):
        adapter = GreenhouseAdapter()
        with pytest.raises(ValueError, match="board_token is required"):
            adapter.search_jobs()

    def test_search_jobs_wraps_http_error(self):
        adapter = GreenhouseAdapter()
        adapter.client = MagicMock()
        adapter.client.fetch_jobs.side_effect = requests.HTTPError("404")

        with pytest.raises(ValueError, match="Unable to fetch Greenhouse jobs"):
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

    def test_normalize_job_missing_location(self):
        raw_job = {
            "id": 99999,
            "title": "Backend Engineer",
            "absolute_url": "https://boards.greenhouse.io/acme/jobs/99999",
        }
        adapter = GreenhouseAdapter()
        normalized = adapter._normalize_job(raw_job, board_token="acme")

        assert normalized["location"] is None
        assert normalized["source_job_id"] == "99999"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_get_adapter_returns_greenhouse_adapter(self):
        adapter = get_adapter("greenhouse")
        assert isinstance(adapter, GreenhouseAdapter)

    def test_get_adapter_greenhouse_case_insensitive(self):
        adapter = get_adapter("Greenhouse")
        assert isinstance(adapter, GreenhouseAdapter)
