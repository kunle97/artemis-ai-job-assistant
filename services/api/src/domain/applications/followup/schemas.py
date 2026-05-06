"""
Follow-up domain schemas (Pydantic models).

Request and response DTOs for follow-up endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FollowUpRead(BaseModel):
    """Schema for follow-up response."""
    id: UUID
    application_id: UUID
    due_date: datetime
    followup_type: str = Field(description="Type of follow-up: first, subsequent, thank_you")
    is_overdue: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FollowUpListResponse(BaseModel):
    """Schema for list of follow-ups with grouping."""
    overdue: list[FollowUpRead] = Field(default_factory=list, description="Overdue follow-ups")
    urgent: list[FollowUpRead] = Field(default_factory=list, description="Due within 1-2 days")
    upcoming: list[FollowUpRead] = Field(default_factory=list, description="Future follow-ups")
    total: int = Field(description="Total count of follow-ups")

    model_config = ConfigDict(from_attributes=True)
