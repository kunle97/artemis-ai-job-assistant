"""
Models for manual fill / retry flow.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AutomationManualFieldOverride(BaseModel):
    label: str | None = None
    name: str | None = None
    value: str


class AutomationManualFillRequest(BaseModel):
    application_url: str
    inspected_fields: list[dict] = Field(default_factory=list)
    field_overrides: list[AutomationManualFieldOverride] = Field(default_factory=list)
    resume_file_path: str | None = None