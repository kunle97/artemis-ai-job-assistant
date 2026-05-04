"""
Unit tests for the Ashby adapter and client.

Covers: normal case, compensation fields present, empty board, HTTP error,
        get_adapter registry lookup.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.integrations.adapters.ashby.client import AshbyClient
from src.integrations.adapters.ashby.adapter import AshbyAdapter, _extract_compensation
from src.integrations.adapters.registry import get_adapter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_JOB = {
    "id": "abc-123",
    "title": "Software Engineer",
    "jobUrl": "https://jobs.ashbyhq.com/acme/abc-123",
    "location": "Remote",
}

JOB_WITH_COMPENSATION = {
    "id": "def-456",
    "title": "Staff Engineer",
    "jobUrl": "https://jobs.ashbyhq.com/acme/def-456",
    "location": "New York, NY",
    "compensation": {
        "summaryComponents": [
            {
                "compensationTierSummary": "$150k – $200k USD",
                "currency": "USD",
                "minValue": 150000.0,
                "maxValue": 200000.0,
                "interval": "ANNUAL",
            }
        ]
    },
}

ASHBY_RESPONSE = {"jobs": [MINIMAL_JOB, JOB_WITH_COMPENSATION]}
EMPTY_RESPONSE = {"jobs": []}


# ---------------------------------------------------------------------------
# AshbyClient
# ---------------------------------------------------------------------------

class TestAshbyClient:
    def test_fetch_jobs_returns_job_list(self):
        mock_response = MagicMock()
        mock_response.json.return_value = ASHBY_RESPONSE
        mock_response.raise_for_status = MagicMock()

        with patch("src.integrations.adapters.ashby.client.requests.get", return_value=mock_response):
            client = AshbyClient()
            jobs = client.fetch_jobs("acme")

        assert len(jobs) == 2
        assert jobs[0]["id"] == "abc-123"

    def test_fetch_jobs_empty_board(self):
        mock_response = MagicMock()
        mock_response.json.return_value = EMPTY_RESPONSE
        mock_response.raise_for_status = MagicMock()

        with patch("src.integrations.adapters.ashby.client.requests.get", return_value=mock_response):
            client = AshbyClient()
            jobs = client.fetch_jobs("acme")

        assert jobs == []

    def test_fetch_jobs_raises_on_http_error(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404")

        with patch("src.integrations.adapters.ashby.client.requests.get", return_value=mock_response):
            client = AshbyClient()
            with pytest.raises(requests.HTTPError):
                client.fetch_jobs("does-not-exist")

    def test_fetch_jobs_url_includes_compensation_param(self):
        mock_response = MagicMock()
        mock_response.json.return_value = EMPTY_RESPONSE
        mock_response.raise_for_status = MagicMock()

        with patch("src.integrations.adapters.ashby.client.requests.get", return_value=mock_response) as mock_get:
            client = AshbyClient()
            client.fetch_jobs("mytoken")

        called_url = mock_get.call_args[0][0]
        assert "mytoken" in called_url
        assert "includeCompensation=true" in called_url


# ---------------------------------------------------------------------------
# _extract_compensation helper
# ---------------------------------------------------------------------------

class TestExtractCompensation:
    def test_returns_none_when_compensation_absent(self):
        assert _extract_compensation({}) == (None, None, None)

    def test_returns_none_when_summary_components_empty(self):
        job = {"compensation": {"summaryComponents": []}}
        assert _extract_compensation(job) == (None, None, None)

    def test_extracts_values_from_first_component(self):
        salary_min, salary_max, currency = _extract_compensation(JOB_WITH_COMPENSATION)
        assert salary_min == 150000
        assert salary_max == 200000
        assert currency == "USD"

    def test_coerces_floats_to_int(self):
        job = {
            "compensation": {
                "summaryComponents": [
                    {"minValue": 90000.0, "maxValue": 120000.0, "currency": "GBP"}
                ]
            }
        }
        salary_min, salary_max, currency = _extract_compensation(job)
        assert isinstance(salary_min, int)
        assert isinstance(salary_max, int)


# ---------------------------------------------------------------------------
# AshbyAdapter.search_jobs
# ---------------------------------------------------------------------------

class TestAshbyAdapter:
    def _make_adapter(self, raw_jobs: list[dict]) -> AshbyAdapter:
        adapter = AshbyAdapter()
        adapter.client = MagicMock()
        adapter.client.fetch_jobs.return_value = raw_jobs
        return adapter

    def test_search_jobs_normal_case(self):
        adapter = self._make_adapter([MINIMAL_JOB, JOB_WITH_COMPENSATION])
        jobs = adapter.search_jobs(board_token="acme")

        assert len(jobs) == 2
        job = jobs[0]
        assert job["source"] == "ashby"
        assert job["source_job_id"] == "abc-123"
        assert job["title"] == "Software Engineer"
        assert job["company_name"] == "acme"
        assert job["location"] == "Remote"
        assert job["apply_url"] == "https://jobs.ashbyhq.com/acme/abc-123"
        assert job["salary_min"] is None
        assert job["salary_max"] is None

    def test_search_jobs_compensation_fields_present(self):
        adapter = self._make_adapter([JOB_WITH_COMPENSATION])
        jobs = adapter.search_jobs(board_token="acme")

        job = jobs[0]
        assert job["salary_min"] == 150000
        assert job["salary_max"] == 200000
        assert job["currency"] == "USD"

    def test_search_jobs_empty_board(self):
        adapter = self._make_adapter([])
        jobs = adapter.search_jobs(board_token="acme")
        assert jobs == []

    def test_search_jobs_raises_on_missing_board_token(self):
        adapter = AshbyAdapter()
        with pytest.raises(ValueError, match="board_token is required"):
            adapter.search_jobs()

    def test_search_jobs_wraps_http_error(self):
        adapter = AshbyAdapter()
        adapter.client = MagicMock()
        adapter.client.fetch_jobs.side_effect = requests.HTTPError("404")

        with pytest.raises(ValueError, match="Unable to fetch Ashby jobs"):
            adapter.search_jobs(board_token="bad-token")

    def test_search_jobs_filters_by_query(self):
        adapter = self._make_adapter([MINIMAL_JOB, JOB_WITH_COMPENSATION])
        jobs = adapter.search_jobs(board_token="acme", query="Staff")

        assert len(jobs) == 1
        assert jobs[0]["title"] == "Staff Engineer"

    def test_search_jobs_filters_by_location(self):
        adapter = self._make_adapter([MINIMAL_JOB, JOB_WITH_COMPENSATION])
        jobs = adapter.search_jobs(board_token="acme", location="New York")

        assert len(jobs) == 1
        assert jobs[0]["title"] == "Staff Engineer"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_get_adapter_returns_ashby_adapter(self):
        adapter = get_adapter("ashby")
        assert isinstance(adapter, AshbyAdapter)

    def test_get_adapter_ashby_case_insensitive(self):
        adapter = get_adapter("Ashby")
        assert isinstance(adapter, AshbyAdapter)
