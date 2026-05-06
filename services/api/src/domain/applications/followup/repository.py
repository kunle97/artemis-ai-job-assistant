"""
Follow-up repository layer.

Handles persistence of follow-up records.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.applications.followup.models import FollowUp


class FollowUpRepository:
    """Repository for follow-up persistence."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_application_id(self, application_id: UUID) -> FollowUp | None:
        """Get the most recent follow-up for an application."""
        return (
            self.db.query(FollowUp)
            .filter(FollowUp.application_id == application_id)
            .order_by(FollowUp.due_date.desc())
            .first()
        )

    def get_by_user_id(self, user_id: UUID) -> list[FollowUp]:
        """Get all follow-ups for a user."""
        return (
            self.db.query(FollowUp)
            .filter(FollowUp.user_id == user_id)
            .order_by(FollowUp.due_date.asc())
            .all()
        )

    def get_active_by_user_id(self, user_id: UUID) -> list[FollowUp]:
        """Get active follow-ups (not yet completed) for a user."""
        return (
            self.db.query(FollowUp)
            .filter(FollowUp.user_id == user_id)
            .filter(FollowUp.due_date <= datetime.now(UTC))
            .order_by(FollowUp.due_date.asc())
            .all()
        )

    def create_or_update(
        self,
        application_id: UUID,
        user_id: UUID,
        due_date: datetime,
        followup_type: str,
        is_overdue: bool = False,
    ) -> FollowUp:
        """Create a new follow-up or update the existing one (upsert)."""
        existing = self.get_by_application_id(application_id)

        if existing:
            existing.due_date = due_date
            existing.followup_type = followup_type
            existing.is_overdue = is_overdue
            existing.updated_at = datetime.now(UTC)
            self.db.add(existing)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        followup = FollowUp(
            application_id=application_id,
            user_id=user_id,
            due_date=due_date,
            followup_type=followup_type,
            is_overdue=is_overdue,
        )
        self.db.add(followup)
        self.db.commit()
        self.db.refresh(followup)
        return followup

    def delete_by_application_id(self, application_id: UUID) -> bool:
        """Delete follow-up record for an application."""
        count = self.db.query(FollowUp).filter(FollowUp.application_id == application_id).delete()
        self.db.commit()
        return count > 0
