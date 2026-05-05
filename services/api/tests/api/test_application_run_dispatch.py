"""API tests for asynchronous application pipeline dispatch endpoint."""

from types import SimpleNamespace

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
        source_job_id="dispatch-gh-123",
        title="Platform Engineer",
        company_name="DispatchCo",
        location="Remote",
        workplace_type="remote",
        description="Dispatch pipeline test role",
        apply_url="https://job-boards.greenhouse.io/dispatchco/jobs/dispatch-gh-123",
        salary_min=140000,
        salary_max=180000,
        currency="USD",
        is_active=True,
    )
    return str(job.id)


def test_run_endpoint_dispatches_celery_task_and_returns_task_id(client, db_session, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)
    job_id = _create_fake_job(db_session)

    create_response = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"job_id": job_id},
    )
    assert create_response.status_code == 200
    application_id = create_response.json()["id"]

    from src.routes import applications as applications_routes

    original_send_task = applications_routes.celery_dispatch.send_task
    calls: list[tuple[str, dict]] = []

    def _fake_send_task(name, kwargs=None, **_):
        calls.append((name, kwargs or {}))
        return SimpleNamespace(id="task-123")

    applications_routes.celery_dispatch.send_task = _fake_send_task
    try:
        run_response = client.post(
            f"/applications/{application_id}/run",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        applications_routes.celery_dispatch.send_task = original_send_task

    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["application_id"] == application_id
    assert payload["task_id"] == "task-123"
    assert payload["status"] == "queued"

    assert len(calls) == 1
    task_name, kwargs = calls[0]
    assert task_name == "run_application_pipeline_async"
    assert kwargs["application_id"] == application_id
