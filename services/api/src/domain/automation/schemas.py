"""
Automation schemas.

Pydantic models for application page intake and field inventory results.
"""

from pydantic import BaseModel, Field


class ApplicationPageIntakeRequest(BaseModel):
    application_url: str


class ApplicationFieldOption(BaseModel):
    label: str | None = None
    value: str | None = None


class ApplicationFieldInventoryItem(BaseModel):
    field_type: str
    input_subtype: str | None = None
    label: str | None = None
    name: str | None = None
    placeholder: str | None = None
    required: bool = False
    options: list[ApplicationFieldOption] = Field(default_factory=list)


class ApplicationPageIntakeResult(BaseModel):
    application_url: str
    status: str
    title: str | None = None
    job_context: str | None = None
    already_applied: bool = False
    fields: list[ApplicationFieldInventoryItem] = Field(default_factory=list)
    screenshot_path: str | None = None
    notes: list[str] = Field(default_factory=list)