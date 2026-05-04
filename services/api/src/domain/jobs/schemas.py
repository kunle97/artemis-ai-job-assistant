"""
Job domain schemas.

Pydantic models for normalized job records and job search requests.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field



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


class FeedScanResponse(BaseModel):
    new_jobs_found: int


class FeedPage(BaseModel):
    total: int
    skip: int
    limit: int
    has_next: bool
    next_url: str | None
    jobs: list[JobRead]