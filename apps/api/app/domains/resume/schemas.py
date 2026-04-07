"""
Resume domain schemas.

Pydantic models for returning uploaded resume metadata and parsed results.
"""

from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any

from pydantic import BaseModel


class ResumeRead(BaseModel):
    id: UUID
    user_id: UUID
    file_name: str
    file_path: str
    mime_type: Optional[str] = None
    extracted_text: Optional[str] = None
    parsed_json: Optional[Dict[str, Any]] = None
    variant_type: str
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True