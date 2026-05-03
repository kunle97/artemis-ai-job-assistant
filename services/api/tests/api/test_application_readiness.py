"""
Application readiness API tests.

Verifies readiness evaluation for authenticated users.
"""

from src.domain.jobs.repository import JobRepository


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


def _create_fake_job(db_session):
    repository = JobRepository(db_session)

    job = repository.create(
        source="greenhouse",
        source_job_id="readiness-gh-123",
        title="Backend Engineer",
        company_name="Stripe",
        location="Remote",
        workplace_type="remote",
        description="Build backend systems.",
        apply_url="https://boards.greenhouse.io/stripe/jobs/readiness-gh-123",
        salary_min=150000,
        salary_max=190000,
        currency="USD",
        is_active=True,
    )

    return str(job.id)


def test_application_readiness_shows_missing_profile_and_resume(
    client,
    db_session,
    sample_user_payload,
):
    token = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)

    create_application_response = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"job_id": job_id},
    )
    assert create_application_response.status_code == 200
    application_id = create_application_response.json()["id"]

    readiness_response = client.get(
        f"/application-readiness/{application_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert readiness_response.status_code == 200
    data = readiness_response.json()
    assert data["is_ready"] is False
    assert "candidate_profile" in data["missing_items"]
    assert "resume" in data["missing_items"]


def test_application_readiness_requires_auth(client):
    response = client.get("/application-readiness")
    assert response.status_code == 401


def test_application_readiness_single_returns_404_for_unknown_id(client, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)

    response = client.get(
        "/application-readiness/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_application_readiness_single_returns_403_for_other_users_application(
    client,
    db_session,
    sample_user_payload,
):
    # User A creates an application
    token_a = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)

    app_response = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"job_id": job_id},
    )
    assert app_response.status_code == 200
    application_id = app_response.json()["id"]

    # User B registers separately
    import uuid
    other_payload = {
        "email": f"other-{uuid.uuid4().hex[:8]}@example.com",
        "password": "password123",
        "first_name": "Other",
        "last_name": "User",
    }
    token_b = _register_and_login(client, other_payload)

    # User B tries to access User A's application
    response = client.get(
        f"/application-readiness/{application_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 403