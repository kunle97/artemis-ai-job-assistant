"""
Candidate profile model.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.infrastructure.db.base import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    phone = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    portfolio_url = Column(String, nullable=True)

    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)

    salary_target = Column(String, nullable=True)

    gender = Column(String, nullable=True)
    race = Column(String, nullable=True)
    veteran_status = Column(String, nullable=True)
    disability_status = Column(String, nullable=True)

    autofill_gender = Column(Boolean, nullable=False, default=False)
    autofill_race = Column(Boolean, nullable=False, default=False)
    autofill_veteran_status = Column(Boolean, nullable=False, default=False)
    autofill_disability_status = Column(Boolean, nullable=False, default=False)

    skills = Column(JSONB, nullable=True)

    current_company = Column(String, nullable=True)

    work_authorization = Column(String, nullable=True)
    visa_sponsorship = Column(String, nullable=True)

    user = relationship("User", back_populates="candidate_profile")

    @property
    def location(self) -> str | None:
        parts = [self.city, self.state]
        parts = [p.strip() for p in parts if p]

        if parts:
            return ", ".join(parts)

        if self.country:
            return self.country

        return None