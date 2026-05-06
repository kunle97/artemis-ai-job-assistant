"""
Follow-up domain models.

Stores calculated follow-up obligations for active applications.
"""

from datetime import UTC, datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from src.infrastructure.db.base import Base


class FollowUp(Base):
    """Tracks follow-up obligations for an application."""
    __tablename__ = "follow_ups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Follow-up details
    due_date = Column(DateTime, nullable=False)  # When follow-up should occur
    followup_type = Column(String(50), nullable=False)  # first, subsequent, thank_you
    is_overdue = Column(Boolean, default=False, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))

    def __repr__(self):
        return f"<FollowUp(application_id={self.application_id}, due_date={self.due_date}, type={self.followup_type})>"
