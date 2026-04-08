"""
Application readiness service.

Evaluates whether an application has enough user data to move toward
automation and identifies what is missing.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.applications.repository import ApplicationRepository
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.resume.repository import ResumeRepository


class ApplicationReadinessResult(BaseModel):
    """
    Structured readiness result for one application.
    """

    application_id: UUID
    is_ready: bool
    missing_items: list[str] = Field(default_factory=list)
    available_answer_keys: list[str] = Field(default_factory=list)


class ApplicationReadinessService:
    """
    Evaluate application readiness based on user data completeness.
    """

    def __init__(
        self,
        application_repository: ApplicationRepository,
        profile_repository: CandidateProfileRepository,
        resume_repository: ResumeRepository,
        application_answer_repository: ApplicationAnswerRepository,
    ):
        self.application_repository = application_repository
        self.profile_repository = profile_repository
        self.resume_repository = resume_repository
        self.application_answer_repository = application_answer_repository

    def evaluate_application(self, user_id, application_id) -> ApplicationReadinessResult:
        application = self.application_repository.get_by_id(application_id)
        if not application:
            raise ValueError("Application not found.")

        if str(application.user_id) != str(user_id):
            raise ValueError("Application does not belong to the current user.")

        return self._build_result(user_id=user_id, application_id=application.id)

    def evaluate_all_for_user(self, user_id) -> list[ApplicationReadinessResult]:
        applications = self.application_repository.list_by_user_id(user_id)

        results = []
        for application in applications:
            results.append(
                self._build_result(user_id=user_id, application_id=application.id)
            )

        return results

    def _build_result(self, user_id, application_id) -> ApplicationReadinessResult:
        missing_items: list[str] = []

        profile = self.profile_repository.get_by_user_id(user_id)
        resumes = self.resume_repository.get_by_user_id(user_id)
        answers = self.application_answer_repository.list_by_user_id(user_id)

        if not profile:
            missing_items.append("candidate_profile")

        if not resumes:
            missing_items.append("resume")

        available_answer_keys = [answer.question_key for answer in answers]

        return ApplicationReadinessResult(
            application_id=application_id,
            is_ready=len(missing_items) == 0,
            missing_items=missing_items,
            available_answer_keys=available_answer_keys,
        )