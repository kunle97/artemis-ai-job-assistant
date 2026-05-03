"""
Job domain models.

Stores normalized job records collected from external job sources.
"""

from datetime import UTC, datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.infrastructure.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    source = Column(String(100), nullable=False)
    source_job_id = Column(String(255), nullable=False)

    title = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    workplace_type = Column(String(50), nullable=True)

    description = Column(Text, nullable=True)
    apply_url = Column(String, nullable=False)

    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    currency = Column(String(10), nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))


class JobPreferences(Base):
    __tablename__ = "job_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    target_titles = Column(JSONB, nullable=False, default=list)
    positive_keywords = Column(JSONB, nullable=False, default=list)
    negative_keywords = Column(JSONB, nullable=False, default=list)
    locations = Column(JSONB, nullable=False, default=list)
    remote_only = Column(Boolean, nullable=False, default=False)
    salary_min = Column(Integer, nullable=True)
    enabled_sources = Column(JSONB, nullable=False, default=list)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )