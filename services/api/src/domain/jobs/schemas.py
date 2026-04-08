"""
Job domain schemas.

Pydantic models for normalized job records and job search requests.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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