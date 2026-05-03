"""
Job domain helper functions.

Contains reusable token-resolution logic for board-backed job searches.
"""

from src.domain.jobs.schemas import JobSearchRequest
from src.domain.jobs.source_registry import JOB_SOURCE_REGISTRY


def resolve_board_tokens(payload: JobSearchRequest) -> list[str]:
    """
    Resolve one or more board tokens from the request using:
    1. direct board_token
    2. company_name via registry
    3. company_names via registry
    """
    if payload.board_token:
        return [payload.board_token]

    source_map = JOB_SOURCE_REGISTRY.get(payload.source, {})
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
