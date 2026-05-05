"""
Application domain models.

Stores a user's intent and progress for applying to a job.
"""

from datetime import UTC, datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from src.infrastructure.db.base import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True)

    status = Column(String(50), nullable=False, default="queued")
    is_ready_for_automation = Column(Boolean, default=False)

    is_authorized_to_submit = Column(Boolean, nullable=False, default=False)
    manual_review_required = Column(Boolean, nullable=False, default=True)

    notes = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))