"""
Application answer API tests.

Verifies authenticated save and list behavior for reusable application answers.
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


def test_save_and_list_application_answers(client, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)

    save_response = client.post(
        "/application-answers",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_key": "work_authorization_us",
            "category": "eligibility",
            "question_text": "Are you authorized to work in the United States?",
            "answer_text": "Yes",
        },
    )

    assert save_response.status_code == 200
    saved = save_response.json()
    assert saved["question_key"] == "work_authorization_us"
    assert saved["category"] == "eligibility"
    assert saved["answer_text"] == "Yes"

    list_response = client.get(
        "/application-answers",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert list_response.status_code == 200
    answers = list_response.json()
    assert len(answers) == 1
    assert answers[0]["question_key"] == "work_authorization_us"


def test_upsert_application_answer(client, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)

    first_response = client.post(
        "/application-answers",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_key": "linkedin_url",
            "category": "profile",
            "question_text": "LinkedIn URL",
            "answer_text": "https://linkedin.com/in/example",
        },
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/application-answers",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_key": "linkedin_url",
            "category": "profile",
            "question_text": "LinkedIn URL",
            "answer_text": "https://linkedin.com/in/updated-example",
        },
    )
    assert second_response.status_code == 200

    updated = second_response.json()
    assert updated["answer_text"] == "https://linkedin.com/in/updated-example"

    list_response = client.get(
        "/application-answers",
        headers={"Authorization": f"Bearer {token}"},
    )
    answers = list_response.json()
    assert len(answers) == 1


def test_application_answers_requires_auth(client):
    response = client.get("/application-answers")
    assert response.status_code == 401