"""
Auth API tests.

Verifies user registration, login, and authenticated session endpoints.
"""

from datetime import UTC, datetime, timedelta
import uuid

from jose import jwt

from src.core.config import settings
from src.integrations.auth.jwt import ALGORITHM


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


def test_register_weak_password_returns_422(client, sample_user_payload):
    weak_payload = {
        **sample_user_payload,
        "password": "password",
    }

    response = client.post("/auth/register", json=weak_payload)
    assert response.status_code == 422
    assert "non-letter" in response.text


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
    assert "refresh_token" in data
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


def test_expired_token_returns_401(client, sample_user_payload):
    register_response = client.post("/auth/register", json=sample_user_payload)
    assert register_response.status_code == 200
    user_id = register_response.json()["id"]

    expired_token = jwt.encode(
        {
            "sub": user_id,
            "jti": str(uuid.uuid4()),
            "type": "access",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.secret_key,
        algorithm=ALGORITHM,
    )

    session_response = client.get(
        "/auth/session",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert session_response.status_code == 401


def test_revoked_token_returns_401(client, sample_user_payload):
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
    access_token = login_response.json()["access_token"]

    logout_response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_response.status_code == 200

    session_response = client.get(
        "/auth/session",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert session_response.status_code == 401


def test_refresh_returns_new_access_token(client, sample_user_payload):
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
    refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_rotates_refresh_token(client, sample_user_payload):
    """Refresh returns a new refresh token and the old one is revoked."""
    client.post("/auth/register", json=sample_user_payload)
    login_response = client.post(
        "/auth/login",
        data={
            "username": sample_user_payload["email"],
            "password": sample_user_payload["password"],
        },
    )
    original_refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )
    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert "refresh_token" in data
    assert data["refresh_token"] != original_refresh_token

    # The old refresh token must now be rejected.
    second_refresh = client.post(
        "/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )
    assert second_refresh.status_code == 401


def test_logout_revokes_both_tokens(client, sample_user_payload):
    """Logout revokes the access token and, when supplied, the refresh token."""
    client.post("/auth/register", json=sample_user_payload)
    login_response = client.post(
        "/auth/login",
        data={
            "username": sample_user_payload["email"],
            "password": sample_user_payload["password"],
        },
    )
    tokens = login_response.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    logout_response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token},
    )
    assert logout_response.status_code == 200

    # Access token should be rejected.
    session_response = client.get(
        "/auth/session",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert session_response.status_code == 401

    # Refresh token should also be rejected.
    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 401


def test_logout_without_refresh_token_still_revokes_access_token(client, sample_user_payload):
    """Logout works when no refresh_token is provided in the body."""
    client.post("/auth/register", json=sample_user_payload)
    login_response = client.post(
        "/auth/login",
        data={
            "username": sample_user_payload["email"],
            "password": sample_user_payload["password"],
        },
    )
    access_token = login_response.json()["access_token"]

    logout_response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_response.status_code == 200

    session_response = client.get(
        "/auth/session",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert session_response.status_code == 401


def test_login_rate_limit_returns_429(client, sample_user_payload):
    register_response = client.post("/auth/register", json=sample_user_payload)
    assert register_response.status_code == 200

    status_codes = []
    for _ in range(11):
        response = client.post(
            "/auth/login",
            data={
                "username": sample_user_payload["email"],
                "password": "wrong-password",
            },
        )
        status_codes.append(response.status_code)

    assert 429 in status_codes