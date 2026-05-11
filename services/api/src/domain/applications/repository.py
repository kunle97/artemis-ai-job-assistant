"""
Application repository.

Handles database operations for user job applications.
"""

from datetime import datetime, timezone
import logging

from sqlalchemy.orm import Session

from src.domain.applications.models import Application


logger = logging.getLogger(__name__)

_JOB_ID_IN_CLAUSE_CHUNK_SIZE = 1000


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

        # Deduplicate first to avoid oversized SQL parameter lists.
        normalized_job_ids = []
        seen_job_ids = set()
        for job_id in job_ids:
            if job_id is None or job_id in seen_job_ids:
                continue
            seen_job_ids.add(job_id)
            normalized_job_ids.append(job_id)

        if not normalized_job_ids:
            return []

        if len(normalized_job_ids) > _JOB_ID_IN_CLAUSE_CHUNK_SIZE:
            logger.info(
                "[ApplicationRepository] list_by_user_and_job_ids chunking user_id=%s job_ids=%d chunk_size=%d",
                user_id,
                len(normalized_job_ids),
                _JOB_ID_IN_CLAUSE_CHUNK_SIZE,
            )

        matched_applications = []
        for idx in range(0, len(normalized_job_ids), _JOB_ID_IN_CLAUSE_CHUNK_SIZE):
            chunk = normalized_job_ids[idx : idx + _JOB_ID_IN_CLAUSE_CHUNK_SIZE]
            matched_applications.extend(
                self.db.query(Application)
                .filter(Application.user_id == user_id, Application.job_id.in_(chunk))
                .all()
            )

        # Preserve previous API contract: newest first.
        return sorted(
            matched_applications,
            key=lambda application: application.created_at
            or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
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

    def delete_by_id(self, application_id) -> bool:
        deleted_rows = (
            self.db.query(Application)
            .filter(Application.id == application_id)
            .delete()
        )
        self.db.commit()
        return deleted_rows > 0

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