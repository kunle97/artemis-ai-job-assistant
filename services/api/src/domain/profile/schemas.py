"""
Profile domain schemas.

Pydantic models for creating and returning structured candidate profiles.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CandidateProfileWrite(BaseModel):
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    years_experience: int | None = None
    work_authorization: str | None = None
    requires_sponsorship: bool = False
    current_title: str | None = None
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    target_titles: list[str] = Field(default_factory=list)
    remote_preference: str | None = None
    salary_min: int | None = None
    salary_target: int | None = None
    default_answers: dict = Field(default_factory=dict)


class CandidateProfileCreate(CandidateProfileWrite):
    user_id: UUID


class CandidateProfileRead(BaseModel):
    id: UUID
    user_id: UUID
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    years_experience: int | None = None
    work_authorization: str | None = None
    requires_sponsorship: bool
    current_title: str | None = None
    summary: str | None = None
    skills: list[str]
    industries: list[str]
    target_titles: list[str]
    remote_preference: str | None = None
    salary_min: int | None = None
    salary_target: int | None = None
    default_answers: dict
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)