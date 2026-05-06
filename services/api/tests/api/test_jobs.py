from src.domain.jobs.models import JobSource


def test_search_jobs_with_multiple_companies(client, sample_user_payload, db_session):
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
            source="greenhouse",
            company_key="figma",
            board_token="figma",
            display_name="Figma",
            is_active=True,
        )
    )
    db_session.commit()

    search_response = client.post(
        "/jobs/search",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "source": "greenhouse",
            "company_names": ["stripe", "figma"],
            "query": "engineer",
        },
    )

    assert search_response.status_code == 200
    data = search_response.json()
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert isinstance(data["jobs"], list)