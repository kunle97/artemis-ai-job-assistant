"""
Job feed API tests.

Covers: POST /jobs/feed/scan and GET /jobs/feed endpoints.
"""

from uuid import UUID
from unittest.mock import patch

from src.domain.jobs.feed_service import JobFeedService
from src.domain.jobs.models import Job, JobFeedStatus, JobUserFeed


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

    matching_link = JobUserFeed(user_id=current_user_id(token, client), job_id=matching.id)
    non_matching_link = JobUserFeed(user_id=current_user_id(token, client), job_id=non_matching.id)
    db_session.add(matching_link)
    db_session.add(non_matching_link)
    db_session.commit()

    response = client.get("/jobs/feed", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "jobs" in data
    assert data["prevUrl"] is None
    job_titles = {j["title"] for j in data["jobs"]}
    assert "Backend Engineer" in job_titles
    assert "Product Manager" not in job_titles


def test_get_feed_returns_prev_url_for_later_pages(client, sample_user_payload, db_session):
    """GET /jobs/feed exposes prevUrl when the current page is not the first page."""
    token = _register_and_login(client, sample_user_payload)

    client.put(
        "/jobs/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={"enabled_sources": ["greenhouse"]},
    )

    user_id = current_user_id(token, client)
    jobs = []
    links = []
    for index in range(3):
        job = Job(
            source="greenhouse",
            source_job_id=f"job-{index}",
            title=f"Backend Engineer {index}",
            company_name="Co",
            apply_url=f"https://a.com/{index}",
            is_active=True,
        )
        db_session.add(job)
        jobs.append(job)

    db_session.commit()

    for job in jobs:
        links.append(JobUserFeed(user_id=user_id, job_id=job.id))

    db_session.add_all(links)
    db_session.commit()

    response = client.get(
        "/jobs/feed?skip=2&limit=1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["prevUrl"] == "http://testserver/jobs/feed?skip=1&limit=1"
    assert data["next_url"] is None


def test_get_feed_filters_by_preferred_location_and_nyc_alias(client, sample_user_payload, db_session):
    """GET /jobs/feed applies location preferences and treats NYC as New York."""
    token = _register_and_login(client, sample_user_payload)

    client.put(
        "/jobs/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={"locations": ["New York, NY"], "enabled_sources": ["greenhouse"]},
    )

    nyc_job = Job(
        source="greenhouse",
        source_job_id="nyc-1",
        title="Frontend Engineer",
        company_name="Co",
        apply_url="https://a.com/nyc",
        location="NYC-Privy",
        is_active=True,
    )
    other_job = Job(
        source="greenhouse",
        source_job_id="sf-1",
        title="Frontend Engineer",
        company_name="Co",
        apply_url="https://a.com/sf",
        location="San Francisco, California, United States",
        is_active=True,
    )
    db_session.add(nyc_job)
    db_session.add(other_job)
    db_session.commit()

    user_id = current_user_id(token, client)
    db_session.add(JobUserFeed(user_id=user_id, job_id=nyc_job.id))
    db_session.add(JobUserFeed(user_id=user_id, job_id=other_job.id))
    db_session.commit()

    response = client.get("/jobs/feed", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    job_locations = {job["location"] for job in data["jobs"]}
    assert "NYC-Privy" in job_locations
    assert "San Francisco, California, United States" not in job_locations


def current_user_id(token, client):
    payload = client.get("/jobs/preferences", headers={"Authorization": f"Bearer {token}"})
    assert payload.status_code == 200
    return UUID(payload.json()["user_id"])


def test_patch_job_feed_status_updates_status(client, sample_user_payload, db_session):
    """PATCH /jobs/feed/{job_id} updates the current user's per-job feed status."""
    token = _register_and_login(client, sample_user_payload)
    user_id = current_user_id(token, client)

    job = Job(
        source="greenhouse",
        source_job_id="job-1",
        title="Backend Engineer",
        company_name="Co",
        apply_url="https://a.com/1",
        is_active=True,
    )
    db_session.add(job)
    db_session.commit()

    link = JobUserFeed(user_id=user_id, job_id=job.id, status=JobFeedStatus.NEW)
    db_session.add(link)
    db_session.commit()

    response = client.patch(
        f"/jobs/feed/{job.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "saved"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "saved"

    db_session.refresh(link)
    assert link.status == JobFeedStatus.SAVED
