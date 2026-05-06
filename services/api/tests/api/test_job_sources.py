"""Job sources API tests."""

from src.domain.jobs.models import JobSource


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


def test_list_job_sources_returns_only_active_entries(client, sample_user_payload, db_session):
    token = _register_and_login(client, sample_user_payload)

    db_session.add(
        JobSource(
            source="greenhouse",
            company_key="stripe",
            board_token="stripe",
            display_name="Stripe",
            is_active=True,
        )
    )
    db_session.add(
        JobSource(
            source="lever",
            company_key="legacy",
            board_token="legacy",
            display_name="Legacy",
            is_active=False,
        )
    )
    db_session.commit()

    response = client.get("/jobs/sources", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["source"] == "greenhouse"
    assert data[0]["company_key"] == "stripe"
