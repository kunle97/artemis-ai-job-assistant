"""
Unit tests for JobFeedService.

Covers: title keyword filter, in-memory dedup, DB dedup,
        partial board failure continues scan.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.domain.jobs.feed_service import JobFeedService

# ---------------------------------------------------------------------------
# Shared test fixtures & helpers
# ---------------------------------------------------------------------------

MOCK_JOB_SOURCES = [
    SimpleNamespace(source="greenhouse", company_key="stripe", board_token="stripe", display_name="Stripe"),
    SimpleNamespace(source="greenhouse", company_key="figma", board_token="figma", display_name="Figma"),
    SimpleNamespace(source="lever", company_key="netflix", board_token="netflix", display_name="Netflix"),
]


def _make_job_data(source="greenhouse", source_job_id="1", title="Software Engineer"):
    return {
        "source": source,
        "source_job_id": source_job_id,
        "title": title,
        "company_name": "acme",
        "location": "Remote",
        "workplace_type": None,
        "description": None,
        "apply_url": f"https://example.com/jobs/{source_job_id}",
        "salary_min": None,
        "salary_max": None,
        "currency": None,
        "is_active": True,
    }


def _make_preferences(enabled_sources=None, target_titles=None):
    prefs = MagicMock()
    prefs.enabled_sources = enabled_sources or []
    prefs.target_titles = target_titles or []
    return prefs


def _make_service(user_id=None):
    """Return a JobFeedService with a MagicMock db."""
    return JobFeedService(user_id=user_id or uuid.uuid4(), db=MagicMock())


# ---------------------------------------------------------------------------
# Helper: common patch stack
# ---------------------------------------------------------------------------

PATCH_PREFS_REPO = "src.domain.jobs.feed_service.JobPreferencesRepository"
PATCH_JOB_REPO = "src.domain.jobs.feed_service.JobRepository"
PATCH_JOB_SOURCE_REPO = "src.domain.jobs.feed_service.JobSourceRepository"
PATCH_USER_FEED_REPO = "src.domain.jobs.feed_service.JobUserFeedRepository"
PATCH_GET_ADAPTER = "src.domain.jobs.feed_service.get_adapter"


# ---------------------------------------------------------------------------
# Tests: title keyword filter
# ---------------------------------------------------------------------------

class TestTitleKeywordFilter:
    def test_jobs_matching_target_title_are_kept(self):
        with (
            patch(PATCH_PREFS_REPO) as mock_prefs_cls,
            patch(PATCH_JOB_REPO) as mock_job_cls,
            patch(PATCH_JOB_SOURCE_REPO) as mock_job_source_cls,
            patch(PATCH_USER_FEED_REPO) as mock_user_feed_cls,
            patch(PATCH_GET_ADAPTER) as mock_get_adapter,
        ):
            mock_prefs_cls.return_value.get_or_create_by_user_id.return_value = (
                _make_preferences(enabled_sources=["greenhouse"], target_titles=["engineer"])
            )
            mock_job_source_cls.return_value.list_active.return_value = MOCK_JOB_SOURCES

            mock_adapter = MagicMock()
            mock_adapter.search_jobs.return_value = [
                _make_job_data(source_job_id="1", title="Software Engineer"),
                _make_job_data(source_job_id="2", title="Marketing Manager"),
            ]
            mock_get_adapter.return_value = mock_adapter

            mock_job_cls.return_value.get_or_create.side_effect = lambda **kw: MagicMock(
                source=kw["source"], source_job_id=kw["source_job_id"]
            )
            mock_user_feed_cls.return_value.get_or_create.return_value = (MagicMock(), True)

            service = _make_service()
            result = service.scan()

        # Only "Software Engineer" matches "engineer"
        assert len(result) == 1
        assert result[0].source_job_id == "1"

    def test_no_target_titles_keeps_all_jobs(self):
        with (
            patch(PATCH_PREFS_REPO) as mock_prefs_cls,
            patch(PATCH_JOB_REPO) as mock_job_cls,
            patch(PATCH_JOB_SOURCE_REPO) as mock_job_source_cls,
            patch(PATCH_USER_FEED_REPO) as mock_user_feed_cls,
            patch(PATCH_GET_ADAPTER) as mock_get_adapter,
        ):
            mock_prefs_cls.return_value.get_or_create_by_user_id.return_value = (
                _make_preferences(enabled_sources=["greenhouse"], target_titles=[])
            )
            mock_job_source_cls.return_value.list_active.return_value = MOCK_JOB_SOURCES

            mock_adapter = MagicMock()
            mock_adapter.search_jobs.return_value = [
                _make_job_data(source_job_id="1", title="Software Engineer"),
                _make_job_data(source_job_id="2", title="Marketing Manager"),
            ]
            mock_get_adapter.return_value = mock_adapter

            mock_job_cls.return_value.get_or_create.side_effect = lambda **kw: MagicMock(
                source=kw["source"], source_job_id=kw["source_job_id"]
            )
            mock_user_feed_cls.return_value.get_or_create.return_value = (MagicMock(), True)

            service = _make_service()
            result = service.scan()

        assert len(result) == 2


# ---------------------------------------------------------------------------
# Tests: deduplication
# ---------------------------------------------------------------------------

class TestDeduplication:
    def test_in_memory_dedup_removes_duplicate_across_boards(self):
        """Same (source, source_job_id) returned by two boards is created once."""
        with (
            patch(PATCH_PREFS_REPO) as mock_prefs_cls,
            patch(PATCH_JOB_REPO) as mock_job_cls,
            patch(PATCH_JOB_SOURCE_REPO) as mock_job_source_cls,
            patch(PATCH_USER_FEED_REPO) as mock_user_feed_cls,
            patch(PATCH_GET_ADAPTER) as mock_get_adapter,
        ):
            mock_prefs_cls.return_value.get_or_create_by_user_id.return_value = (
                _make_preferences(enabled_sources=["greenhouse"])
            )
            mock_job_source_cls.return_value.list_active.return_value = MOCK_JOB_SOURCES

            duplicate = _make_job_data(source_job_id="99", title="Data Engineer")
            mock_adapter = MagicMock()
            # Both boards return the same job
            mock_adapter.search_jobs.return_value = [duplicate]
            mock_get_adapter.return_value = mock_adapter

            created = []

            def _create(**kw):
                job = MagicMock(source=kw["source"], source_job_id=kw["source_job_id"])
                created.append(job)
                return job

            mock_job_cls.return_value.get_or_create.side_effect = _create
            mock_user_feed_cls.return_value.get_or_create.return_value = (MagicMock(), True)

            service = _make_service()
            result = service.scan()

        # Even though two boards return the duplicate, we create it only once
        assert len(result) == 1
        assert len(created) == 1

    def test_db_dedup_skips_already_stored_jobs(self):
        """Jobs already in the DB are not re-created and not returned."""
        with (
            patch(PATCH_PREFS_REPO) as mock_prefs_cls,
            patch(PATCH_JOB_REPO) as mock_job_cls,
            patch(PATCH_JOB_SOURCE_REPO) as mock_job_source_cls,
            patch(PATCH_USER_FEED_REPO) as mock_user_feed_cls,
            patch(PATCH_GET_ADAPTER) as mock_get_adapter,
        ):
            mock_prefs_cls.return_value.get_or_create_by_user_id.return_value = (
                _make_preferences(enabled_sources=["greenhouse"])
            )
            mock_job_source_cls.return_value.list_active.return_value = [
                SimpleNamespace(
                    source="greenhouse",
                    company_key="stripe",
                    board_token="stripe",
                    display_name="Stripe",
                )
            ]

            mock_adapter = MagicMock()
            mock_adapter.search_jobs.return_value = [
                _make_job_data(source_job_id="existing", title="Backend Engineer"),
            ]
            mock_get_adapter.return_value = mock_adapter

            mock_job_cls.return_value.get_or_create.return_value = MagicMock(id=uuid.uuid4())
            mock_user_feed_cls.return_value.get_or_create.return_value = (MagicMock(), False)

            service = _make_service()
            result = service.scan()

        assert result == []
        mock_user_feed_cls.return_value.get_or_create.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: partial failure
# ---------------------------------------------------------------------------

class TestPartialFailure:
    def test_board_failure_continues_scan(self):
        """A failing board is skipped; other boards still yield results."""
        with (
            patch(PATCH_PREFS_REPO) as mock_prefs_cls,
            patch(PATCH_JOB_REPO) as mock_job_cls,
            patch(PATCH_JOB_SOURCE_REPO) as mock_job_source_cls,
            patch(PATCH_USER_FEED_REPO) as mock_user_feed_cls,
            patch(PATCH_GET_ADAPTER) as mock_get_adapter,
        ):
            mock_prefs_cls.return_value.get_or_create_by_user_id.return_value = (
                _make_preferences(enabled_sources=["greenhouse"])
            )
            mock_job_source_cls.return_value.list_active.return_value = MOCK_JOB_SOURCES

            def _search_jobs(board_token):
                if board_token == "stripe":
                    raise RuntimeError("Connection timeout")
                return [_make_job_data(source_job_id="figma-1", title="Staff Engineer")]

            mock_adapter = MagicMock()
            mock_adapter.search_jobs.side_effect = _search_jobs
            mock_get_adapter.return_value = mock_adapter

            mock_job_cls.return_value.get_or_create.side_effect = lambda **kw: MagicMock(
                source=kw["source"], source_job_id=kw["source_job_id"]
            )
            mock_user_feed_cls.return_value.get_or_create.return_value = (MagicMock(), True)

            service = _make_service()
            result = service.scan()

        # Figma board succeeded; stripe failed but was swallowed
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Tests: edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_enabled_sources_returns_empty(self):
        with (
            patch(PATCH_PREFS_REPO) as mock_prefs_cls,
            patch(PATCH_JOB_REPO),
            patch(PATCH_JOB_SOURCE_REPO),
            patch(PATCH_USER_FEED_REPO),
            patch(PATCH_GET_ADAPTER) as mock_get_adapter,
        ):
            mock_prefs_cls.return_value.get_or_create_by_user_id.return_value = (
                _make_preferences(enabled_sources=[])
            )

            service = _make_service()
            result = service.scan()

        assert result == []
        mock_get_adapter.assert_not_called()

    def test_source_not_in_registry_returns_empty(self):
        with (
            patch(PATCH_PREFS_REPO) as mock_prefs_cls,
            patch(PATCH_JOB_REPO),
            patch(PATCH_JOB_SOURCE_REPO) as mock_job_source_cls,
            patch(PATCH_GET_ADAPTER) as mock_get_adapter,
        ):
            mock_prefs_cls.return_value.get_or_create_by_user_id.return_value = (
                _make_preferences(enabled_sources=["greenhouse"])
            )
            mock_job_source_cls.return_value.list_active.return_value = []

            service = _make_service()
            result = service.scan()

        assert result == []
        mock_get_adapter.assert_not_called()
