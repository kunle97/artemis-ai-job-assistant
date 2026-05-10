"""
Application repository.

Handles database operations for user job applications.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.domain.applications.models import Application


class ApplicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, application_id):
        return (
            self.db.query(Application)
            .filter(Application.id == application_id)
            .first()
        )

    def get_by_user_and_job(self, user_id, job_id):
        return (
            self.db.query(Application)
            .filter(Application.user_id == user_id, Application.job_id == job_id)
            .first()
        )

    def create(self, **application_data):
        application = Application(**application_data)
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application

    def list_by_user_id(self, user_id):
        return (
            self.db.query(Application)
            .filter(Application.user_id == user_id)
            .order_by(Application.created_at.desc())
            .all()
        )

    def list_by_user_and_job_ids(self, user_id, job_ids):
        if not job_ids:
            return []

        return (
            self.db.query(Application)
            .filter(Application.user_id == user_id, Application.job_id.in_(job_ids))
            .order_by(Application.created_at.desc())
            .all()
        )

    def update_fields(self, application_id, **fields):
        application = self.get_by_id(application_id)
        if not application:
            return None
        for key, value in fields.items():
            setattr(application, key, value)
        self.db.commit()
        self.db.refresh(application)
        return application

    def clear_resume_references(self, user_id, resume_id):
        updated_rows = (
            self.db.query(Application)
            .filter(
                Application.user_id == user_id,
                Application.resume_id == resume_id,
            )
            .update({Application.resume_id: None}, synchronize_session=False)
        )
        self.db.commit()
        return updated_rows

    def list_stale_submitted(self, submitted_before: datetime) -> list[Application]:
        """Return applications stuck in 'submitted' with updated_at before the cutoff."""
        return (
            self.db.query(Application)
            .filter(
                Application.status == "submitted",
                Application.updated_at < submitted_before,
            )
            .all()
        )