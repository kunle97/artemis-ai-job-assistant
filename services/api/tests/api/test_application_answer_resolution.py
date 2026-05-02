"""
Application answer resolution API tests.

Verifies resolution from saved answers and unresolved fallback behavior.
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


def test_resolve_question_from_saved_answer(client, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)

    save_response = client.post(
        "/application-answers",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_key": "next_role_priorities",
            "category": "preferences",
            "question_text": "What are the three most important factors you’re looking for in your next role?",
            "answer_text": "Strong engineering culture, meaningful product impact, and growth opportunities.",
        },
    )
    assert save_response.status_code == 200

    resolve_response = client.post(
        "/application-answer-resolution",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_text": "What are the three most important factors you're looking for in your next role?*",
        },
    )

    assert resolve_response.status_code == 200
    data = resolve_response.json()
    assert data["resolved_answer"] is not None
    assert data["source"] in ("saved_answer_exact", "saved_answer_fuzzy")
    assert data["needs_review"] is False


def test_resolve_unknown_question_requires_review(client, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)

    resolve_response = client.post(
        "/application-answer-resolution",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_text": "What is your favorite way to design a database sharding strategy?",
        },
    )

    assert resolve_response.status_code == 200
    data = resolve_response.json()
    assert data["resolved_answer"] is None
    assert data["source"] == "unresolved"
    assert data["needs_review"] is True


def test_application_answer_resolution_requires_auth(client):
    response = client.post(
        "/application-answer-resolution",
        json={"question_text": "Why are you interested in this role?"},
    )
    assert response.status_code == 401