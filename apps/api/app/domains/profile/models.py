"""
Profile domain models.

Represents the structured candidate profile extracted from a user's resume
and additional inputs. This becomes the canonical source of truth for applications.
"""

import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, UTC

from app.infrastructure.db.base import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)

    linkedin_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    portfolio_url = Column(String, nullable=True)

    years_experience = Column(Integer, nullable=True)

    work_authorization = Column(String(100), nullable=True)
    requires_sponsorship = Column(Boolean, default=False)

    current_title = Column(String(255), nullable=True)
    summary = Column(String, nullable=True)

    skills = Column(JSON, default=list)
    industries = Column(JSON, default=list)
    target_titles = Column(JSON, default=list)

    remote_preference = Column(String(50), nullable=True)

    salary_min = Column(Integer, nullable=True)
    salary_target = Column(Integer, nullable=True)

    default_answers = Column(JSON, default=dict)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))