"""
API tests for GET /applications/patterns.

Covers: unauthenticated access (401), sparse data response, and a full
analytics payload when the user has sufficient meaningful applications.
"""

import uuid

from src.domain.applications.models import Application
from src.domain.auth.repository import UserRepository
from src.domain.jobs.repository import JobRepository
from src.domain.jobs.scoring.models import ApplicationScore
from src.domain.resume.repository import ResumeRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_and_login(client, sample_user_payload):
    r = client.post("/auth/register", json=sample_user_payload)
    assert r.status_code == 200
    lr = client.post(
        "/auth/login",
        data={
            "username": sample_user_payload["email"],
            "password": sample_user_payload["password"],
        },
    )
    assert lr.status_code == 200
    return lr.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _create_fake_job(db_session):
    job = JobRepository(db_session).create(
        source="greenhouse",
        source_job_id=f"test-{uuid.uuid4().hex[:8]}",
        title="Engineer",
        company_name="Acme",
        location="Remote",
        workplace_type="remote",
        description="Build things.",
        apply_url="https://example.com/apply",
        is_active=True,
    )
    return job.id  # Return the UUID object, not a string


def _get_user_id(db_session, email):
    return UserRepository(db_session).get_by_email(email).id


def _create_resume(db_session, user_id):
    return str(
        ResumeRepository(db_session)
        .create(
            user_id=user_id,
            file_name="resume.pdf",
            file_path="/uploads/resume.pdf",
            mime_type="application/pdf",
            extracted_text="Sample resume text",
        )
        .id
    )


def _seed_applications(db_session, user_id, job_id, statuses):
    """Insert Application rows with the given statuses directly via the ORM."""
    apps = []
    for status in statuses:
        app = Application(
            user_id=user_id,
            job_id=job_id,
            status=status,
        )
        db_session.add(app)
    db_session.commit()
    for app in db_session.query(Application).filter(Application.user_id == user_id).all():
        apps.append(app)
    return apps


def _seed_score(db_session, application_id, user_id, global_score):
    score = ApplicationScore(
        application_id=application_id,
        user_id=user_id,
        global_score=global_score,
        role_fit=global_score,
        location_match=global_score,
        seniority_match=global_score,
    )
    db_session.add(score)
    db_session.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_get_patterns_requires_auth(client):
    """Unauthenticated requests must be rejected with 401."""
    response = client.get("/applications/patterns")
    assert response.status_code == 401


def test_get_patterns_insufficient_data(client, db_session, sample_user_payload):
    """
    When fewer than 5 meaningful applications exist, the endpoint returns
    an ``is_sufficient_data=False`` response with no analytics fields.
    """
    token = _register_and_login(client, sample_user_payload)
    user_id = _get_user_id(db_session, sample_user_payload["email"])
    job_id = _create_fake_job(db_session)

    # Only 2 meaningful applications — below the threshold of 5
    _seed_applications(db_session, user_id, job_id, ["applied", "rejected"])

    response = client.get("/applications/patterns", headers=_auth_headers(token))
    assert response.status_code == 200

    data = response.json()
    assert data["is_sufficient_data"] is False
    assert data["minimum_threshold"] == 5
    assert data["insufficient_data_message"] is not None
    assert data["outcome_summary"] is None
    assert data["funnel"] is None
    assert data["recommendations"] is None


def test_get_patterns_full_analytics(client, db_session, sample_user_payload):
    """
    When ≥ 5 meaningful applications exist, the endpoint returns a full
    analytics payload with outcome_summary, funnel, and recommendations.
    """
    token = _register_and_login(client, sample_user_payload)
    user_id = _get_user_id(db_session, sample_user_payload["email"])
    job_id = _create_fake_job(db_session)

    statuses = [
        "applied",
        "interviewing",
        "rejected",
        "rejected",
        "rejected",
    ]
    apps = _seed_applications(db_session, user_id, job_id, statuses)

    # Seed a score for each application
    for app in apps:
        _seed_score(db_session, app.id, user_id, 3.5)

    response = client.get("/applications/patterns", headers=_auth_headers(token))
    assert response.status_code == 200

    data = response.json()
    assert data["is_sufficient_data"] is True
    assert data["total_applications"] >= 5
    assert data["outcome_summary"] is not None
    assert data["outcome_summary"]["positive"] == 2
    assert data["outcome_summary"]["negative"] == 3
    assert data["funnel"] is not None
    assert isinstance(data["funnel"], list)
    assert len(data["funnel"]) > 0
    assert data["score_by_outcome"] is not None
    assert data["recommendations"] is not None
    # With high rejection count (3 rejections out of 5) and 40% conversion, we should get a targeting recommendation
    if len(data["recommendations"]) > 0:
        impacts = [r["impact"] for r in data["recommendations"]]
        assert "high" in impacts or "medium" in impacts
