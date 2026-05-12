"""
Resume tailoring repository.

Loads application, resume, profile, and job records needed for tailoring.
"""

from src.domain.applications.repository import ApplicationRepository
from src.domain.jobs.repository import JobRepository
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.resume.repository import ResumeRepository


class ResumeTailoringRepository:
    """Data access wrapper for resume tailoring context."""

    def __init__(self, *, application_repository: ApplicationRepository, resume_repository: ResumeRepository, profile_repository: CandidateProfileRepository, job_repository: JobRepository):
        self.application_repository = application_repository
        self.resume_repository = resume_repository
        self.profile_repository = profile_repository
        self.job_repository = job_repository

    def get_application(self, application_id):
        return self.application_repository.get_by_id(application_id)

    def get_resume_by_user(self, user_id, resume_id):
        return self.resume_repository.get_by_id_and_user_id(resume_id, user_id)

    def get_primary_resume_for_user(self, user_id):
        return self.resume_repository.get_primary_by_user_id(user_id)

    def get_latest_resume_for_user(self, user_id):
        resumes = self.resume_repository.get_by_user_id(user_id)
        return resumes[0] if resumes else None

    def get_profile_for_user(self, user_id):
        return self.profile_repository.get_by_user_id(user_id)

    def get_job(self, job_id):
        return self.job_repository.get_by_id(job_id)
