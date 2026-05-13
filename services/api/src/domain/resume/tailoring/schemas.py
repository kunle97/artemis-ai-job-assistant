"""
Resume tailoring schemas.

Pydantic request/response models for per-application resume tailoring.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TailorResumeRequest(BaseModel):
    """Optional resume override; defaults to application resume or latest."""

    resume_id: UUID | None = None
    job_description: str | None = None


class TailoringRecommendation(BaseModel):
    """A single suggested rewrite for a resume section."""

    section: str
    current_text: str
    proposed_text: str
    reason: str
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)


class TailoredResumeResult(BaseModel):
    """Structured resume tailoring response."""

    application_id: UUID
    resume_id: UUID | None = None
    generated_at: datetime

    is_fallback: bool = False
    message: str | None = None

    suggestions: list[TailoringRecommendation] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
