"""Jobs source discovery API tests."""


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


class _FakeResponse:
    def __init__(self, url: str, status_code: int = 200):
        self.url = url
        self.status_code = status_code


def test_crawl_job_sources_returns_discovery_candidates(client, sample_user_payload, monkeypatch):
    token = _register_and_login(client, sample_user_payload)

    def _fake_get(url: str, timeout: float, allow_redirects: bool):
        return _FakeResponse("https://jobs.ashbyhq.com/superco")

    monkeypatch.setattr("src.domain.jobs.discovery_service.requests.get", _fake_get)

    response = client.post(
        "/jobs/discovery/crawl",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "hosted_urls": ["https://job-boards.greenhouse.io/stripe"],
            "career_urls": ["https://superco.com/careers"],
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["total_candidates"] == 2
    assert payload["provider_counts"] == {"greenhouse": 1, "ashby": 1}
    assert len(payload["candidates"]) == 2


def test_promote_job_source_candidates_from_discovery_run(client, sample_user_payload, monkeypatch):
    token = _register_and_login(client, sample_user_payload)

    def _fake_get(url: str, timeout: float, allow_redirects: bool):
        return _FakeResponse("https://jobs.ashbyhq.com/superco")

    monkeypatch.setattr("src.domain.jobs.discovery_service.requests.get", _fake_get)

    crawl_response = client.post(
        "/jobs/discovery/crawl",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "hosted_urls": ["https://job-boards.greenhouse.io/stripe"],
            "career_urls": ["https://superco.com/careers"],
        },
    )
    assert crawl_response.status_code == 200
    crawl_payload = crawl_response.json()

    promote_response = client.post(
        "/jobs/discovery/promote",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "run_id": crawl_payload["run_id"],
            "is_active": True,
        },
    )
    assert promote_response.status_code == 200
    promote_payload = promote_response.json()

    assert promote_payload["selected_candidates"] == 2
    assert promote_payload["promoted_count"] == 2
    assert promote_payload["skipped_count"] == 0
    assert {item["source"] for item in promote_payload["promoted_sources"]} == {"greenhouse", "ashby"}

    list_sources_response = client.get(
        "/jobs/sources",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_sources_response.status_code == 200
    list_payload = list_sources_response.json()
    assert len(list_payload) == 2
    assert {item["company_key"] for item in list_payload} == {"stripe", "superco"}


def test_promote_job_source_candidates_supports_candidate_id_filter(client, sample_user_payload, monkeypatch):
    token = _register_and_login(client, sample_user_payload)

    def _fake_get(url: str, timeout: float, allow_redirects: bool):
        return _FakeResponse("https://jobs.ashbyhq.com/superco")

    monkeypatch.setattr("src.domain.jobs.discovery_service.requests.get", _fake_get)

    crawl_response = client.post(
        "/jobs/discovery/crawl",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "hosted_urls": ["https://job-boards.greenhouse.io/stripe"],
            "career_urls": ["https://superco.com/careers"],
        },
    )
    assert crawl_response.status_code == 200
    crawl_payload = crawl_response.json()
    chosen_candidate_id = crawl_payload["candidates"][0]["id"]

    promote_response = client.post(
        "/jobs/discovery/promote",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "run_id": crawl_payload["run_id"],
            "candidate_ids": [chosen_candidate_id],
            "is_active": True,
        },
    )
    assert promote_response.status_code == 200
    promote_payload = promote_response.json()

    assert promote_payload["selected_candidates"] == 1
    assert promote_payload["promoted_count"] == 1
    assert len(promote_payload["promoted_sources"]) == 1


def test_promote_job_source_candidates_skips_unsafe_token(client, sample_user_payload):
    token = _register_and_login(client, sample_user_payload)

    crawl_response = client.post(
        "/jobs/discovery/crawl",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "hosted_urls": ["https://job-boards.greenhouse.io/jobs"],
            "career_urls": [],
        },
    )
    assert crawl_response.status_code == 200
    crawl_payload = crawl_response.json()

    promote_response = client.post(
        "/jobs/discovery/promote",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "run_id": crawl_payload["run_id"],
            "is_active": True,
        },
    )
    assert promote_response.status_code == 200
    promote_payload = promote_response.json()

    assert promote_payload["selected_candidates"] == 1
    assert promote_payload["promoted_count"] == 0
    assert promote_payload["skipped_count"] == 1
