"""
Application service.

Coordinates creation and retrieval of user job application records.
"""

from src.domain.applications.constants import (
    APPLICATION_STATUS_NEEDS_REVIEW,
    APPLICATION_STATUS_SAVED,
)
from src.domain.applications.repository import ApplicationRepository
from src.domain.applications.schemas import ApplicationCreate
from src.domain.jobs.repository import JobRepository
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.resume.repository import ResumeRepository


class ApplicationService:
    def __init__(
        self,
        repository: ApplicationRepository,
        job_repository: JobRepository,
        profile_repository: CandidateProfileRepository,
        resume_repository: ResumeRepository,
    ):
        self.repository = repository
        self.job_repository = job_repository
        self.profile_repository = profile_repository
        self.resume_repository = resume_repository

    def create_application(self, user_id, payload: ApplicationCreate):
        existing = self.repository.get_by_user_and_job(user_id=user_id, job_id=payload.job_id)
        if existing:
            raise ValueError("You already created an application for this job.")

        job = self.job_repository.get_by_id(payload.job_id)
        if not job:
            raise ValueError("Job not found.")

        profile = self.profile_repository.get_by_user_id(user_id)
        resumes = self.resume_repository.get_by_user_id(user_id)

        is_ready = bool(profile and resumes)
        status = APPLICATION_STATUS_SAVED if is_ready else APPLICATION_STATUS_NEEDS_REVIEW

        return self.repository.create(
            user_id=user_id,
            job_id=payload.job_id,
            status=status,
            is_ready_for_automation=is_ready,
            notes=payload.notes,
            failure_reason=None,
        )

    def list_applications(self, user_id):
        return self.repository.list_by_user_id(user_id)