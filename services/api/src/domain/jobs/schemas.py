"""
Job domain schemas.

Pydantic models for normalized job records and job search requests.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.domain.jobs.models import JobFeedStatus



class JobInboxEntry(BaseModel):
    """
    A job URL pending evaluation or automation in the Artemis pipeline.

    Represents a job posting the user has flagged for processing but which
    has not yet been turned into a full Job + Application record.
    """

    url: str
    notes: str | None = None


class JobBoardConfig(BaseModel):
    """
    Configuration for a single job board or company portal.

    Used when scanning external sources for new job postings.
    ``source`` identifies the adapter to use (greenhouse | lever | ashby | manual).
    ``board_token`` is the board-specific identifier required by some adapters.
    ``apply_url`` is a direct application URL for sources that don't use board tokens.
    """

    name: str
    source: str
    board_token: str | None = None
    apply_url: str | None = None


class JobPreferencesSchema(BaseModel):
    id: UUID | None = None
    user_id: UUID | None = None

    target_titles: list[str] = Field(default_factory=list)
    positive_keywords: list[str] = Field(default_factory=list)
    negative_keywords: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    remote_only: bool = False
    salary_min: int | None = None
    enabled_sources: list[str] = Field(default_factory=list)

    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class JobPreferencesUpsertRequest(BaseModel):
    target_titles: list[str] = Field(default_factory=list)
    positive_keywords: list[str] = Field(default_factory=list)
    negative_keywords: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    remote_only: bool = False
    salary_min: int | None = None
    enabled_sources: list[str] = Field(default_factory=list)


class JobSearchRequest(BaseModel):
    source: str
    board_token: str | None = None
    company_name: str | None = None
    company_names: list[str] = Field(default_factory=list)
    query: str | None = None
    location: str | None = None


class JobSourceDiscoveryRequest(BaseModel):
    hosted_urls: list[str] = Field(default_factory=list)
    career_urls: list[str] = Field(default_factory=list)


class JobSourceDiscoveryCandidateRead(BaseModel):
    id: UUID
    run_id: UUID
    source_channel: str
    input_url: str
    discovered_url: str
    detected_provider: str
    raw_candidate_value: str | None = None
    normalized_token: str | None = None
    extraction_timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class JobSourceDiscoveryResponse(BaseModel):
    run_id: UUID
    total_candidates: int
    provider_counts: dict[str, int]
    candidates: list[JobSourceDiscoveryCandidateRead]


class JobSourceDiscoveryPromoteRequest(BaseModel):
    run_id: UUID
    candidate_ids: list[UUID] = Field(default_factory=list)
    is_active: bool = True


class JobRead(BaseModel):
    id: UUID
    source: str
    source_job_id: str
    title: str
    company_name: str
    location: str | None = None
    workplace_type: str | None = None
    description: str | None = None
    apply_url: str
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeedJobRead(JobRead):
    application_id: UUID | None = None
    fit_score: float | None = None
    fit_recommendation: str | None = None
    fit_score_confidence: str | None = None
    feed_status: JobFeedStatus | None = None


class JobSourceRead(BaseModel):
    id: int
    source: str
    company_key: str
    board_token: str
    display_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobSourceDiscoveryPromoteResponse(BaseModel):
    run_id: UUID
    selected_candidates: int
    promoted_count: int
    skipped_count: int
    promoted_sources: list[JobSourceRead]


class FeedScanResponse(BaseModel):
    new_jobs_found: int
    discovery_run_id: UUID | None = None
    discovery_candidates_found: int | None = None
    discovery_promoted_count: int | None = None
    discovery_skipped_count: int | None = None


class JobFeedStatusUpdateRequest(BaseModel):
    status: JobFeedStatus


class JobFeedStatusUpdateResponse(BaseModel):
    job_id: UUID
    status: JobFeedStatus


class FeedPage(BaseModel):
    total: int
    skip: int
    limit: int
    has_next: bool
    prev_url: str | None = Field(default=None, serialization_alias="prevUrl")
    next_url: str | None
    jobs: list[FeedJobRead]

    model_config = ConfigDict(populate_by_name=True)