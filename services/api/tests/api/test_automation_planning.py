"""
Automation planning API tests.

Verifies adapter-aware fill planning from inspected fields.
"""

from src.domain.profile.repository import CandidateProfileRepository
from src.domain.profile.schemas import CandidateProfileCreate
import uuid


def _register_and_login(client, sample_user_payload):
    register_response = client.post("/auth/register", json=sample_user_payload)
    assert register_response.status_code == 200
    user_id = register_response.json()["id"]

    login_response = client.post(
        "/auth/login",
        data={
            "username": sample_user_payload["email"],
            "password": sample_user_payload["password"],
        },
    )
    assert login_response.status_code == 200

    return user_id, login_response.json()["access_token"]


def _create_profile(db_session, user_id):
    repository = CandidateProfileRepository(db_session)

    repository.upsert_by_user_id(
        user_id,
        CandidateProfileCreate(
            phone="(973) 666-7154",
            linkedin_url="https://linkedin.com/in/example",
            github_url="https://github.com/example",
            city="New York",
            state="NY",
            skills=["Python", "React"],
        ),
    )


def test_build_automation_fill_plan(client, db_session, sample_user_payload):
    user_id, token = _register_and_login(client, sample_user_payload)
    _create_profile(db_session, uuid.UUID(user_id))

    client.post(
        "/application-answers",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_key": "why_company_and_role",
            "category": "motivation",
            "question_text": "What about the company and this role excites you most?",
            "answer_text": "I’m excited by the product impact and the chance to work on meaningful engineering problems.",
        },
    )

    response = client.post(
        "/automation-planning",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "application_url": "https://job-boards.greenhouse.io/greenhouse/jobs/7705020?gh_jid=7705020",
            "inspected_fields": [
                {
                    "field_type": "input",
                    "label": "First Name",
                    "name": None,
                    "placeholder": None,
                    "required": True,
                },
                {
                    "field_type": "input",
                    "label": "Email",
                    "name": None,
                    "placeholder": None,
                    "required": True,
                },
                {
                    "field_type": "input",
                    "label": "Phone",
                    "name": None,
                    "placeholder": None,
                    "required": False,
                },
                {
                    "field_type": "textarea",
                    "label": "What about the company and this role excites you most?",
                    "name": None,
                    "placeholder": None,
                    "required": True,
                },
                {
                    "field_type": "button",
                    "label": "Submit application",
                    "name": None,
                    "placeholder": None,
                    "required": False,
                },
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["application_url"] is not None
    assert len(data["fields"]) == 5
    assert any(item["classified_role"] == "first_name" for item in data["fields"])
    assert any(item["classified_role"] == "email" for item in data["fields"])
    assert any(item["classified_role"] == "phone" for item in data["fields"])
    assert any(item["classified_role"] == "open_ended_question" for item in data["fields"])
    assert any(item["classified_role"] == "submit_action" for item in data["fields"])


def test_automation_planning_requires_auth(client):
    response = client.post(
        "/automation-planning",
        json={
            "application_url": "https://example.com/apply",
            "inspected_fields": [],
        },
    )
    assert response.status_code == 401