"""
Application scoring API tests.

Verifies POST /applications/{application_id}/score returns a score result
and enforces ownership checks.
"""

import uuid

from src.domain.auth.repository import UserRepository
from src.domain.jobs.repository import JobRepository


def _register_and_login(client, sample_user_payload):
    client.post("/auth/register", json=sample_user_payload)
    response = client.post(
        "/auth/login",
        data={
            "username": sample_user_payload["email"],
            "password": sample_user_payload["password"],
        },
    )
    return response.json()["access_token"]


def _create_fake_job(db_session):
    repository = JobRepository(db_session)
    job = repository.create(
        source="greenhouse",
        source_job_id=f"score-test-{uuid.uuid4().hex[:8]}",
        title="Senior Python Engineer",
        company_name="Acme Corp",
        location="Remote",
        workplace_type="remote",
        description="Python FastAPI PostgreSQL Kubernetes experience required.",
        apply_url="https://job-boards.greenhouse.io/acme/jobs/1234",
        salary_min=140000,
        salary_max=180000,
        currency="USD",
        is_active=True,
    )
    return str(job.id)


def _get_user_id(db_session, email):
    return UserRepository(db_session).get_by_email(email).id


def _create_application(client, token, job_id):
    response = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"job_id": job_id},
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_score_application_returns_result(client, db_session, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)
    application_id = _create_application(client, token, job_id)

    response = client.post(
        f"/applications/{application_id}/score",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["application_id"] == application_id
    assert "global_score" in data
    assert data["global_score"] is not None
    assert "recommendation" in data
    assert data["recommendation"] in {
        "apply_immediately",
        "worth_applying",
        "apply_if_specific_reason",
        "recommend_against",
    }
    assert "role_fit" in data
    assert "seniority_match" in data
    assert "location_match" in data
    assert "skills_gap_summary" in data


def test_score_application_idempotent(client, db_session, sample_user_payload):
    """Scoring the same application twice should update and return a score each time."""
    token = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)
    application_id = _create_application(client, token, job_id)

    first = client.post(
        f"/applications/{application_id}/score",
        headers={"Authorization": f"Bearer {token}"},
    )
    second = client.post(
        f"/applications/{application_id}/score",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["application_id"] == second.json()["application_id"]


def test_score_application_unauthenticated(client, db_session):
    response = client.post(f"/applications/{uuid.uuid4()}/score")
    assert response.status_code == 401


def test_score_application_not_found(client, db_session, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)
    response = client.post(
        f"/applications/{uuid.uuid4()}/score",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_score_application_forbidden_for_other_user(client, db_session, sample_user_payload):
    """A user cannot score another user's application."""
    token_a = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)
    application_id = _create_application(client, token_a, job_id)

    # Register a second user
    other_payload = {
        "email": f"other-{uuid.uuid4().hex[:8]}@example.com",
        "password": "password123",
        "first_name": "Other",
        "last_name": "User",
    }
    token_b = _register_and_login(client, other_payload)

    response = client.post(
        f"/applications/{application_id}/score",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 403
