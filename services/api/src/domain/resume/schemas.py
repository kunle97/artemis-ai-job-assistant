"""
Resume domain schemas.

Pydantic models for returning uploaded resume metadata and parsed results.
"""

from datetime import datetime
from uuid import UUID
from typing import Any

from pydantic import BaseModel, ConfigDict


class ResumeRead(BaseModel):
    id: UUID
    user_id: UUID
    file_name: str
    file_path: str
    mime_type: str | None = None
    extracted_text: str | None = None
    parsed_json: dict[str, Any] | None = None
    variant_type: str
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)