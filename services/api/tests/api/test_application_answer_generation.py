"""
Application answer generation API tests.

Verifies authenticated generation calls and resolver-backed reuse behavior.
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


def test_generate_answer_uses_saved_answer_when_available(client, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)

    save_response = client.post(
        "/application-answers",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_key": "js_react_proficiency",
            "category": "technical",
            "question_text": "Do you have proficiency in JavaScript and React? Please describe.",
            "answer_text": "Yes. I use JavaScript and React daily to build production web apps.",
        },
    )
    assert save_response.status_code == 200

    response = client.post(
        "/application-answer-generation",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_text": "Do you have proficiency in JavaScript and React? Please describe.",
            "page_title": "Frontend Engineer",
            "job_context": "React, TypeScript, Next.js",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer_text"] is not None
    assert data["source"] in ("saved_answer_exact", "saved_answer_fuzzy")
    assert data["needs_review"] is False


def test_application_answer_generation_requires_auth(client):
    response = client.post(
        "/application-answer-generation",
        json={"question_text": "Why are you interested in this role?"},
    )
    assert response.status_code == 401
