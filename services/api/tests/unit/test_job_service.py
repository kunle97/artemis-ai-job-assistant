"""
Unit tests for JobService.

Covers applying title keyword preferences during search-and-store flows.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.domain.jobs.schemas import JobSearchRequest
from src.domain.jobs.service import JobService


@patch("src.domain.jobs.service.resolve_board_tokens", return_value=["stripe"])
@patch("src.domain.jobs.service.get_adapter")
def test_search_and_store_jobs_applies_user_title_filters(mock_get_adapter, _mock_tokens):
    adapter = MagicMock()
    adapter.search_jobs.return_value = [
        {
            "source": "greenhouse",
            "source_job_id": "1",
            "title": "Senior Python Engineer",
            "company_name": "Acme",
            "apply_url": "https://example.com/1",
            "location": "Remote",
            "workplace_type": "remote",
            "description": "Python",
            "salary_min": None,
            "salary_max": None,
            "currency": None,
            "is_active": True,
        },
        {
            "source": "greenhouse",
            "source_job_id": "2",
            "title": "PHP Engineer",
            "company_name": "Acme",
            "apply_url": "https://example.com/2",
            "location": "Remote",
            "workplace_type": "remote",
            "description": "PHP",
            "salary_min": None,
            "salary_max": None,
            "currency": None,
            "is_active": True,
        },
    ]
    mock_get_adapter.return_value = adapter

    repo = MagicMock()
    repo.get_or_create.side_effect = lambda **job_data: SimpleNamespace(**job_data)

    prefs_repo = MagicMock()
    prefs_repo.get_or_create_by_user_id.return_value = SimpleNamespace(
        positive_keywords=["python"],
        negative_keywords=["php"],
    )

    service = JobService(repository=repo, preferences_repository=prefs_repo)
    payload = JobSearchRequest(source="greenhouse", company_name="stripe")

    jobs, total = service.search_and_store_jobs(payload, user_id="user-1")

    assert total == 1
    assert len(jobs) == 1
    assert jobs[0].source_job_id == "1"
    repo.get_or_create.assert_called_once()


@patch("src.domain.jobs.service.resolve_board_tokens", return_value=["stripe"])
@patch("src.domain.jobs.service.get_adapter")
def test_search_and_store_jobs_without_user_preferences_keeps_all(mock_get_adapter, _mock_tokens):
    adapter = MagicMock()
    adapter.search_jobs.return_value = [
        {
            "source": "greenhouse",
            "source_job_id": "1",
            "title": "Senior Python Engineer",
            "company_name": "Acme",
            "apply_url": "https://example.com/1",
            "location": "Remote",
            "workplace_type": "remote",
            "description": "Python",
            "salary_min": None,
            "salary_max": None,
            "currency": None,
            "is_active": True,
        },
        {
            "source": "greenhouse",
            "source_job_id": "2",
            "title": "PHP Engineer",
            "company_name": "Acme",
            "apply_url": "https://example.com/2",
            "location": "Remote",
            "workplace_type": "remote",
            "description": "PHP",
            "salary_min": None,
            "salary_max": None,
            "currency": None,
            "is_active": True,
        },
    ]
    mock_get_adapter.return_value = adapter

    repo = MagicMock()
    repo.get_or_create.side_effect = lambda **job_data: SimpleNamespace(**job_data)

    service = JobService(repository=repo)
    payload = JobSearchRequest(source="greenhouse", company_name="stripe")

    jobs, total = service.search_and_store_jobs(payload)

    assert total == 2
    assert len(jobs) == 2
    assert {job.source_job_id for job in jobs} == {"1", "2"}
    assert repo.get_or_create.call_count == 2
