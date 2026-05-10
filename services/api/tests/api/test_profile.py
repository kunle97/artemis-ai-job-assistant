"""
Profile API tests.

Verifies authenticated candidate profile creation and retrieval endpoints.
"""


def test_create_profile(client, sample_user_payload):
    register_response = client.post("/auth/register", json=sample_user_payload)
    assert register_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        data={
            "username": sample_user_payload["email"],
            "password": sample_user_payload["password"],
        },
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "city": "New York",
            "state": "NY",
            "skills": ["Python", "FastAPI"],
            "work_arrangement": ["remote", "hybrid"],
            "willing_to_relocate": True,
            "relocation_destinations": ["Austin", "Seattle"],
            "desired_start_date": "2 weeks",
            "min_salary": "180000",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["location"] == "New York, NY"
    assert data["skills"] == ["Python", "FastAPI"]
    assert data["work_arrangement"] == ["remote", "hybrid"]
    assert data["willing_to_relocate"] is True
    assert data["relocation_destinations"] == ["Austin", "Seattle"]
    assert data["desired_start_date"] == "2 weeks"
    assert data["min_salary"] == "180000"


def test_get_profile(client, sample_user_payload):
    register_response = client.post("/auth/register", json=sample_user_payload)
    assert register_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        data={
            "username": sample_user_payload["email"],
            "password": sample_user_payload["password"],
        },
    )
    token = login_response.json()["access_token"]

    create_response = client.post(
        "/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "work_arrangement": ["remote"],
            "skills": ["React"],
        },
    )
    assert create_response.status_code == 200

    response = client.get(
        "/profile",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["work_arrangement"] == ["remote"]
    assert data["skills"] == ["React"]


def test_duplicate_profile_returns_400(client, sample_user_payload):
    register_response = client.post("/auth/register", json=sample_user_payload)
    assert register_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        data={
            "username": sample_user_payload["email"],
            "password": sample_user_payload["password"],
        },
    )
    token = login_response.json()["access_token"]

    payload = {
        "work_arrangement": ["remote"],
        "skills": ["Python"],
    }

    first_response = client.post(
        "/profile",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/profile",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert second_response.status_code == 400
    assert "already has a candidate profile" in second_response.json()["detail"]


def test_profile_requires_auth(client):
    response = client.get("/profile")
    assert response.status_code == 401