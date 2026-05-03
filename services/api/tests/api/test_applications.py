"""
Applications API tests.

Verifies authenticated creation and listing of application records.
"""

from src.domain.auth.repository import UserRepository
from src.domain.jobs.repository import JobRepository
from src.domain.resume.repository import ResumeRepository


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
    token = login_response.json()["access_token"]
    return token


def _create_fake_job(db_session):
    repository = JobRepository(db_session)

    job = repository.create(
        source="greenhouse",
        source_job_id="test-gh-123",
        title="Senior Full Stack Engineer",
        company_name="Stripe",
        location="Remote",
        workplace_type="remote",
        description="Build internal and external platform features.",
        apply_url="https://boards.greenhouse.io/stripe/jobs/test-gh-123",
        salary_min=150000,
        salary_max=190000,
        currency="USD",
        is_active=True,
    )

    return str(job.id)


def _get_user_id(db_session, email: str):
    user = UserRepository(db_session).get_by_email(email)
    return user.id


def _create_resume(db_session, user_id, file_name: str, file_path: str):
    return ResumeRepository(db_session).create(
        user_id=user_id,
        file_name=file_name,
        file_path=file_path,
        mime_type="application/pdf",
        extracted_text="Sample",
        parsed_json={"status": "ok"},
    )


def test_create_and_list_applications(client, db_session, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)

    create_response = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "job_id": job_id,
            "notes": "Strong fit for backend platform work.",
        },
    )

    assert create_response.status_code == 200
    data = create_response.json()
    assert data["job_id"] == job_id
    assert data["notes"] == "Strong fit for backend platform work."

    list_response = client.get(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200

    applications = list_response.json()
    assert len(applications) == 1
    assert applications[0]["job_id"] == job_id


def test_create_application_with_explicit_resume_id(client, db_session, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)
    user_id = _get_user_id(db_session, sample_user_payload["email"])

    first_resume = _create_resume(
        db_session,
        user_id=user_id,
        file_name="older.pdf",
        file_path="s3://bucket/older.pdf",
    )
    second_resume = _create_resume(
        db_session,
        user_id=user_id,
        file_name="newer.pdf",
        file_path="s3://bucket/newer.pdf",
    )

    create_response = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "job_id": job_id,
            "resume_id": str(first_resume.id),
        },
    )

    assert create_response.status_code == 200
    data = create_response.json()
    assert data["resume_id"] == str(first_resume.id)
    assert data["resume_id"] != str(second_resume.id)


def test_create_application_defaults_to_most_recent_resume(client, db_session, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)
    user_id = _get_user_id(db_session, sample_user_payload["email"])

    older_resume = _create_resume(
        db_session,
        user_id=user_id,
        file_name="older.pdf",
        file_path="s3://bucket/older.pdf",
    )
    newest_resume = _create_resume(
        db_session,
        user_id=user_id,
        file_name="newest.pdf",
        file_path="s3://bucket/newest.pdf",
    )

    create_response = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "job_id": job_id,
        },
    )

    assert create_response.status_code == 200
    data = create_response.json()
    assert data["resume_id"] == str(newest_resume.id)
    assert data["resume_id"] != str(older_resume.id)


def test_get_application_includes_resume_id(client, db_session, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)
    user_id = _get_user_id(db_session, sample_user_payload["email"])
    resume = _create_resume(
        db_session,
        user_id=user_id,
        file_name="target.pdf",
        file_path="s3://bucket/target.pdf",
    )

    create_response = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"job_id": job_id, "resume_id": str(resume.id)},
    )
    assert create_response.status_code == 200

    application_id = create_response.json()["id"]
    get_response = client.get(
        f"/applications/{application_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == application_id
    assert data["resume_id"] == str(resume.id)


def test_create_duplicate_application_returns_400(client, db_session, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)

    first_response = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"job_id": job_id},
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"job_id": job_id},
    )
    assert second_response.status_code == 400
    assert "already created an application" in second_response.json()["detail"]


def test_create_application_for_missing_job_returns_400(client, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)

    create_response = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "job_id": "11111111-1111-1111-1111-111111111111",
        },
    )

    assert create_response.status_code == 400
    assert "Job not found" in create_response.json()["detail"]


def test_applications_requires_auth(client):
    response = client.get("/applications")
    assert response.status_code == 401