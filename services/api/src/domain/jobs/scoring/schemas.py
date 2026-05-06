"""
Job scoring domain schemas.

Pydantic models for job score results returned by the scoring endpoint.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobScoreRead(BaseModel):
    id: UUID
    application_id: UUID
    user_id: UUID

    role_fit: float | None = None
    seniority_match: float | None = None
    location_match: float | None = None

    global_score: float | None = None
    skills_gap_summary: str | None = None

    # One of: apply_immediately, worth_applying, apply_if_specific_reason, recommend_against
    recommendation: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
