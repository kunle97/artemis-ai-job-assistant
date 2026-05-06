"""
Job domain helper functions.

Contains reusable token-resolution and preference-matching logic for job searches.
"""

import re

from src.domain.jobs.schemas import JobSearchRequest


def resolve_board_tokens(payload: JobSearchRequest, source_map: dict[str, dict]) -> list[str]:
    """
    Resolve one or more board tokens from the request using:
    1. direct board_token
    2. company_name via registry
    3. company_names via registry
    """
    if payload.board_token:
        return [payload.board_token]

    resolved_tokens: list[str] = []

    if payload.company_name:
        resolved_tokens.append(
            lookup_company_board_token(
                source=payload.source,
                company_name=payload.company_name,
                source_map=source_map,
            )
        )

    for company_name in payload.company_names:
        resolved_tokens.append(
            lookup_company_board_token(
                source=payload.source,
                company_name=company_name,
                source_map=source_map,
            )
        )

    deduped_tokens: list[str] = []
    for token in resolved_tokens:
        if token not in deduped_tokens:
            deduped_tokens.append(token)

    if deduped_tokens:
        return deduped_tokens

    raise ValueError("Provide board_token, company_name, or company_names for job search.")


def lookup_company_board_token(
    *,
    source: str,
    company_name: str,
    source_map: dict,
) -> str:
    """Resolve a company name to a board token for a given source."""
    company_key = company_name.lower()

    if company_key in source_map:
        return source_map[company_key]["board_token"]

    raise ValueError(f"Unknown company '{company_name}' for source '{source}'.")


def filter_job_by_title(title: str, positive: list[str], negative: list[str]) -> bool:
    """Return True when a title passes positive/negative keyword rules.

    Rules are case-insensitive:
    - If `positive` is empty, the positive check passes.
    - Otherwise at least one positive keyword must be present in the title.
    - No negative keyword may be present in the title.
    """
    title_lower = (title or "").lower()
    positive_keywords = [keyword.lower() for keyword in positive]
    negative_keywords = [keyword.lower() for keyword in negative]

    positive_match = not positive_keywords or any(keyword in title_lower for keyword in positive_keywords)
    negative_match = any(keyword in title_lower for keyword in negative_keywords)

    return positive_match and not negative_match


def matches_job_location(job_location: str | None, preferred_locations: list[str]) -> bool:
    """Return True when a job location matches at least one preferred location.

    Matching is case-insensitive and compares normalized locality keys so
    values like "New York City", "New York, NY", and similar city variants
    match each other consistently.
    """
    if not preferred_locations:
        return True

    job_location_keys = _location_match_keys(job_location)
    if not job_location_keys:
        return False

    return any(
        _location_keys_overlap(job_location_keys, _location_match_keys(preferred_location))
        for preferred_location in preferred_locations
        if preferred_location
    )


def _normalize_location_value(value: str | None) -> str:
    """Normalize free-form location text for stable substring matching."""
    if not value:
        return ""

    normalized = value.lower().strip()
    normalized = normalized.replace("new york city", "new york")
    normalized = normalized.replace("nyc", "new york")
    normalized = normalized.replace("new york, ny", "new york")
    normalized = re.sub(r"\bnew york\s+ny\b", "new york", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _location_match_keys(value: str | None) -> set[str]:
    """Build comparable location keys from a free-form location string."""
    if not value:
        return set()

    keys: set[str] = set()
    raw_segments = [value]
    raw_segments.extend(segment.strip() for segment in re.split(r"[;/|]", value) if segment.strip())

    for segment in raw_segments:
        segment = segment.strip()
        if not segment:
            continue

        comma_parts = [part.strip() for part in segment.split(",") if part.strip()]
        dash_parts = [part.strip() for part in re.split(r"\s*-\s*", segment) if part.strip()]

        candidate_parts = {segment}
        candidate_parts.update(comma_parts)
        candidate_parts.update(dash_parts)
        if comma_parts:
            candidate_parts.add(comma_parts[0])

        for candidate in candidate_parts:
            normalized_candidate = _normalize_location_value(candidate)
            if not normalized_candidate:
                continue

            keys.add(normalized_candidate)
            stripped_candidate = _strip_location_suffixes(normalized_candidate)
            if stripped_candidate:
                keys.add(stripped_candidate)

    return keys


def _strip_location_suffixes(value: str) -> str:
    """Strip generic locality suffixes that should not affect city matching."""
    tokens = value.split()
    while tokens and tokens[-1] in {"city", "metro", "metropolitan", "region", "area"}:
        tokens.pop()
    return " ".join(tokens)


def _location_keys_overlap(job_location_keys: set[str], preferred_location_keys: set[str]) -> bool:
    """Return True when any normalized job/preference location key overlaps."""
    if not preferred_location_keys:
        return False

    return any(
        job_key == preferred_key
        or job_key in preferred_key
        or preferred_key in job_key
        for job_key in job_location_keys
        for preferred_key in preferred_location_keys
    )
