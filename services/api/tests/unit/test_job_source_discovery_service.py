"""Unit tests for ATS source discovery service."""

from src.domain.jobs.discovery_service import JobSourceDiscoveryService
from src.domain.jobs.repository import JobSourceDiscoveryRepository


class _FakeResponse:
    def __init__(self, url: str, status_code: int = 200):
        self.url = url
        self.status_code = status_code


def test_discover_extracts_hosted_urls_and_redirects(db_session, monkeypatch):
    service = JobSourceDiscoveryService(repository=JobSourceDiscoveryRepository(db_session))

    def _fake_get(url: str, timeout: float, allow_redirects: bool):
        assert allow_redirects is True
        assert timeout == 10.0
        return _FakeResponse("https://jobs.lever.co/acme")

    monkeypatch.setattr("src.domain.jobs.discovery_service.requests.get", _fake_get)

    run_id, candidates, provider_counts = service.discover(
        hosted_urls=["https://job-boards.greenhouse.io/stripe"],
        career_urls=["https://acme.com/careers"],
    )

    assert run_id is not None
    assert len(candidates) == 2
    assert provider_counts == {"greenhouse": 1, "lever": 1}

    greenhouse = [c for c in candidates if c.detected_provider == "greenhouse"][0]
    assert greenhouse.source_channel == "hosted_url"
    assert greenhouse.raw_candidate_value == "stripe"
    assert greenhouse.normalized_token == "stripe"

    lever = [c for c in candidates if c.detected_provider == "lever"][0]
    assert lever.source_channel == "career_redirect"
    assert lever.input_url == "https://acme.com/careers"
    assert lever.discovered_url == "https://jobs.lever.co/acme"


def test_discover_skips_unrecognized_or_failed_inputs(db_session, monkeypatch):
    service = JobSourceDiscoveryService(repository=JobSourceDiscoveryRepository(db_session))

    def _fake_get(url: str, timeout: float, allow_redirects: bool):
        return _FakeResponse("https://example.com/jobs", status_code=404)

    monkeypatch.setattr("src.domain.jobs.discovery_service.requests.get", _fake_get)

    run_id, candidates, provider_counts = service.discover(
        hosted_urls=["https://example.com/not-an-ats-url"],
        career_urls=["https://example.com/careers"],
    )

    assert run_id is not None
    assert candidates == []
    assert provider_counts == {}


def test_promote_candidates_skips_unsafe_token(db_session):
    service = JobSourceDiscoveryService(repository=JobSourceDiscoveryRepository(db_session))

    run_id, candidates, _ = service.discover(
        hosted_urls=["https://job-boards.greenhouse.io/jobs"],
        career_urls=[],
    )
    assert len(candidates) == 1

    from src.domain.jobs.repository import JobSourceRepository

    promoted_sources, selected_candidates, skipped_count = service.promote_candidates(
        source_repository=JobSourceRepository(db_session),
        run_id=run_id,
        candidate_ids=[],
        is_active=True,
    )

    assert selected_candidates == 1
    assert skipped_count == 1
    assert promoted_sources == []
