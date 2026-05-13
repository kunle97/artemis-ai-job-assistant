"""
ATS source discovery service.

Discovers candidate ATS providers/tokens from hosted URLs and career-page redirects.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
import logging
import re
from uuid import UUID, uuid4

import requests

from src.domain.jobs.repository import JobSourceDiscoveryRepository, JobSourceRepository

logger = logging.getLogger(__name__)

_BLOCKED_TOKENS = {
    "all",
    "apply",
    "applications",
    "career",
    "careers",
    "company",
    "home",
    "index",
    "job",
    "jobs",
    "openings",
    "positions",
    "team",
}


_HOSTED_RULES: dict[str, tuple[str, re.Pattern[str]]] = {
    "greenhouse": (
        "greenhouse.io",
        re.compile(r"(?:job-boards\.)?greenhouse\.io/(?P<token>[a-z0-9][a-z0-9\-]{1,254})", re.IGNORECASE),
    ),
    "lever": (
        "lever.co",
        re.compile(r"jobs\.lever\.co/(?P<token>[a-z0-9][a-z0-9\-]{1,254})", re.IGNORECASE),
    ),
    "ashby": (
        "ashbyhq.com",
        re.compile(r"jobs\.ashbyhq\.com/(?P<token>[a-z0-9][a-z0-9\-]{1,254})", re.IGNORECASE),
    ),
}


def parse_csv_urls(csv_value: str) -> list[str]:
    """Parse a comma-separated URL setting into a trimmed URL list."""
    return [item.strip() for item in csv_value.split(",") if item.strip()]


def build_hosted_board_url(source: str, board_token: str) -> str | None:
    """Build a canonical hosted ATS URL from a source/token pair when supported."""
    source_key = (source or "").strip().lower()
    token = (board_token or "").strip()
    if not source_key or not token:
        return None

    if source_key == "greenhouse":
        return f"https://job-boards.greenhouse.io/{token}"
    if source_key == "lever":
        return f"https://jobs.lever.co/{token}"
    if source_key == "ashby":
        return f"https://jobs.ashbyhq.com/{token}"
    return None


@dataclass
class DiscoveryHit:
    source_channel: str
    input_url: str
    discovered_url: str
    detected_provider: str
    raw_candidate_value: str | None
    normalized_token: str | None


class JobSourceDiscoveryService:
    """Run ATS candidate discovery and persist evidence rows."""

    def __init__(self, repository: JobSourceDiscoveryRepository):
        self.repository = repository

    def discover(
        self,
        *,
        hosted_urls: list[str],
        career_urls: list[str],
        request_timeout_seconds: float = 10.0,
    ) -> tuple[UUID, list, dict[str, int]]:
        run_id = uuid4()
        logger.info(
            "[JobSourceDiscoveryService] Starting discovery run %s (hosted=%d, career=%d)",
            run_id,
            len(hosted_urls),
            len(career_urls),
        )

        hits: list[DiscoveryHit] = []

        for hosted_url in hosted_urls:
            maybe_hit = self._extract_from_url(
                source_channel="hosted_url",
                input_url=hosted_url,
                discovered_url=hosted_url,
            )
            if maybe_hit is not None:
                hits.append(maybe_hit)

        for career_url in career_urls:
            redirected_url = self._resolve_redirect_url(career_url, timeout_seconds=request_timeout_seconds)
            if redirected_url is None:
                continue
            maybe_hit = self._extract_from_url(
                source_channel="career_redirect",
                input_url=career_url,
                discovered_url=redirected_url,
            )
            if maybe_hit is not None:
                hits.append(maybe_hit)

        deduped_hits = self._dedupe_hits(hits)
        provider_counts = dict(Counter(hit.detected_provider for hit in deduped_hits))

        for hit in deduped_hits:
            self.repository.create_candidate(
                run_id=run_id,
                source_channel=hit.source_channel,
                input_url=hit.input_url,
                discovered_url=hit.discovered_url,
                detected_provider=hit.detected_provider,
                raw_candidate_value=hit.raw_candidate_value,
                normalized_token=hit.normalized_token,
            )

        candidates = self.repository.list_by_run_id(run_id)
        logger.info(
            "[JobSourceDiscoveryService] Completed run %s with %d candidates",
            run_id,
            len(candidates),
        )
        return run_id, candidates, provider_counts

    def discover_and_promote(
        self,
        *,
        source_repository: JobSourceRepository,
        hosted_urls: list[str],
        career_urls: list[str],
        is_active: bool = True,
    ) -> dict:
        """Run discovery and promote all safe candidates from a single run."""
        run_id, candidates, provider_counts = self.discover(
            hosted_urls=hosted_urls,
            career_urls=career_urls,
        )
        promoted_sources, selected_candidates, skipped_count = self.promote_candidates(
            source_repository=source_repository,
            run_id=run_id,
            candidate_ids=[],
            is_active=is_active,
        )
        return {
            "run_id": run_id,
            "candidates_found": len(candidates),
            "selected_candidates": selected_candidates,
            "promoted_count": len(promoted_sources),
            "skipped_count": skipped_count,
            "provider_counts": provider_counts,
        }

    def promote_candidates(
        self,
        *,
        source_repository: JobSourceRepository,
        run_id: UUID,
        candidate_ids: list[UUID],
        is_active: bool,
    ) -> tuple[list, int, int]:
        candidates = self.repository.list_by_run_id_and_ids(run_id=run_id, candidate_ids=candidate_ids)

        promoted_sources = []
        skipped_count = 0

        for candidate in candidates:
            if candidate.normalized_token is None:
                skipped_count += 1
                continue

            source = candidate.detected_provider.strip().lower()
            board_token = candidate.normalized_token.strip().lower()
            if not source or not board_token or not self._is_safe_token(board_token):
                skipped_count += 1
                continue

            company_key = self._derive_company_key(board_token)
            display_name = self._derive_display_name(company_key)
            promoted = source_repository.upsert(
                source=source,
                company_key=company_key,
                board_token=board_token,
                display_name=display_name,
                is_active=is_active,
            )
            promoted_sources.append(promoted)

        logger.info(
            "[JobSourceDiscoveryService] Promoted %d candidates from run %s (%d skipped)",
            len(promoted_sources),
            run_id,
            skipped_count,
        )
        return promoted_sources, len(candidates), skipped_count

    def _resolve_redirect_url(self, career_url: str, *, timeout_seconds: float) -> str | None:
        try:
            response = requests.get(career_url, timeout=timeout_seconds, allow_redirects=True)
        except requests.RequestException:
            logger.warning("[JobSourceDiscoveryService] Redirect resolution failed for %s", career_url)
            return None

        if response.status_code >= 400:
            logger.warning(
                "[JobSourceDiscoveryService] Redirect resolution returned %s for %s",
                response.status_code,
                career_url,
            )
            return None

        return response.url

    def _extract_from_url(self, *, source_channel: str, input_url: str, discovered_url: str) -> DiscoveryHit | None:
        lowered = discovered_url.lower()
        for provider, (host_fragment, pattern) in _HOSTED_RULES.items():
            if host_fragment not in lowered:
                continue
            match = pattern.search(discovered_url)
            raw = match.group("token") if match else None
            normalized = raw.lower().strip() if raw else None
            return DiscoveryHit(
                source_channel=source_channel,
                input_url=input_url,
                discovered_url=discovered_url,
                detected_provider=provider,
                raw_candidate_value=raw,
                normalized_token=normalized,
            )

        return None

    def _dedupe_hits(self, hits: list[DiscoveryHit]) -> list[DiscoveryHit]:
        seen: set[tuple[str, str, str, str | None]] = set()
        deduped: list[DiscoveryHit] = []
        for hit in hits:
            key = (
                hit.source_channel,
                hit.discovered_url,
                hit.detected_provider,
                hit.normalized_token,
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(hit)
        return deduped

    def _derive_company_key(self, token: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", token.lower())

    def _derive_display_name(self, company_key: str) -> str:
        return company_key.replace("-", " ").replace("_", " ").strip().title() or company_key

    def _is_safe_token(self, token: str) -> bool:
        if len(token) < 3:
            return False
        if token in _BLOCKED_TOKENS:
            return False
        if token.isdigit():
            return False
        if not re.fullmatch(r"[a-z0-9\-]+", token):
            return False
        return True


class DiscoveryClock:
    """Simple indirection for tests around UTC timestamps in responses."""

    @staticmethod
    def now() -> datetime:
        return datetime.now(UTC)
