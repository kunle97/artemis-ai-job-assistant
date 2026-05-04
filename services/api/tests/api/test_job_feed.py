"""
Job feed API tests.

Covers: POST /jobs/feed/scan and GET /jobs/feed endpoints.
"""

from unittest.mock import patch

from src.domain.jobs.feed_service import JobFeedService
from src.domain.jobs.models import Job


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


_FAKE_JOBS = [
    {
        "source": "greenhouse",
        "source_job_id": "fake-1",
        "title": "Backend Engineer",
        "company_name": "FakeCo",
        "apply_url": "https://boards.greenhouse.io/fakeco/jobs/fake-1",
        "location": "Remote",
        "workplace_type": "remote",
        "description": "Python engineer role",
        "salary_min": None,
        "salary_max": None,
        "currency": None,
        "is_active": True,
    },
    {
        "source": "greenhouse",
        "source_job_id": "fake-2",
        "title": "Senior Engineer",
        "company_name": "FakeCo",
        "apply_url": "https://boards.greenhouse.io/fakeco/jobs/fake-2",
        "location": "Remote",
        "workplace_type": "remote",
        "description": "Senior engineer role",
        "salary_min": None,
        "salary_max": None,
        "currency": None,
        "is_active": True,
    },
]


def test_feed_scan_returns_new_jobs(client, sample_user_payload):
    """POST /jobs/feed/scan returns newly ingested jobs."""
    token = _register_and_login(client, sample_user_payload)

    client.put(
        "/jobs/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={"enabled_sources": ["greenhouse"], "target_titles": ["engineer"]},
    )

    with patch.object(JobFeedService, "_fetch_board", return_value=_FAKE_JOBS):
        response = client.post(
            "/jobs/feed/scan",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["new_jobs_found"] == 2
    assert "jobs" not in data


def test_feed_scan_deduplicates_on_rescan(client, sample_user_payload):
    """Re-scanning the same boards does not create duplicate job records."""
    token = _register_and_login(client, sample_user_payload)

    client.put(
        "/jobs/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={"enabled_sources": ["greenhouse"], "target_titles": ["engineer"]},
    )

    with patch.object(JobFeedService, "_fetch_board", return_value=_FAKE_JOBS):
        first = client.post("/jobs/feed/scan", headers={"Authorization": f"Bearer {token}"})
        second = client.post("/jobs/feed/scan", headers={"Authorization": f"Bearer {token}"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["new_jobs_found"] == 2
    assert second.json()["new_jobs_found"] == 0


def test_get_feed_filters_by_user_preferences(client, sample_user_payload, db_session):
    """GET /jobs/feed only returns jobs matching the user's target_titles preference."""
    token = _register_and_login(client, sample_user_payload)

    client.put(
        "/jobs/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_titles": ["engineer"], "enabled_sources": ["greenhouse"]},
    )

    matching = Job(
        source="greenhouse",
        source_job_id="match-1",
        title="Backend Engineer",
        company_name="Co",
        apply_url="https://a.com/1",
        is_active=True,
    )
    non_matching = Job(
        source="greenhouse",
        source_job_id="nomatch-1",
        title="Product Manager",
        company_name="Co",
        apply_url="https://a.com/2",
        is_active=True,
    )
    db_session.add(matching)
    db_session.add(non_matching)
    db_session.commit()

    response = client.get("/jobs/feed", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "jobs" in data
    job_titles = {j["title"] for j in data["jobs"]}
    assert "Backend Engineer" in job_titles
    assert "Product Manager" not in job_titles
