"""
Candidate profile schemas.
"""

from __future__ import annotations

from uuid import UUID

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
    min_salary: str | None = None

    gender: str | None = None
    race: str | None = None
    veteran_status: str | None = None
    disability_status: str | None = None
    pronouns: str | None = None

    autofill_gender: bool | None = None
    autofill_race: bool | None = None
    autofill_veteran_status: bool | None = None
    autofill_disability_status: bool | None = None
    autofill_pronouns: bool | None = None

    current_company: str | None = None

    preferred_relocation_cities: list[str] | None = None
    work_arrangement: list[str] | None = None
    skills: list[str] | None = None


CandidateProfileCreate = CandidateProfileUpsertRequest


class CandidateProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID

    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None

    city: str | None = None
    state: str | None = None
    country: str | None = None
    zip_code: str | None = None

    salary_target: str | None = None
    min_salary: str | None = None

    gender: str | None = None
    race: str | None = None
    veteran_status: str | None = None
    disability_status: str | None = None
    pronouns: str | None = None

    autofill_gender: bool = False
    autofill_race: bool = False
    autofill_veteran_status: bool = False
    autofill_disability_status: bool = False
    autofill_pronouns: bool = False

    current_company: str | None = None

    preferred_relocation_cities: list[str] | None = None
    work_arrangement: list[str] | None = None
    skills: list[str] | None = None

    location: str | None = None