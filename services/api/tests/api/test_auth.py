"""
Auth API tests.

Verifies user registration, login, and authenticated session endpoints.
"""


def test_register_user(client, sample_user_payload):
    response = client.post("/auth/register", json=sample_user_payload)

    assert response.status_code == 200
    data = response.json()

    assert data["email"] == sample_user_payload["email"]
    assert data["first_name"] == sample_user_payload["first_name"]
    assert data["last_name"] == sample_user_payload["last_name"]
    assert "id" in data


def test_register_duplicate_user_returns_400(client, sample_user_payload):
    first_response = client.post("/auth/register", json=sample_user_payload)
    assert first_response.status_code == 200

    second_response = client.post("/auth/register", json=sample_user_payload)
    assert second_response.status_code == 400
    assert "already exists" in second_response.json()["detail"]


def test_login_user_returns_token(client, sample_user_payload):
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
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_user_with_bad_password_returns_401(client, sample_user_payload):
    register_response = client.post("/auth/register", json=sample_user_payload)
    assert register_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        data={
            "username": sample_user_payload["email"],
            "password": "wrong-password",
        },
    )

    assert login_response.status_code == 401


def test_get_current_session(client, sample_user_payload):
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

    session_response = client.get(
        "/auth/session",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert session_response.status_code == 200
    data = session_response.json()
    assert data["email"] == sample_user_payload["email"]


def test_get_current_session_requires_auth(client):
    response = client.get("/auth/session")
    assert response.status_code == 401