"""
Application analytics repository.

Fetches the Application and ApplicationScore records required for
pattern analysis without introducing cross-domain SQLAlchemy coupling.
"""

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.applications.models import Application
from src.domain.jobs.scoring.repository import ApplicationScoreRepository

logger = logging.getLogger(__name__)


class ApplicationPatternRepository:
    """Retrieves application and score data needed for analytics."""

    def __init__(self, db: Session, score_repository: ApplicationScoreRepository):
        self.db = db
        self._score_repo = score_repository

    def list_applications_by_user(self, user_id) -> list[Application]:
        """Return all Application records for a user, newest first."""
        return (
            self.db.query(Application)
            .filter(Application.user_id == user_id)
            .order_by(Application.created_at.desc())
            .all()
        )

    def list_scores_for_applications(
        self, application_ids: list
    ) -> dict:
        """
        Return a mapping of application_id → global_score for the supplied IDs.
        Only returns entries where a score record exists.
        Accepts both string and UUID application IDs.
        """
        if not application_ids:
            return {}

        # Convert string IDs to UUIDs to handle test DB type coercion
        app_ids_as_uuids = [
            id if isinstance(id, UUID) else UUID(id)
            for id in application_ids
        ]

        scores = self._score_repo.list_by_application_ids(app_ids_as_uuids)

        return {
            str(score.application_id): score.global_score
            for score in scores
            if score.global_score is not None
        }
