"""
Application authorization API tests.

Verifies the manual review gate: pipeline halts at 'filled' when
manual_review_required is True, /authorize unblocks it, and a different
user cannot authorize another user's application.
"""

import uuid

import pytest

from src.domain.applications.models import Application
from src.domain.applications.pipeline_service import ApplicationPipelineService
from src.domain.applications.repository import ApplicationRepository
from src.domain.auth.repository import UserRepository
from src.domain.jobs.repository import JobRepository
from src.domain.resume.repository import ResumeRepository


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
            source_job_id=f"test-gate-{uuid.uuid4().hex[:6]}",
            title="Software Engineer",
            company_name="Acme",
            location="Remote",
            workplace_type="remote",
            description="Build things.",
            apply_url="https://boards.greenhouse.io/acme/jobs/gate-test",
            salary_min=120000,
            salary_max=160000,
            currency="USD",
            is_active=True,
        )
        .id
    )


def _make_user_payload():
    uid = uuid.uuid4().hex[:8]
    return {
        "email": f"gate-{uid}@example.com",
        "password": "password123",
        "first_name": "Gate",
        "last_name": "Tester",
    }


# ---------------------------------------------------------------------------
# Pipeline gate unit tests  (no HTTP, uses ApplicationPipelineService directly)
# ---------------------------------------------------------------------------

class _FakeApplication:
    """Minimal stand-in for an Application row."""

    def __init__(self, *, status, manual_review_required, is_authorized_to_submit):
        self.id = uuid.uuid4()
        self.status = status
        self.manual_review_required = manual_review_required
        self.is_authorized_to_submit = is_authorized_to_submit


def _make_gate_service():
    """Build a minimal ApplicationPipelineService for gate-only tests."""
    return ApplicationPipelineService(
        application_repo=None,
        job_repo=None,
        automation_service=None,
        planning_service=None,
        fill_service=None,
    )


def test_pipeline_halts_when_manual_review_required_and_not_authorized():
    svc = _make_gate_service()
    app = _FakeApplication(
        status="filled",
        manual_review_required=True,
        is_authorized_to_submit=False,
    )
    assert svc.can_advance_past_filled(app) is False


def test_pipeline_advances_when_manually_authorized():
    svc = _make_gate_service()
    app = _FakeApplication(
        status="filled",
        manual_review_required=True,
        is_authorized_to_submit=True,
    )
    assert svc.can_advance_past_filled(app) is True


def test_pipeline_advances_when_auto_submit_enabled():
    svc = _make_gate_service()
    app = _FakeApplication(
        status="filled",
        manual_review_required=False,
        is_authorized_to_submit=False,
    )
    assert svc.can_advance_past_filled(app) is True


def test_pipeline_returns_false_when_not_in_filled_state():
    svc = _make_gate_service()
    app = _FakeApplication(
        status="saved",
        manual_review_required=False,
        is_authorized_to_submit=True,
    )
    assert svc.can_advance_past_filled(app) is False


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------

def test_authorize_sets_flag(client, db_session, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)

    create_resp = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"job_id": job_id},
    )
    assert create_resp.status_code == 200
    app_id = create_resp.json()["id"]

    # Before authorize: flag should be False
    assert create_resp.json()["is_authorized_to_submit"] is False

    auth_resp = client.post(
        f"/applications/{app_id}/authorize",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert auth_resp.status_code == 200
    data = auth_resp.json()
    assert data["is_authorized_to_submit"] is True
    assert data["id"] == app_id


def test_authorize_returns_403_for_different_user(client, db_session, sample_user_payload):
    # Owner creates the application.
    owner_token = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)

    create_resp = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"job_id": job_id},
    )
    assert create_resp.status_code == 200
    app_id = create_resp.json()["id"]

    # A second user tries to authorize the first user's application.
    other_payload = _make_user_payload()
    other_token = _register_and_login(client, other_payload)

    auth_resp = client.post(
        f"/applications/{app_id}/authorize",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert auth_resp.status_code == 403


def test_authorize_returns_404_for_nonexistent_application(client, db_session, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)
    fake_id = str(uuid.uuid4())

    resp = client.post(
        f"/applications/{fake_id}/authorize",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


def test_new_application_defaults_manual_review_required_to_true(client, db_session, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)

    resp = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"job_id": job_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["manual_review_required"] is True
    assert data["is_authorized_to_submit"] is False
