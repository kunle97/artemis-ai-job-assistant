"""
Application domain schemas.

Pydantic models for creating and returning job application records.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field



class ApplicationSeed(BaseModel):
    """
    Seed data for creating an Application record from an external source.

    ``apply_url`` is required; the caller is responsible for resolving or
    creating the corresponding Job record and linking it before persisting.
    ``status`` should be an Artemis-canonical application status string.
    """

    apply_url: str
    company_name: str | None = None
    role_title: str | None = None
    status: str = "saved"
    notes: str | None = None


class ApplicationCreate(BaseModel):
    job_id: UUID
    resume_id: UUID | None = None
    notes: str | None = None


class ApplicationRead(BaseModel):
    id: UUID
    user_id: UUID
    job_id: UUID
    resume_id: UUID | None = None
    status: str
    is_ready_for_automation: bool
    is_authorized_to_submit: bool = False
    manual_review_required: bool = True
    notes: str | None = None
    failure_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationRunDispatchRead(BaseModel):
    """Response payload for async pipeline dispatch calls."""

    application_id: UUID
    task_id: str
    status: str = "queued"


class ApplicationStatusRead(BaseModel):
    """Combined status payload for one application."""

    application_id: UUID
    status: str
    is_ready_for_automation: bool
    manual_review_required: bool
    is_authorized_to_submit: bool
    failure_reason: str | None = None
    missing_items: list[str] = Field(default_factory=list)
    available_answer_keys: list[str] = Field(default_factory=list)


class ApplicationLifecycleStatusUpdate(BaseModel):
    """Payload for manually updating the lifecycle status after submission."""

    status: str