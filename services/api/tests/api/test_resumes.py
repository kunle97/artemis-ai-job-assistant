"""
Resume API tests.

Verifies authenticated resume upload, persistence, and automatic profile sync behavior.
"""

from io import BytesIO


def test_upload_resume_and_list_resumes(client, sample_user_payload):
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

    resume_text = b"""
Jane Doe
Full Stack Software Engineer | (555) 123-4567 | jane@example.com | https://github.com/janedoe

SKILLS
Python, React, Django, Docker

EXPERIENCE
Example Corp
Senior Software Engineer
Jan 2020 - Current
Built backend services with FastAPI and PostgreSQL.
"""

    response = client.post(
        "/resumes/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("resume.txt", BytesIO(resume_text), "text/plain")},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["file_name"] == "resume.txt"
    assert data["mime_type"] == "text/plain"
    assert data["extracted_text"] is not None
    assert data["parsed_json"]["status"] == "text_extracted"

    list_response = client.get(
        "/resumes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200

    resumes = list_response.json()
    assert len(resumes) == 1


def test_upload_resume_syncs_profile(client, sample_user_payload):
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

    resume_text = b"""
Jane Doe
Full Stack Software Engineer | (555) 123-4567 | jane@example.com | https://github.com/janedoe

SKILLS
Python, React, Django, Docker

EXPERIENCE
Example Corp
Senior Software Engineer
Jan 2020 - Current
Built backend services with FastAPI and PostgreSQL.
"""

    upload_response = client.post(
        "/resumes/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("resume.txt", BytesIO(resume_text), "text/plain")},
    )

    assert upload_response.status_code == 200

    upload_data = upload_response.json()
    assert upload_data["parsed_json"]["normalized_data"]["years_experience"] is not None

    profile_response = client.get(
        "/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert profile_response.status_code == 200

    profile = profile_response.json()
    assert "python" in profile["skills"]
    assert profile["years_experience"] is not None
    assert profile["current_title"] is not None


def test_upload_resume_rejects_unsupported_type(client, sample_user_payload):
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
        "/resumes/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("resume.exe", BytesIO(b"fake"), "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "Unsupported resume file type" in response.json()["detail"]


def test_resumes_requires_auth(client):
    response = client.get("/resumes")
    assert response.status_code == 401