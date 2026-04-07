"""
Profile API tests.

Verifies candidate profile creation and retrieval endpoints.
"""


def test_create_profile(client, sample_user_payload):
    user_response = client.post("/auth/register", json=sample_user_payload)
    user_id = user_response.json()["id"]

    payload = {
        "user_id": user_id,
        "location": "New York, NY",
        "skills": ["Python", "FastAPI"],
        "current_title": "Software Engineer",
    }

    response = client.post("/profile", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == user_id
    assert data["location"] == "New York, NY"
    assert data["skills"] == ["Python", "FastAPI"]
    assert data["current_title"] == "Software Engineer"


def test_get_profile(client, sample_user_payload):
    user_response = client.post("/auth/register", json=sample_user_payload)
    user_id = user_response.json()["id"]

    create_response = client.post(
        "/profile",
        json={
            "user_id": user_id,
            "location": "Remote",
            "skills": ["React"],
        },
    )
    assert create_response.status_code == 200

    response = client.get(f"/profile/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert data["location"] == "Remote"
    assert data["skills"] == ["React"]


def test_duplicate_profile_returns_400(client, sample_user_payload):
    user_response = client.post("/auth/register", json=sample_user_payload)
    user_id = user_response.json()["id"]

    payload = {
        "user_id": user_id,
        "location": "Remote",
        "skills": ["Python"],
    }

    first_response = client.post("/profile", json=payload)
    assert first_response.status_code == 200

    second_response = client.post("/profile", json=payload)
    assert second_response.status_code == 400
    assert "already has a candidate profile" in second_response.json()["detail"]