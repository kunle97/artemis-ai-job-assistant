"""
Resume API tests.

Verifies resume upload, persistence, and automatic profile sync behavior.
"""

from io import BytesIO


def test_upload_resume_and_list_resumes(client, sample_user_payload):
    user_response = client.post("/auth/register", json=sample_user_payload)
    user_id = user_response.json()["id"]

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
        data={"user_id": user_id},
        files={"file": ("resume.txt", BytesIO(resume_text), "text/plain")},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == user_id
    assert data["file_name"] == "resume.txt"
    assert data["mime_type"] == "text/plain"
    assert data["extracted_text"] is not None
    assert data["parsed_json"]["status"] == "text_extracted"

    list_response = client.get(f"/resumes/{user_id}")
    assert list_response.status_code == 200

    resumes = list_response.json()
    assert len(resumes) == 1
    assert resumes[0]["user_id"] == user_id


def test_upload_resume_syncs_profile(client, sample_user_payload):
    user_response = client.post("/auth/register", json=sample_user_payload)
    user_id = user_response.json()["id"]

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
        data={"user_id": user_id},
        files={"file": ("resume.txt", BytesIO(resume_text), "text/plain")},
    )

    assert upload_response.status_code == 200
    
    upload_data = upload_response.json()
    assert upload_data["parsed_json"]["normalized_data"]["years_experience"] is not None

    profile_response = client.get(f"/profile/{user_id}")
    assert profile_response.status_code == 200

    profile = profile_response.json()
    assert profile["user_id"] == user_id
    assert "python" in profile["skills"]
    assert profile["years_experience"] is not None
    assert profile["current_title"] is not None


def test_upload_resume_rejects_unsupported_type(client, sample_user_payload):
    user_response = client.post("/auth/register", json=sample_user_payload)
    user_id = user_response.json()["id"]

    response = client.post(
        "/resumes/upload",
        data={"user_id": user_id},
        files={"file": ("resume.exe", BytesIO(b"fake"), "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "Unsupported resume file type" in response.json()["detail"]