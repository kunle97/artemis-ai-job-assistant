"""
Application planning API tests.

Verifies pre-automation planning behavior for applications.
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
        source_job_id="planning-gh-123",
        title="Backend Engineer",
        company_name="Stripe",
        location="Remote",
        workplace_type="remote",
        description="Build backend systems.",
        apply_url="https://boards.greenhouse.io/stripe/jobs/planning-gh-123",
        salary_min=150000,
        salary_max=190000,
        currency="USD",
        is_active=True,
    )

    return str(job.id)


def test_application_plan_marks_unresolved_questions_for_review(
    client,
    db_session,
    sample_user_payload,
):
    token = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)

    application_response = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"job_id": job_id},
    )
    assert application_response.status_code == 200
    application_id = application_response.json()["id"]

    planning_response = client.post(
        "/application-planning",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "application_id": application_id,
            "questions": [
                "What are the three most important factors you're looking for in your next role?",
                "What is your favorite database sharding strategy?",
            ],
        },
    )

    assert planning_response.status_code == 200
    data = planning_response.json()

    assert data["application_id"] == application_id
    assert data["readiness_status"] == "needs_review"
    assert len(data["items"]) == 2
    assert data["items"][1]["needs_review"] is True


def test_application_plan_uses_saved_answer(
    client,
    db_session,
    sample_user_payload,
):
    token = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)

    save_answer_response = client.post(
        "/application-answers",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_key": "next_role_priorities",
            "category": "preferences",
            "question_text": "What are the three most important factors you're looking for in your next role?",
            "answer_text": "Strong engineering culture, meaningful product impact, and growth opportunities.",
        },
    )
    assert save_answer_response.status_code == 200

    application_response = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"job_id": job_id},
    )
    assert application_response.status_code == 200
    application_id = application_response.json()["id"]

    planning_response = client.post(
        "/application-planning",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "application_id": application_id,
            "questions": [
                "What are the three most important factors you’re looking for in your next role?*",
            ],
        },
    )

    assert planning_response.status_code == 200
    data = planning_response.json()

    assert data["items"][0]["matched_question_key"] == "next_role_priorities"
    assert data["items"][0]["resolved_answer"] is not None
    assert data["items"][0]["source"] == "saved_answer"
    assert data["items"][0]["needs_review"] is False


def test_application_planning_requires_auth(client):
    response = client.post(
        "/application-planning",
        json={
            "application_id": "11111111-1111-1111-1111-111111111111",
            "questions": [],
        },
    )
    assert response.status_code == 401