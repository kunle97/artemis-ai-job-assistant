"""
Job repository.

Handles DB operations for jobs.
"""

from sqlalchemy.orm import Session

from src.domain.jobs.models import Job, JobPreferences


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, job_id):
        return self.db.query(Job).filter(Job.id == job_id).first()

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