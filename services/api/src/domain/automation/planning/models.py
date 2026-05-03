"""
Models for automation planning flow.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AutomationFillPlanRequest(BaseModel):
    application_url: str
    inspected_fields: list[dict] = Field(default_factory=list)
    page_title: str | None = None
    job_context: str | None = None


class AutomationPlannedField(BaseModel):
    field_type: str
    input_subtype: str | None = None
    label: str | None = None
    name: str | None = None
    placeholder: str | None = None
    required: bool = False
    options: list[dict] = Field(default_factory=list)

    classified_role: str
    resolved_value: str | None = None
    needs_review: bool = False


class AutomationFillPlan(BaseModel):
    application_url: str
    fields: list[AutomationPlannedField] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)