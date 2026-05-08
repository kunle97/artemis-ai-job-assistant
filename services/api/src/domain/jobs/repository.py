"""
Job repository.

Handles DB operations for jobs.
"""

from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from src.domain.jobs.models import Job, JobFeedStatus, JobPreferences, JobSource, JobUserFeed


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, job_id):
        return self.db.query(Job).filter(Job.id == job_id).first()

    def update_apply_url(self, job_id, apply_url: str):
        job = self.get_by_id(job_id)
        if job is None:
            return None

        job.apply_url = apply_url
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_by_source_and_source_job_id(self, source: str, source_job_id: str):
        return (
            self.db.query(Job)
            .filter(Job.source == source, Job.source_job_id == source_job_id)
            .first()
        )

    def create(self, **job_data):
        job = Job(**job_data)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_or_create(self, **job_data):
        existing = self.get_by_source_and_source_job_id(
            source=job_data["source"],
            source_job_id=job_data["source_job_id"],
        )
        if existing:
            updated = False
            for field in ["location", "workplace_type", "description", "apply_url", "salary_min", "salary_max", "currency"]:
                incoming = job_data.get(field)
                current = getattr(existing, field)
                if incoming is not None and incoming != "" and (current is None or current == ""):
                    setattr(existing, field, incoming)
                    updated = True
            if updated:
                self.db.add(existing)
                self.db.commit()
                self.db.refresh(existing)
            return existing
        return self.create(**job_data)

    def list_all(self):
        return self.db.query(Job).order_by(Job.created_at.desc()).all()

    def list_paginated(self, skip: int = 0, limit: int = 20) -> tuple[list, int]:
        base = self.db.query(Job).order_by(Job.created_at.desc())
        total = base.count()
        jobs = base.offset(skip).limit(limit).all()
        return jobs, total

    def list_active_by_sources(self, enabled_sources: list[str]) -> list["Job"]:
        query = self.db.query(Job).filter(Job.is_active == True)  # noqa: E712
        if enabled_sources:
            query = query.filter(Job.source.in_(enabled_sources))
        return query.order_by(Job.created_at.desc()).all()


class JobPreferencesRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id):
        return (
            self.db.query(JobPreferences)
            .filter(JobPreferences.user_id == user_id)
            .first()
        )

    def get_or_create_by_user_id(self, user_id):
        preferences = self.get_by_user_id(user_id)
        if preferences is not None:
            return preferences

        preferences = JobPreferences(user_id=user_id)
        self.db.add(preferences)
        self.db.commit()
        self.db.refresh(preferences)
        return preferences

    def upsert(self, user_id, payload):
        preferences = self.get_or_create_by_user_id(user_id)

        preferences.target_titles = payload.target_titles
        preferences.positive_keywords = payload.positive_keywords
        preferences.negative_keywords = payload.negative_keywords
        preferences.locations = payload.locations
        preferences.remote_only = payload.remote_only
        preferences.salary_min = payload.salary_min
        preferences.enabled_sources = payload.enabled_sources

        self.db.add(preferences)
        self.db.commit()
        self.db.refresh(preferences)
        return preferences

    def list_user_ids_with_enabled_sources(self) -> list:
        """Return user IDs whose job preferences have at least one enabled source."""
        preferences = self.db.query(JobPreferences).all()
        return [preference.user_id for preference in preferences if preference.enabled_sources]


class JobSourceRepository:
    """Repository for configurable ATS source and board-token mappings."""

    def __init__(self, db: Session):
        self.db = db

    def list_active(self) -> list[JobSource]:
        return (
            self.db.query(JobSource)
            .filter(JobSource.is_active == True)  # noqa: E712
            .order_by(JobSource.source.asc(), JobSource.company_key.asc())
            .all()
        )

    def get_by_source_and_key(self, source: str, company_key: str) -> JobSource | None:
        return (
            self.db.query(JobSource)
            .filter(JobSource.source == source, JobSource.company_key == company_key)
            .first()
        )

    def upsert(
        self,
        source: str,
        company_key: str,
        board_token: str,
        display_name: str,
        is_active: bool = True,
    ) -> JobSource:
        entry = self.get_by_source_and_key(source=source, company_key=company_key)
        if entry is None:
            entry = JobSource(
                source=source,
                company_key=company_key,
                board_token=board_token,
                display_name=display_name,
                is_active=is_active,
            )
        else:
            entry.board_token = board_token
            entry.display_name = display_name
            entry.is_active = is_active

        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry


class JobUserFeedRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_and_job_id(self, user_id, job_id):
        return (
            self.db.query(JobUserFeed)
            .filter(JobUserFeed.user_id == user_id, JobUserFeed.job_id == job_id)
            .first()
        )

    def get_or_create(self, user_id, job_id, status: JobFeedStatus = JobFeedStatus.NEW):
        existing = self.get_by_user_and_job_id(user_id=user_id, job_id=job_id)
        if existing is not None:
            return existing, False

        link = JobUserFeed(user_id=user_id, job_id=job_id, status=status)
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link, True

    def update_status(self, user_id, job_id, status: JobFeedStatus):
        link = self.get_by_user_and_job_id(user_id=user_id, job_id=job_id)
        if link is None:
            return None

        link.status = status
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def list_for_user(self, user_id, status: JobFeedStatus | None = None):
        query = (
            self.db.query(JobUserFeed)
            .options(joinedload(JobUserFeed.job))
            .join(Job)
            .filter(JobUserFeed.user_id == user_id, Job.is_active == True)  # noqa: E712
            .order_by(JobUserFeed.created_at.desc())
        )
        if status is not None:
            query = query.filter(JobUserFeed.status == status)
        return query.all()