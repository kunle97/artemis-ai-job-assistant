"""
Submit endpoint API tests.

Verifies that POST /applications/{id}/submit enforces all safety
guardrails before allowing form submission to proceed.
"""

import uuid
from unittest.mock import patch, MagicMock

import pytest

from src.domain.applications.repository import ApplicationRepository
from src.domain.jobs.repository import JobRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register_and_login(client, payload):
    client.post("/auth/register", json=payload)
    login = client.post(
        "/auth/login",
        data={"username": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def _create_fake_job(db_session):
    return str(
        JobRepository(db_session)
        .create(
            source="greenhouse",
            source_job_id=f"test-submit-{uuid.uuid4().hex[:6]}",
            title="Software Engineer",
            company_name="Submit Corp",
            location="Remote",
            workplace_type="remote",
            description="A job to test submission.",
            apply_url="https://boards.greenhouse.io/submitcorp/jobs/submit-test",
            salary_min=100000,
            salary_max=150000,
            currency="USD",
            is_active=True,
        )
        .id
    )


def _make_user_payload():
    uid = uuid.uuid4().hex[:8]
    return {
        "email": f"submit-{uid}@example.com",
        "password": "password123",
        "first_name": "Submit",
        "last_name": "Tester",
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_submit_returns_400_when_pipeline_not_run(client, db_session, sample_user_payload):
    """Should return 400 if the application has not gone through the fill pipeline."""
    token = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)

    create_resp = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"job_id": job_id},
    )
    assert create_resp.status_code == 200
    app_id = create_resp.json()["id"]

    # Application is in 'saved' or 'needs_review' — pipeline not run
    resp = client.post(
        f"/applications/{app_id}/submit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "Submission blocked" in resp.json()["detail"]


def test_submit_returns_403_for_different_user(client, db_session, sample_user_payload):
    """Should return 403 when a different user tries to submit another user's application."""
    owner_token = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)

    create_resp = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"job_id": job_id},
    )
    assert create_resp.status_code == 200
    app_id = create_resp.json()["id"]

    other_payload = _make_user_payload()
    other_token = _register_and_login(client, other_payload)

    resp = client.post(
        f"/applications/{app_id}/submit",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 403


def test_submit_returns_400_when_manual_review_required_and_not_authorized(
    client, db_session, sample_user_payload
):
    """Should block submission when manual review is required but not yet authorized."""
    token = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)

    create_resp = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"job_id": job_id},
    )
    assert create_resp.status_code == 200
    app_id = create_resp.json()["id"]

    # Manually put the application into filled state but without authorization
    ApplicationRepository(db_session).update_fields(
        uuid.UUID(app_id),
        status="filled",
        is_ready_for_automation=True,
        manual_review_required=True,
        is_authorized_to_submit=False,
    )

    resp = client.post(
        f"/applications/{app_id}/submit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "user authorization is required" in resp.json()["detail"]
