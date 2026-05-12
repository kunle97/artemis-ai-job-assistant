"""
Unit tests for ResumeTailoringService.

Covers ownership checks, deterministic fallback behavior, and
LLM JSON normalization into structured recommendation objects.
"""

from datetime import UTC, datetime
import uuid
from unittest.mock import MagicMock

import pytest

from src.domain.resume.tailoring.service import ResumeTailoringService


def _build_repo(*, owner_user_id, include_resume=True, include_job_description=True):
    application = MagicMock()
    application.id = uuid.uuid4()
    application.user_id = owner_user_id
    application.job_id = uuid.uuid4()
    application.resume_id = uuid.uuid4() if include_resume else None

    resume = None
    if include_resume:
        resume = MagicMock()
        resume.id = application.resume_id
        resume.extracted_text = "Backend engineer with Python and distributed systems experience."
        resume.parsed_json = {
            "normalized_data": {
                "headline_title": "Senior Backend Engineer",
                "skills": ["Python", "FastAPI", "PostgreSQL"],
            }
        }

    profile = MagicMock()
    profile.current_company = "Acme"
    profile.work_arrangement = "remote"
    profile.skills = ["Python", "FastAPI"]

    job = MagicMock()
    job.id = application.job_id
    job.title = "Senior Backend Engineer"
    job.company_name = "Acme"
    job.description = (
        "Build scalable Python services with FastAPI, PostgreSQL, and strong observability practices."
        if include_job_description
        else ""
    )

    repo = MagicMock()
    repo.get_application.return_value = application
    repo.get_resume_by_user.return_value = resume
    repo.get_latest_resume_for_user.return_value = resume
    repo.get_profile_for_user.return_value = profile
    repo.get_job.return_value = job
    return repo, application, resume


def test_tailor_resume_forbidden_for_non_owner():
    owner = uuid.uuid4()
    other_user = uuid.uuid4()
    repo, application, _ = _build_repo(owner_user_id=owner)

    service = ResumeTailoringService(repository=repo, llm_client=None)

    with pytest.raises(PermissionError):
        service.tailor_resume(
            user_id=other_user,
            application_id=application.id,
            resume_id=None,
        )


def test_tailor_resume_fallback_when_llm_missing():
    owner = uuid.uuid4()
    repo, application, resume = _build_repo(owner_user_id=owner)

    service = ResumeTailoringService(repository=repo, llm_client=None)
    result = service.tailor_resume(
        user_id=owner,
        application_id=application.id,
        resume_id=resume.id,
    )

    assert result.application_id == application.id
    assert result.is_fallback is True
    assert result.suggestions == []
    assert "LLM provider unavailable" in (result.message or "")


def test_tailor_resume_fallback_when_jd_missing():
    owner = uuid.uuid4()
    repo, application, resume = _build_repo(owner_user_id=owner, include_job_description=False)

    llm_client = MagicMock()
    service = ResumeTailoringService(repository=repo, llm_client=llm_client)
    result = service.tailor_resume(
        user_id=owner,
        application_id=application.id,
        resume_id=resume.id,
    )

    assert result.is_fallback is True
    assert result.suggestions == []
    assert "Job description is missing" in (result.message or "")


def test_tailor_resume_parses_llm_json_suggestions():
    owner = uuid.uuid4()
    repo, application, resume = _build_repo(owner_user_id=owner)

    llm_client = MagicMock()
    llm_client.complete.return_value = (
        '{"suggestions": ['
        '{"section":"summary","current_text":"Experienced engineer",'
        '"proposed_text":"Backend engineer focused on scalable Python systems.",'
        '"reason":"Align with JD keywords",'
        '"matched_keywords":["python","fastapi"],'
        '"missing_keywords":["observability"]}'
        ']}'
    )

    service = ResumeTailoringService(repository=repo, llm_client=llm_client)
    result = service.tailor_resume(
        user_id=owner,
        application_id=application.id,
        resume_id=resume.id,
    )

    assert result.is_fallback is False
    assert result.suggestions
    first = result.suggestions[0]
    assert first.section == "summary"
    assert first.proposed_text
    assert first.reason
    assert "python" in first.matched_keywords
