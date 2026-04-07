"""
Auth API tests.

Verifies user registration and retrieval endpoints.
"""


def test_register_user(client, sample_user_payload):
    response = client.post("/auth/register", json=sample_user_payload)

    assert response.status_code == 200
    data = response.json()

    assert data["email"] == sample_user_payload["email"]
    assert data["full_name"] == sample_user_payload["full_name"]
    assert "id" in data


def test_register_duplicate_user_returns_400(client, sample_user_payload):
    first_response = client.post("/auth/register", json=sample_user_payload)
    assert first_response.status_code == 200

    second_response = client.post("/auth/register", json=sample_user_payload)
    assert second_response.status_code == 400
    assert "already exists" in second_response.json()["detail"]


def test_get_user(client, sample_user_payload):
    create_response = client.post("/auth/register", json=sample_user_payload)
    user_id = create_response.json()["id"]

    response = client.get(f"/auth/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == sample_user_payload["email"]