"""Job preferences API tests."""


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


def test_get_job_preferences_creates_defaults_when_missing(client, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)

    response = client.get(
        "/jobs/preferences",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["target_titles"] == []
    assert data["positive_keywords"] == []
    assert data["negative_keywords"] == []
    assert data["locations"] == []
    assert data["remote_only"] is False
    assert data["salary_min"] is None
    assert data["enabled_sources"] == []


def test_put_job_preferences_creates_preferences_for_current_user(client, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)

    response = client.put(
        "/jobs/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "target_titles": ["Software Engineer", "Backend Engineer"],
            "positive_keywords": ["python", "fastapi"],
            "negative_keywords": ["php"],
            "locations": ["Remote", "New York, NY"],
            "remote_only": True,
            "salary_min": 150000,
            "enabled_sources": ["greenhouse", "lever"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["target_titles"] == ["Software Engineer", "Backend Engineer"]
    assert data["positive_keywords"] == ["python", "fastapi"]
    assert data["negative_keywords"] == ["php"]
    assert data["locations"] == ["Remote", "New York, NY"]
    assert data["remote_only"] is True
    assert data["salary_min"] == 150000
    assert data["enabled_sources"] == ["greenhouse", "lever"]


def test_put_job_preferences_updates_existing_preferences(client, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)

    create_response = client.put(
        "/jobs/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "target_titles": ["Software Engineer"],
            "positive_keywords": ["python"],
            "negative_keywords": [],
            "locations": ["Remote"],
            "remote_only": False,
            "salary_min": 120000,
            "enabled_sources": ["greenhouse"],
        },
    )
    assert create_response.status_code == 200

    update_response = client.put(
        "/jobs/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "target_titles": ["Senior Backend Engineer"],
            "positive_keywords": ["python", "postgres"],
            "negative_keywords": ["wordpress"],
            "locations": ["Remote", "Boston, MA"],
            "remote_only": True,
            "salary_min": 170000,
            "enabled_sources": ["greenhouse", "ashby"],
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["target_titles"] == ["Senior Backend Engineer"]
    assert updated["positive_keywords"] == ["python", "postgres"]
    assert updated["negative_keywords"] == ["wordpress"]
    assert updated["locations"] == ["Remote", "Boston, MA"]
    assert updated["remote_only"] is True
    assert updated["salary_min"] == 170000
    assert updated["enabled_sources"] == ["greenhouse", "ashby"]

    get_response = client.get(
        "/jobs/preferences",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["target_titles"] == ["Senior Backend Engineer"]
    assert fetched["enabled_sources"] == ["greenhouse", "ashby"]