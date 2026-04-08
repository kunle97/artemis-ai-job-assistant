"""
Application answer schemas.

Pydantic models for saving and returning reusable application answers.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ApplicationAnswerCreate(BaseModel):
    question_key: str
    category: str | None = None
    question_text: str | None = None
    answer_text: str


class ApplicationAnswerRead(BaseModel):
    id: UUID
    user_id: UUID
    question_key: str
    category: str | None = None
    question_text: str | None = None
    answer_text: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)