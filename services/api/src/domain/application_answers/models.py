"""
Application answer models.

Stores reusable user-provided answers for common job application questions.
"""

from datetime import UTC, datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from src.infrastructure.db.base import Base


class ApplicationAnswer(Base):
    __tablename__ = "application_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    question_key = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    question_text = Column(Text, nullable=True)
    answer_text = Column(Text, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))