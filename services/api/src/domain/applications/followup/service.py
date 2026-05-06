"""
Follow-up domain service.

Orchestrates follow-up cadence calculation and tracking for active applications.
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.applications.followup.constants import (
    ACTIONABLE_STATUSES,
    CADENCE,
    FOLLOWUP_TYPES,
)
from src.domain.applications.followup.repository import FollowUpRepository
from src.domain.applications.models import Application

logger = logging.getLogger(__name__)


class FollowUpService:
    """Service for follow-up cadence tracking and recommendations."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = FollowUpRepository(db)

    def calculate_followups_for_user(self, user_id: UUID) -> list[dict]:
        """
        Scan a user's active applications and calculate follow-up recommendations.

        Returns:
            List of follow-up dictionaries with application_id, due_date, type, is_overdue
        """
        logger.info(f"Calculating follow-ups for user {user_id}")

        # Fetch active applications for this user
        applications = (
            self.db.query(Application)
            .filter(Application.user_id == user_id)
            .filter(Application.status.in_(ACTIONABLE_STATUSES))
            .all()
        )

        followups = []
        now = datetime.now(UTC)

        for app in applications:
            # Get existing follow-up record (if any)
            existing_followup = self.repo.get_by_application_id(app.id)

            # Calculate next follow-up based on status and history
            followup_info = self._calculate_next_followup(
                app, existing_followup, now
            )

            if followup_info:
                # Create or update the follow-up record
                due_date = followup_info['due_date']
                due_naive = due_date.replace(tzinfo=None) if due_date.tzinfo else due_date
                now_naive = now.replace(tzinfo=None)
                is_overdue = due_naive <= now_naive

                self.repo.create_or_update(
                    application_id=app.id,
                    user_id=user_id,
                    due_date=due_date,
                    followup_type=followup_info['type'],
                    is_overdue=is_overdue,
                )

                followups.append({
                    'application_id': app.id,
                    'due_date': due_date,
                    'type': followup_info['type'],
                    'is_overdue': is_overdue,
                })
            else:
                # No more follow-ups needed (e.g., max reached for applied status)
                logger.info(
                    f"No follow-up needed for application {app.id} (status={app.status})"
                )

        logger.info(f"Calculated {len(followups)} follow-ups for user {user_id}")
        return followups

    def _calculate_next_followup(
        self, app: Application, existing_followup, now: datetime
    ) -> dict | None:
        """
        Calculate the next follow-up for an application based on status and history.

        Returns:
            Dict with 'due_date' and 'type', or None if no follow-up needed.
        """
        days_since_update = (now - app.updated_at.replace(tzinfo=UTC)).days

        if app.status == 'applied':
            # For applied status, track follow-up count
            if existing_followup:
                # Existing follow-up: check if we've hit max
                if existing_followup.followup_type == FOLLOWUP_TYPES['subsequent']:
                    # Count how many follow-ups have been done
                    followup_count = self._count_followups_for_app(app.id)
                    if followup_count >= CADENCE['applied_max_followups']:
                        return None  # Max reached, cold
                    # Schedule next follow-up
                    due_date = existing_followup.due_date + timedelta(
                        days=CADENCE['applied_subsequent']
                    )
                    return {'due_date': due_date, 'type': FOLLOWUP_TYPES['subsequent']}
                else:
                    # First follow-up already exists, schedule subsequent
                    due_date = existing_followup.due_date + timedelta(
                        days=CADENCE['applied_subsequent']
                    )
                    return {'due_date': due_date, 'type': FOLLOWUP_TYPES['subsequent']}
            else:
                # No existing follow-up, schedule first one
                due_date = app.updated_at.replace(tzinfo=UTC) + timedelta(
                    days=CADENCE['applied_first']
                )
                return {'due_date': due_date, 'type': FOLLOWUP_TYPES['first']}

        elif app.status == 'responded':
            # Thank-you follow-up (1 day after status changed)
            if existing_followup:
                # Already have a thank-you, schedule next reach-out in 3 days
                due_date = existing_followup.due_date + timedelta(
                    days=CADENCE['responded_subsequent']
                )
                return {'due_date': due_date, 'type': FOLLOWUP_TYPES['subsequent']}
            else:
                # First follow-up: thank-you note
                due_date = app.updated_at.replace(tzinfo=UTC) + timedelta(
                    days=CADENCE['responded_initial']
                )
                return {'due_date': due_date, 'type': FOLLOWUP_TYPES['thank_you']}

        elif app.status == 'interview':
            # Thank-you follow-up (1 day after interview)
            if existing_followup:
                # Already sent thank-you, no further follow-ups
                return None
            else:
                due_date = app.updated_at.replace(tzinfo=UTC) + timedelta(
                    days=CADENCE['interview_thankyou']
                )
                return {'due_date': due_date, 'type': FOLLOWUP_TYPES['thank_you']}

        return None

    def _count_followups_for_app(self, application_id: UUID) -> int:
        """Count how many follow-ups have been completed for an application."""
        followup = self.db.query(Application).filter(Application.id == application_id).first()
        if not followup:
            return 0
        # In a full implementation, this would query a follow-up history table
        # For now, assume max 2 based on the most recent record
        return 1

    def get_followups_for_user(self, user_id: UUID) -> dict:
        """
        Get grouped follow-ups for a user (overdue, urgent, upcoming).

        Returns:
            Dict with 'overdue', 'urgent', 'upcoming' lists and 'total' count
        """
        logger.info(f"Fetching follow-ups for user {user_id}")

        # Calculate fresh follow-ups
        self.calculate_followups_for_user(user_id)

        # Fetch all follow-ups for user
        all_followups = self.repo.get_by_user_id(user_id)

        now = datetime.now(UTC)
        urgent_threshold = now + timedelta(days=2)

        result = {'overdue': [], 'urgent': [], 'upcoming': [], 'total': len(all_followups)}

        for followup in all_followups:
            due = followup.due_date.replace(tzinfo=UTC) if followup.due_date.tzinfo is None else followup.due_date
            if due <= now:
                result['overdue'].append(followup)
            elif due <= urgent_threshold:
                result['urgent'].append(followup)
            else:
                result['upcoming'].append(followup)

        logger.info(
            f"Retrieved {len(all_followups)} follow-ups for user {user_id}: "
            f"overdue={len(result['overdue'])}, urgent={len(result['urgent'])}, "
            f"upcoming={len(result['upcoming'])}"
        )

        return result
