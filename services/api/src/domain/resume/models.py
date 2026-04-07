"""
Resume domain models.

Stores uploaded resume metadata and parsed output references for a user.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON

from src.infrastructure.db.base import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    file_name = Column(String(255), nullable=False)
    file_path = Column(String, nullable=False)
    mime_type = Column(String(100), nullable=True)

    extracted_text = Column(String, nullable=True)
    parsed_json = Column(JSON, nullable=True)

    variant_type = Column(String(50), default="master")
    is_primary = Column(Boolean, default=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))