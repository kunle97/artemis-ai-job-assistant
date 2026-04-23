"""
Automation API tests.

Verifies auth behavior for automation endpoints.
"""


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


def test_automation_inspect_requires_auth(client):
    response = client.post(
        "/automation/inspect",
        json={"application_url": "https://example.com/apply"},
    )
    assert response.status_code == 401