"""
Models for automation fill flow.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class AutomationFillRequest(BaseModel):
    application_url: str
    inspected_fields: list[dict] = Field(default_factory=list)
    application_id: UUID | None = None
    resume_file_path: str | None = None
    page_title: str | None = None
    job_context: str | None = None


class AutomationFillFieldResult(BaseModel):
    label: str | None = None
    name: str | None = None
    classified_role: str
    resolved_value: str | None = None
    fill_status: str


class AutomationUnresolvedField(BaseModel):
    label: str | None = None
    name: str | None = None
    classified_role: str
    resolved_value: str | None = None
    fill_status: str
    reason: str | None = None


class AutomationFillResult(BaseModel):
    application_url: str
    fields: list[AutomationFillFieldResult]
    filled_count: int
    skipped_count: int
    screenshot_path: str | None = None
    unresolved_fields: list[AutomationUnresolvedField] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    submission_confirmed: bool = False