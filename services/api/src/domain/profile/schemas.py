"""
Candidate profile schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CandidateProfileUpsertRequest(BaseModel):
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    zip_code: str | None = None
    salary_target: str | None = None

    gender: str | None = None
    race: str | None = None
    veteran_status: str | None = None
    disability_status: str | None = None

    autofill_gender: bool | None = None
    autofill_race: bool | None = None
    autofill_veteran_status: bool | None = None
    autofill_disability_status: bool | None = None


CandidateProfileCreate = CandidateProfileUpsertRequest


class CandidateProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str

    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None

    city: str | None = None
    state: str | None = None
    country: str | None = None
    zip_code: str | None = None

    salary_target: str | None = None

    gender: str | None = None
    race: str | None = None
    veteran_status: str | None = None
    disability_status: str | None = None

    autofill_gender: bool = False
    autofill_race: bool = False
    autofill_veteran_status: bool = False
    autofill_disability_status: bool = False

    location: str | None = None