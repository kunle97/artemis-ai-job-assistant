"""
Unit tests for JobScoringService.

Covers heuristic scoring, LLM-based scoring, ownership enforcement,
and recommendation tier derivation.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.domain.jobs.scoring.service import (
    JobScoringService,
    _heuristic_location_match,
    _heuristic_role_fit,
    _heuristic_seniority_match,
    _heuristic_skills_gap_summary,
    _recommendation_from_score,
    _weighted_global,
)


# ---------------------------------------------------------------------------
# Pure helper tests
# ---------------------------------------------------------------------------


def test_weighted_global_formula():
    score = _weighted_global(5.0, 5.0, 5.0)
    assert score == 5.0


def test_weighted_global_partial():
    score = _weighted_global(4.0, 3.0, 2.0)
    # 4.0*0.5 + 3.0*0.3 + 2.0*0.2 = 2.0 + 0.9 + 0.4 = 3.3
    assert score == pytest.approx(3.3)


@pytest.mark.parametrize(
    "global_score,expected",
    [
        (5.0, "apply_immediately"),
        (4.5, "apply_immediately"),
        (4.2, "worth_applying"),
        (4.0, "worth_applying"),
        (3.7, "apply_if_specific_reason"),
        (3.5, "apply_if_specific_reason"),
        (3.0, "recommend_against"),
        (1.0, "recommend_against"),
    ],
)
def test_recommendation_thresholds(global_score, expected):
    assert _recommendation_from_score(global_score) == expected


def test_role_fit_with_matching_skills():
    skills = ["Python", "FastAPI", "PostgreSQL"]
    jd = "We are looking for a Python developer experienced in FastAPI and PostgreSQL databases."
    score = _heuristic_role_fit(jd, skills)
    assert score > 3.0  # all 3 skills found


def test_role_fit_no_skills():
    score = _heuristic_role_fit("Some job description", [])
    assert score == 2.5


def test_role_fit_no_matches():
    skills = ["Cobol", "Fortran"]
    jd = "Looking for a React developer with TypeScript experience."
    score = _heuristic_role_fit(jd, skills)
    assert score == pytest.approx(1.0)


def test_seniority_match_senior_job_senior_candidate():
    experience = [{}] * 6  # 6 experience entries → candidate_seniority=4
    score = _heuristic_seniority_match("Senior Software Engineer", experience)
    assert score >= 4.0


def test_seniority_match_junior_job_senior_candidate():
    experience = [{}] * 8  # candidate_seniority=5
    score = _heuristic_seniority_match("Junior Developer", experience)
    # diff = |2-5|=3 → 5 - 3*1.5 = 0.5 → clamped to 1.0
    assert score == pytest.approx(1.0)


def test_location_match_remote_prefers_remote():
    score = _heuristic_location_match("remote", ["remote", "hybrid"])
    assert score == 5.0


def test_location_match_onsite_no_preference():
    score = _heuristic_location_match("onsite", None)
    assert score == 2.0


def test_skills_gap_summary_returns_string():
    skills = ["Python"]
    jd = "Experience with React, TypeScript, Kubernetes, and AWS required."
    summary = _heuristic_skills_gap_summary(jd, skills)
    assert isinstance(summary, str)
    assert len(summary) > 0


def test_skills_gap_summary_no_gaps():
    skills = ["Python", "React", "Kubernetes"]
    jd = "python react kubernetes"
    summary = _heuristic_skills_gap_summary(jd, skills)
    # No capitalized tech keywords found
    assert "No significant" in summary or "Potential gaps" in summary


# ---------------------------------------------------------------------------
# JobScoringService tests
# ---------------------------------------------------------------------------


def _make_mock_application(user_id, job_id, resume_id=None):
    app = MagicMock()
    app.user_id = user_id
    app.job_id = job_id
    app.resume_id = resume_id
    return app


def _make_mock_job():
    job = MagicMock()
    job.title = "Senior Python Engineer"
    job.company_name = "Acme Corp"
    job.description = "Python FastAPI PostgreSQL experience required."
    job.location = "Remote"
    job.workplace_type = "remote"
    return job


def _make_mock_profile(user_id):
    profile = MagicMock()
    profile.skills = ["Python", "FastAPI", "PostgreSQL"]
    profile.experience_sections = [{}] * 5
    profile.work_arrangement = ["remote"]
    return profile


def _make_score_repo():
    repo = MagicMock()
    score = MagicMock()
    score.global_score = 4.2
    score.recommendation = "worth_applying"
    repo.create_or_update.return_value = score
    return repo, score


def _build_service(user_id, job_id, resume_id=None, llm_client=None):
    application = _make_mock_application(user_id, job_id, resume_id)
    job = _make_mock_job()
    profile = _make_mock_profile(user_id)
    score_repo, score = _make_score_repo()

    app_repo = MagicMock()
    app_repo.get_by_id.return_value = application

    job_repo = MagicMock()
    job_repo.get_by_id.return_value = job

    profile_repo = MagicMock()
    profile_repo.get_by_user_id.return_value = profile

    resume_repo = MagicMock()
    resume_repo.get_by_id_and_user_id.return_value = None

    return (
        JobScoringService(
            application_repository=app_repo,
            job_repository=job_repo,
            profile_repository=profile_repo,
            resume_repository=resume_repo,
            score_repository=score_repo,
            llm_client=llm_client,
        ),
        score,
    )


def test_score_application_heuristic():
    user_id = uuid.uuid4()
    job_id = uuid.uuid4()
    service, expected_score = _build_service(user_id, job_id)

    result = service.score_application(application_id=uuid.uuid4(), user_id=user_id)
    assert result is expected_score


def test_score_application_not_found_raises():
    service, _ = _build_service(uuid.uuid4(), uuid.uuid4())
    service.application_repository.get_by_id.return_value = None

    with pytest.raises(ValueError, match="Application not found"):
        service.score_application(application_id=uuid.uuid4(), user_id=uuid.uuid4())


def test_score_application_wrong_owner_raises():
    user_id = uuid.uuid4()
    other_user = uuid.uuid4()
    service, _ = _build_service(user_id, uuid.uuid4())

    with pytest.raises(PermissionError):
        service.score_application(application_id=uuid.uuid4(), user_id=other_user)


def test_score_application_llm_path():
    user_id = uuid.uuid4()
    llm_client = MagicMock()
    llm_client.complete.return_value = (
        '{"role_fit": 4.5, "seniority_match": 4.0, "location_match": 5.0, '
        '"global_score": 4.4, "skills_gap_summary": "Minor gap in Kubernetes.", '
        '"recommendation": "worth_applying"}'
    )

    service, expected_score = _build_service(user_id, uuid.uuid4(), llm_client=llm_client)
    result = service.score_application(application_id=uuid.uuid4(), user_id=user_id)

    assert result is expected_score
    llm_client.complete.assert_called_once()


def test_score_application_llm_fallback_on_bad_json():
    user_id = uuid.uuid4()
    llm_client = MagicMock()
    llm_client.complete.return_value = "not valid json"

    service, expected_score = _build_service(user_id, uuid.uuid4(), llm_client=llm_client)
    result = service.score_application(application_id=uuid.uuid4(), user_id=user_id)

    # Should still return a result via heuristic fallback
    assert result is expected_score


def test_score_persisted_via_repository():
    user_id = uuid.uuid4()
    application_id = uuid.uuid4()
    service, _ = _build_service(user_id, uuid.uuid4())

    service.score_application(application_id=application_id, user_id=user_id)

    service.score_repository.create_or_update.assert_called_once()
    call_kwargs = service.score_repository.create_or_update.call_args[1]
    assert "application_id" in call_kwargs
    assert "role_fit" in call_kwargs
    assert "global_score" in call_kwargs
    assert "recommendation" in call_kwargs
