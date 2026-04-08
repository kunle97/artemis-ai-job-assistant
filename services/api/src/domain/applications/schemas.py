"""
Application domain schemas.

Pydantic models for creating and returning job application records.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ApplicationCreate(BaseModel):
    job_id: UUID
    notes: str | None = None


class ApplicationRead(BaseModel):
    id: UUID
    user_id: UUID
    job_id: UUID
    status: str
    is_ready_for_automation: bool
    notes: str | None = None
    failure_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)