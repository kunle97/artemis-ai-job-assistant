"""
Application service.

Coordinates creation and retrieval of user job application records.
"""

import logging

from src.domain.applications.constants import (
    APPLICATION_STATUS_QUEUED,
    APPLICATION_STATUS_NEEDS_REVIEW,
    APPLICATION_STATUS_SUBMITTED,
    POST_SUBMISSION_LIFECYCLE_STATUSES,
    ALL_VALID_LIFECYCLE_STATUSES,
)
from src.domain.applications.repository import ApplicationRepository
from src.domain.applications.schemas import ApplicationCreate
from src.domain.jobs.repository import JobRepository
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.resume.repository import ResumeRepository


logger = logging.getLogger(__name__)


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
        logger.info("[ApplicationService] Create application start")

        existing = self.repository.get_by_user_and_job(user_id=user_id, job_id=payload.job_id)
        if existing:
            raise ValueError("You already created an application for this job.")

        job = self.job_repository.get_by_id(payload.job_id)
        if not job:
            raise ValueError("Job not found.")

        profile = self.profile_repository.get_by_user_id(user_id)
        resumes = self.resume_repository.get_by_user_id(user_id)

        selected_resume = None
        if payload.resume_id:
            selected_resume = self.resume_repository.get_by_id_and_user_id(
                payload.resume_id,
                user_id,
            )
            if not selected_resume:
                raise ValueError("Resume not found.")
        elif resumes:
            # Default to most recently uploaded resume when not explicitly provided.
            selected_resume = resumes[0]

        is_ready = bool(profile and selected_resume)
        status = APPLICATION_STATUS_QUEUED if is_ready else APPLICATION_STATUS_NEEDS_REVIEW

        # Inherit the user's auto-submit preference from profile when available.
        auto_submit = bool(profile and getattr(profile, "auto_submit", False))
        manual_review_required = not auto_submit

        application = self.repository.create(
            user_id=user_id,
            job_id=payload.job_id,
            resume_id=getattr(selected_resume, "id", None),
            status=status,
            is_ready_for_automation=is_ready,
            manual_review_required=manual_review_required,
            notes=payload.notes,
            failure_reason=None,
        )

        logger.info(
            "[ApplicationService] Create application complete "
            f"application_id={application.id} ready={is_ready}"
        )
        return application

    def get_application(self, user_id, application_id):
        logger.info(f"[ApplicationService] Fetch application start application_id={application_id}")

        application = self.repository.get_by_id(application_id)
        if not application:
            raise ValueError("Application not found.")

        if str(application.user_id) != str(user_id):
            raise ValueError("Application does not belong to the current user.")

        logger.info(f"[ApplicationService] Fetch application complete application_id={application_id}")
        return application

    def list_applications(self, user_id):
        return self.repository.list_by_user_id(user_id)

    def authorize_submission(self, user_id, application_id):
        logger.info(f"[ApplicationService] Authorize submission start application_id={application_id}")

        application = self.repository.get_by_id(application_id)
        if not application:
            raise ValueError("Application not found.")

        if str(application.user_id) != str(user_id):
            raise PermissionError("You are not allowed to authorize this application.")

        application = self.repository.update_fields(application_id, is_authorized_to_submit=True)

        logger.info(
            f"[ApplicationService] Authorize submission complete application_id={application_id}"
        )
        return application

    def update_lifecycle_status(self, user_id, application_id, new_status: str):
        """Allow the user to manually set a post-submission lifecycle status.

        Only statuses in POST_SUBMISSION_LIFECYCLE_STATUSES are accepted.
        The application must already be in a submitted or post-submission state.
        """
        logger.info(
            f"[ApplicationService] Update lifecycle status start "
            f"application_id={application_id} new_status={new_status}"
        )

        if new_status not in ALL_VALID_LIFECYCLE_STATUSES:
            valid = ", ".join(sorted(ALL_VALID_LIFECYCLE_STATUSES))
            raise ValueError(
                f"'{new_status}' is not a valid lifecycle status. Valid options: {valid}"
            )

        application = self.repository.get_by_id(application_id)
        if not application:
            raise ValueError("Application not found.")

        if str(application.user_id) != str(user_id):
            raise PermissionError("You are not allowed to update this application.")

        allowed_source_statuses = POST_SUBMISSION_LIFECYCLE_STATUSES | {APPLICATION_STATUS_SUBMITTED}
        if application.status not in allowed_source_statuses:
            raise ValueError(
                f"Lifecycle status can only be updated after the application has been submitted "
                f"(current status: '{application.status}')."
            )

        application = self.repository.update_fields(application_id, status=new_status)

        logger.info(
            f"[ApplicationService] Update lifecycle status complete "
            f"application_id={application_id} status={new_status}"
        )
        return application