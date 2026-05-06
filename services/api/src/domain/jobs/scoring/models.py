"""
Job scoring domain models.

Stores per-application scoring results produced by the JobScoringService.
"""

from datetime import UTC, datetime
import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from src.infrastructure.db.base import Base


class ApplicationScore(Base):
    __tablename__ = "application_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("applications.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Dimension scores (0–5 scale, matching career-ops scoring system)
    role_fit = Column(Float, nullable=True)
    seniority_match = Column(Float, nullable=True)
    location_match = Column(Float, nullable=True)

    global_score = Column(Float, nullable=True)
    skills_gap_summary = Column(Text, nullable=True)

    # Recommendation tier derived from global_score thresholds
    recommendation = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))
