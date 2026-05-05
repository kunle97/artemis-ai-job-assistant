"""
Unit tests for adapter output normalization.

Verifies that Greenhouse, Lever, and Ashby adapter outputs normalize
correctly into Artemis Job model fields using fixture JSON payloads that
mirror real API responses.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.integrations.adapters.greenhouse.adapter import GreenhouseAdapter
from src.integrations.adapters.lever.adapter import LeverAdapter
from src.integrations.adapters.ashby.adapter import AshbyAdapter
from src.domain.jobs.helpers import filter_job_by_title

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load(filename: str) -> dict | list:
    return json.loads((FIXTURES_DIR / filename).read_text())


# ---------------------------------------------------------------------------
# Greenhouse normalization
# ---------------------------------------------------------------------------

class TestGreenhouseNormalization:
    def _adapter(self, raw_jobs: list[dict]) -> GreenhouseAdapter:
        from unittest.mock import MagicMock
        adapter = GreenhouseAdapter()
        adapter.client = MagicMock()
        adapter.client.fetch_jobs.return_value = raw_jobs
        return adapter

    def _jobs(self) -> list[dict]:
        return _load("greenhouse_jobs_response.json")["jobs"]

    def test_required_fields_populated(self):
        jobs = self._adapter(self._jobs()).search_jobs(board_token="acme")
        assert len(jobs) == 2
        for job in jobs:
            assert job["source"] == "greenhouse"
            assert isinstance(job["source_job_id"], str)
            assert job["source_job_id"] != ""
            assert job["title"]
            assert job["company_name"] == "acme"
            assert job["apply_url"]

    def test_location_populated_from_location_object(self):
        jobs = self._adapter(self._jobs()).search_jobs(board_token="acme")
        assert jobs[0]["location"] == "San Francisco, CA"
        assert jobs[1]["location"] == "Remote"

    def test_apply_url_contains_board_token_and_id(self):
        jobs = self._adapter(self._jobs()).search_jobs(board_token="acme")
        assert "acme" in jobs[0]["apply_url"]
        assert "11111" in jobs[0]["apply_url"]

    def test_missing_location_produces_none(self):
        raw_no_loc = {
            "id": 99999,
            "title": "No Location Job",
            "absolute_url": "https://boards.greenhouse.io/acme/jobs/99999",
        }
        adapter = GreenhouseAdapter()
        result = adapter._normalize_job(raw_no_loc, board_token="acme")
        assert result["location"] is None

    def test_missing_salary_produces_none(self):
        jobs = self._adapter(self._jobs()).search_jobs(board_token="acme")
        # First fixture job has no salary metadata
        assert jobs[0]["salary_min"] is None
        assert jobs[0]["salary_max"] is None

    def test_source_job_id_is_string(self):
        jobs = self._adapter(self._jobs()).search_jobs(board_token="acme")
        for job in jobs:
            assert isinstance(job["source_job_id"], str)
            assert len(job["source_job_id"]) > 0


# ---------------------------------------------------------------------------
# Lever normalization
# ---------------------------------------------------------------------------

class TestLeverNormalization:
    def _adapter(self, raw_jobs: list[dict]) -> LeverAdapter:
        from unittest.mock import MagicMock
        adapter = LeverAdapter()
        adapter.client = MagicMock()
        adapter.client.fetch_jobs.return_value = raw_jobs
        return adapter

    def _jobs(self) -> list[dict]:
        return _load("lever_jobs_response.json")

    def test_required_fields_populated(self):
        jobs = self._adapter(self._jobs()).search_jobs(board_token="acme")
        assert len(jobs) == 2
        for job in jobs:
            assert job["source"] == "lever"
            assert isinstance(job["source_job_id"], str)
            assert job["source_job_id"] != ""
            assert job["title"]
            assert job["company_name"] == "acme"
            assert job["apply_url"]

    def test_location_populated_from_categories(self):
        jobs = self._adapter(self._jobs()).search_jobs(board_token="acme")
        assert jobs[0]["location"] == "San Francisco, CA"
        assert jobs[1]["location"] == "Remote"

    def test_apply_url_is_hosted_url(self):
        jobs = self._adapter(self._jobs()).search_jobs(board_token="acme")
        assert "lever.co" in jobs[0]["apply_url"]
        assert "lever-aaa-111" in jobs[0]["apply_url"]

    def test_missing_categories_produces_none_location(self):
        raw_no_cat = {
            "id": "lever-zzz-999",
            "text": "No Categories Job",
            "hostedUrl": "https://jobs.lever.co/acme/lever-zzz-999",
        }
        adapter = LeverAdapter()
        result = adapter._normalize_job(raw_no_cat, board_token="acme")
        assert result["location"] is None

    def test_missing_salary_produces_none(self):
        jobs = self._adapter(self._jobs()).search_jobs(board_token="acme")
        # Lever adapter does not parse salaryRange — always None
        for job in jobs:
            assert job["salary_min"] is None
            assert job["salary_max"] is None

    def test_source_job_id_is_string(self):
        jobs = self._adapter(self._jobs()).search_jobs(board_token="acme")
        for job in jobs:
            assert isinstance(job["source_job_id"], str)
            assert len(job["source_job_id"]) > 0


# ---------------------------------------------------------------------------
# Ashby normalization
# ---------------------------------------------------------------------------

class TestAshbyNormalization:
    def _adapter(self, raw_jobs: list[dict]) -> AshbyAdapter:
        from unittest.mock import MagicMock
        adapter = AshbyAdapter()
        adapter.client = MagicMock()
        adapter.client.fetch_jobs.return_value = raw_jobs
        return adapter

    def _jobs(self) -> list[dict]:
        return _load("ashby_jobs_response.json")["jobs"]

    def test_required_fields_populated(self):
        jobs = self._adapter(self._jobs()).search_jobs(board_token="acme")
        assert len(jobs) == 2
        for job in jobs:
            assert job["source"] == "ashby"
            assert isinstance(job["source_job_id"], str)
            assert job["source_job_id"] != ""
            assert job["title"]
            assert job["company_name"] == "acme"
            assert job["apply_url"]

    def test_location_populated_directly(self):
        jobs = self._adapter(self._jobs()).search_jobs(board_token="acme")
        assert jobs[0]["location"] == "San Francisco, CA"
        assert jobs[1]["location"] == "Remote"

    def test_apply_url_is_job_url(self):
        jobs = self._adapter(self._jobs()).search_jobs(board_token="acme")
        assert "ashbyhq.com" in jobs[0]["apply_url"]
        assert "ashby-ccc-333" in jobs[0]["apply_url"]

    def test_missing_location_produces_none(self):
        raw_no_loc = {
            "id": "ashby-zzz-999",
            "title": "No Location Job",
            "jobUrl": "https://jobs.ashbyhq.com/acme/ashby-zzz-999",
        }
        adapter = AshbyAdapter()
        result = adapter._normalize_job(raw_no_loc, board_token="acme")
        assert result["location"] is None

    def test_job_without_compensation_has_none_salary(self):
        jobs = self._adapter(self._jobs()).search_jobs(board_token="acme")
        # First fixture job has no compensation block
        assert jobs[0]["salary_min"] is None
        assert jobs[0]["salary_max"] is None
        assert jobs[0]["currency"] is None

    def test_job_with_compensation_populates_salary_fields(self):
        jobs = self._adapter(self._jobs()).search_jobs(board_token="acme")
        # Second fixture job has compensation
        assert jobs[1]["salary_min"] == 140000
        assert jobs[1]["salary_max"] == 180000
        assert jobs[1]["currency"] == "USD"

    def test_source_job_id_is_string(self):
        jobs = self._adapter(self._jobs()).search_jobs(board_token="acme")
        for job in jobs:
            assert isinstance(job["source_job_id"], str)
            assert len(job["source_job_id"]) > 0


# ---------------------------------------------------------------------------
# filter_job_by_title gates results before get_or_create
# ---------------------------------------------------------------------------

class TestFilterJobByTitleGating:
    """Verify filter_job_by_title correctly gates which jobs reach persistence."""

    def _normalized_jobs(self, adapter, raw_jobs: list[dict], board_token: str = "acme") -> list[dict]:
        from unittest.mock import MagicMock
        adapter.client = MagicMock()
        adapter.client.fetch_jobs.return_value = raw_jobs
        return adapter.search_jobs(board_token=board_token)

    def test_positive_keyword_passes_matching_title(self):
        result = filter_job_by_title(
            title="Senior Backend Engineer",
            positive=["backend"],
            negative=[],
        )
        assert result is True

    def test_positive_keyword_blocks_non_matching_title(self):
        result = filter_job_by_title(
            title="Senior Backend Engineer",
            positive=["frontend"],
            negative=[],
        )
        assert result is False

    def test_negative_keyword_blocks_matching_title(self):
        result = filter_job_by_title(
            title="Senior DevOps Engineer",
            positive=[],
            negative=["devops"],
        )
        assert result is False

    def test_no_keywords_always_passes(self):
        for title in ["Backend Engineer", "Data Scientist", "Product Manager"]:
            assert filter_job_by_title(title=title, positive=[], negative=[]) is True

    def test_greenhouse_jobs_filtered_by_positive_keyword(self):
        raw_jobs = _load("greenhouse_jobs_response.json")["jobs"]
        from unittest.mock import MagicMock
        adapter = GreenhouseAdapter()
        adapter.client = MagicMock()
        adapter.client.fetch_jobs.return_value = raw_jobs
        all_jobs = adapter.search_jobs(board_token="acme")

        filtered = [
            j for j in all_jobs
            if filter_job_by_title(j["title"], positive=["backend"], negative=[])
        ]
        assert len(filtered) == 1
        assert "backend" in filtered[0]["title"].lower()

    def test_lever_jobs_filtered_by_negative_keyword(self):
        raw_jobs = _load("lever_jobs_response.json")
        from unittest.mock import MagicMock
        adapter = LeverAdapter()
        adapter.client = MagicMock()
        adapter.client.fetch_jobs.return_value = raw_jobs
        all_jobs = adapter.search_jobs(board_token="acme")

        filtered = [
            j for j in all_jobs
            if filter_job_by_title(j["title"], positive=[], negative=["data"])
        ]
        # "Staff Data Scientist" should be blocked; only "Senior Backend Engineer" passes
        assert len(filtered) == 1
        assert "data" not in filtered[0]["title"].lower()

    def test_ashby_jobs_all_pass_with_no_keywords(self):
        raw_jobs = _load("ashby_jobs_response.json")["jobs"]
        from unittest.mock import MagicMock
        adapter = AshbyAdapter()
        adapter.client = MagicMock()
        adapter.client.fetch_jobs.return_value = raw_jobs
        all_jobs = adapter.search_jobs(board_token="acme")

        filtered = [
            j for j in all_jobs
            if filter_job_by_title(j["title"], positive=[], negative=[])
        ]
        assert len(filtered) == len(all_jobs)
