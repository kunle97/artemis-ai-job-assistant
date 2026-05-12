"""
Resume tailoring API tests.

Covers success, ownership enforcement, and deterministic fallback behavior
for POST /applications/{application_id}/tailor-resume.
"""

import uuid

from src.core.config import settings
from src.domain.auth.repository import UserRepository
from src.domain.jobs.repository import JobRepository
from src.domain.resume.repository import ResumeRepository
from src.integrations.groq.client import GroqClient


def _register_and_login(client, sample_user_payload):
    register_response = client.post("/auth/register", json=sample_user_payload)
    assert register_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        data={
            "username": sample_user_payload["email"],
            "password": sample_user_payload["password"],
        },
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def _create_job_with_description(db_session):
    repository = JobRepository(db_session)
    job = repository.create(
        source="greenhouse",
        source_job_id=f"tailor-{uuid.uuid4().hex[:8]}",
        title="Senior Backend Engineer",
        company_name="Acme Corp",
        location="Remote",
        workplace_type="remote",
        description=(
            "Build scalable FastAPI services, improve observability, and collaborate across product teams. "
            "Strong Python, SQL, and cloud deployment experience required."
        ),
        apply_url="https://boards.example.com/acme/123",
        is_active=True,
    )
    return str(job.id)


def _get_user_id(db_session, email: str):
    user = UserRepository(db_session).get_by_email(email)
    return user.id


def _create_resume(db_session, user_id):
    return ResumeRepository(db_session).create(
        user_id=user_id,
        file_name="resume.pdf",
        file_path="/uploads/resume.pdf",
        mime_type="application/pdf",
        extracted_text="Senior Python engineer with experience building APIs and distributed systems.",
        parsed_json={
            "normalized_data": {
                "headline_title": "Senior Backend Engineer",
                "skills": ["Python", "FastAPI", "PostgreSQL"],
            }
        },
    )


def _create_application(client, token, job_id, resume_id):
    response = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "job_id": job_id,
            "resume_id": str(resume_id),
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_tailor_resume_success(client, db_session, sample_user_payload, monkeypatch):
    token = _register_and_login(client, sample_user_payload)
    user_id = _get_user_id(db_session, sample_user_payload["email"])
    resume = _create_resume(db_session, user_id)
    job_id = _create_job_with_description(db_session)
    application_id = _create_application(client, token, job_id, resume.id)

    monkeypatch.setattr(settings, "groq_api_key", "test-key")

    def _fake_complete(self, *, system: str, user: str, max_tokens: int = 300):
        return (
            '{"suggestions": ['
            '{"section":"summary","current_text":"Experienced engineer","proposed_text":"Backend engineer focused on scalable Python services.",'
            '"reason":"Aligns with Python/FastAPI emphasis","matched_keywords":["python","fastapi"],"missing_keywords":["observability"]}'
            ']}'
        )

    monkeypatch.setattr(GroqClient, "complete", _fake_complete)

    response = client.post(
        f"/applications/{application_id}/tailor-resume",
        headers={"Authorization": f"Bearer {token}"},
        json={"resume_id": str(resume.id)},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["application_id"] == application_id
    assert data["resume_id"] == str(resume.id)
    assert data["is_fallback"] is False
    assert len(data["suggestions"]) >= 1
    assert data["suggestions"][0]["section"] == "summary"
    assert data["suggestions"][0]["proposed_text"]
    assert data["suggestions"][0]["reason"]


def test_tailor_resume_forbidden_for_other_user(client, db_session, sample_user_payload):
    token_a = _register_and_login(client, sample_user_payload)
    user_id = _get_user_id(db_session, sample_user_payload["email"])
    resume = _create_resume(db_session, user_id)
    job_id = _create_job_with_description(db_session)
    application_id = _create_application(client, token_a, job_id, resume.id)

    other_payload = {
        "email": f"other-{uuid.uuid4().hex[:8]}@example.com",
        "password": "password123",
        "first_name": "Other",
        "last_name": "User",
    }
    token_b = _register_and_login(client, other_payload)

    response = client.post(
        f"/applications/{application_id}/tailor-resume",
        headers={"Authorization": f"Bearer {token_b}"},
        json={},
    )

    assert response.status_code == 403


def test_tailor_resume_fallback_when_llm_unavailable(client, db_session, sample_user_payload, monkeypatch):
    token = _register_and_login(client, sample_user_payload)
    user_id = _get_user_id(db_session, sample_user_payload["email"])
    resume = _create_resume(db_session, user_id)
    job_id = _create_job_with_description(db_session)
    application_id = _create_application(client, token, job_id, resume.id)

    monkeypatch.setattr(settings, "groq_api_key", None)

    response = client.post(
        f"/applications/{application_id}/tailor-resume",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_fallback"] is True
    assert data["suggestions"] == []
    assert "LLM provider unavailable" in (data["message"] or "")
