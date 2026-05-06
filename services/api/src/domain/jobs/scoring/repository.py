"""
Job scoring repository.

Handles database operations for application score records.
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.domain.jobs.scoring.models import ApplicationScore


class ApplicationScoreRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_application_id(self, application_id):
        return (
            self.db.query(ApplicationScore)
            .filter(ApplicationScore.application_id == application_id)
            .first()
        )

    def list_by_application_ids(self, application_ids):
        if not application_ids:
            return []

        return (
            self.db.query(ApplicationScore)
            .filter(ApplicationScore.application_id.in_(application_ids))
            .all()
        )

    def create_or_update(self, application_id, user_id, **score_data):
        existing = self.get_by_application_id(application_id)
        if existing:
            for key, value in score_data.items():
                setattr(existing, key, value)
            existing.updated_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        score = ApplicationScore(
            application_id=application_id,
            user_id=user_id,
            **score_data,
        )
        self.db.add(score)
        self.db.commit()
        self.db.refresh(score)
        return score
