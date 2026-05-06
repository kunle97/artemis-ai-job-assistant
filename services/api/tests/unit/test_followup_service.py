"""
Unit tests for follow-up service.

Tests cadence logic, urgency computation, and follow-up calculations.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.domain.applications.followup.constants import CADENCE, FOLLOWUP_TYPES
from src.domain.applications.followup.models import FollowUp
from src.domain.applications.followup.service import FollowUpService
from src.domain.applications.models import Application
from src.domain.auth.models import User


@pytest.fixture
def user(db_session: Session) -> User:
    """Create a test user."""
    user = User(email="test@example.com", password="hashed")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def application_applied(db_session: Session, user: User) -> Application:
    """Create an application with 'applied' status."""
    now = datetime.now(UTC)
    app = Application(
        user_id=user.id,
        job_id=uuid4(),
        status="applied",
        updated_at=now,
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)
    return app


@pytest.fixture
def application_responded(db_session: Session, user: User) -> Application:
    """Create an application with 'responded' status."""
    now = datetime.now(UTC)
    app = Application(
        user_id=user.id,
        job_id=uuid4(),
        status="responded",
        updated_at=now,
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)
    return app


@pytest.fixture
def application_interview(db_session: Session, user: User) -> Application:
    """Create an application with 'interview' status."""
    now = datetime.now(UTC)
    app = Application(
        user_id=user.id,
        job_id=uuid4(),
        status="interview",
        updated_at=now,
    )
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)
    return app


class TestFollowUpService:
    """Test follow-up service functionality."""

    def test_calculate_first_followup_for_applied_status(
        self, db_session: Session, user: User, application_applied: Application
    ):
        """Test that first follow-up is calculated for applied status."""
        service = FollowUpService(db_session)
        followups = service.calculate_followups_for_user(user.id)

        assert len(followups) == 1
        followup = followups[0]
        assert followup['application_id'] == application_applied.id
        assert followup['type'] == FOLLOWUP_TYPES['first']
        assert not followup['is_overdue']

        # Verify database record
        db_followup = db_session.query(FollowUp).filter_by(application_id=application_applied.id).first()
        assert db_followup is not None
        assert db_followup.followup_type == FOLLOWUP_TYPES['first']

    def test_calculate_thankyou_followup_for_responded_status(
        self, db_session: Session, user: User, application_responded: Application
    ):
        """Test that thank-you follow-up is calculated for responded status."""
        service = FollowUpService(db_session)
        followups = service.calculate_followups_for_user(user.id)

        assert len(followups) == 1
        followup = followups[0]
        assert followup['application_id'] == application_responded.id
        assert followup['type'] == FOLLOWUP_TYPES['thank_you']

    def test_calculate_thankyou_followup_for_interview_status(
        self, db_session: Session, user: User, application_interview: Application
    ):
        """Test that thank-you follow-up is calculated for interview status."""
        service = FollowUpService(db_session)
        followups = service.calculate_followups_for_user(user.id)

        assert len(followups) == 1
        followup = followups[0]
        assert followup['application_id'] == application_interview.id
        assert followup['type'] == FOLLOWUP_TYPES['thank_you']

    def test_overdue_detection(self, db_session: Session, user: User, application_applied: Application):
        """Test that overdue follow-ups are correctly detected."""
        # Set application to 10 days ago (past the 7-day cadence)
        past_date = datetime.now(UTC) - timedelta(days=10)
        application_applied.updated_at = past_date
        db_session.commit()

        service = FollowUpService(db_session)
        followups = service.calculate_followups_for_user(user.id)

        assert len(followups) == 1
        assert followups[0]['is_overdue']

    def test_multiple_applications_for_user(self, db_session: Session, user: User):
        """Test that service handles multiple applications."""
        app1 = Application(user_id=user.id, job_id=uuid4(), status="applied")
        app2 = Application(user_id=user.id, job_id=uuid4(), status="responded")
        db_session.add_all([app1, app2])
        db_session.commit()

        service = FollowUpService(db_session)
        followups = service.calculate_followups_for_user(user.id)

        assert len(followups) == 2

    def test_get_followups_grouped_by_urgency(self, db_session: Session, user: User):
        """Test that get_followups returns grouped results."""
        # Create applications with different timings
        now = datetime.now(UTC)

        # Overdue: 10 days ago
        app_overdue = Application(
            user_id=user.id, job_id=uuid4(), status="applied",
            updated_at=now - timedelta(days=10)
        )
        db_session.add(app_overdue)
        db_session.commit()

        service = FollowUpService(db_session)
        result = service.get_followups_for_user(user.id)

        assert 'overdue' in result
        assert 'urgent' in result
        assert 'upcoming' in result
        assert 'total' in result
        assert result['total'] >= 1

    def test_ignored_statuses(self, db_session: Session, user: User):
        """Test that non-actionable statuses are ignored."""
        # Create applications with non-actionable statuses
        app_rejected = Application(user_id=user.id, job_id=uuid4(), status="rejected")
        app_rejected.status = "rejected"
        db_session.add(app_rejected)
        db_session.commit()

        service = FollowUpService(db_session)
        followups = service.calculate_followups_for_user(user.id)

        assert len(followups) == 0

    def test_idempotent_calculation(
        self, db_session: Session, user: User, application_applied: Application
    ):
        """Test that recalculating follow-ups is idempotent."""
        service = FollowUpService(db_session)

        # First calculation
        followups1 = service.calculate_followups_for_user(user.id)
        db_count_1 = db_session.query(FollowUp).filter_by(application_id=application_applied.id).count()

        # Second calculation
        followups2 = service.calculate_followups_for_user(user.id)
        db_count_2 = db_session.query(FollowUp).filter_by(application_id=application_applied.id).count()

        assert len(followups1) == len(followups2)
        assert db_count_1 == db_count_2  # Should not create duplicates

    def test_cadence_thresholds(self, db_session: Session, user: User, application_applied: Application):
        """Test that cadence thresholds are respected."""
        service = FollowUpService(db_session)
        followups = service.calculate_followups_for_user(user.id)

        followup = followups[0]
        now = datetime.now(UTC)
        days_until_due = (followup['due_date'] - now).days

        # Should be approximately 7 days from now
        assert 6 <= days_until_due <= 8  # Allow 1 day variance

