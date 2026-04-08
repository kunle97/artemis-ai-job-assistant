"""
Application answer resolution service.

Resolves raw application questions into the best available answer source:
saved reusable answers first, then limited profile-based fallbacks.
"""

from __future__ import annotations

from pydantic import BaseModel

from src.domain.application_answers.matching.service import ApplicationAnswerMatcher
from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.profile.repository import CandidateProfileRepository


class ResolvedApplicationAnswer(BaseModel):
    """
    Structured answer resolution result for a raw question.
    """

    question_text: str
    matched_question_key: str | None = None
    resolved_answer: str | None = None
    source: str
    needs_review: bool


class ApplicationAnswerResolver:
    """
    Resolve raw application questions to saved or derived answers.
    """

    def __init__(
        self,
        answer_repository: ApplicationAnswerRepository,
        profile_repository: CandidateProfileRepository,
    ):
        self.answer_repository = answer_repository
        self.profile_repository = profile_repository
        self.matcher = ApplicationAnswerMatcher()

    def resolve(self, user_id, question_text: str) -> ResolvedApplicationAnswer:
        """
        Resolve a question for a user.
        """
        matched_question_key = self.matcher.match_question_to_key(question_text)

        if matched_question_key:
            saved_answer = self.answer_repository.get_by_user_and_key(
                user_id=user_id,
                question_key=matched_question_key,
            )
            if saved_answer:
                return ResolvedApplicationAnswer(
                    question_text=question_text,
                    matched_question_key=matched_question_key,
                    resolved_answer=saved_answer.answer_text,
                    source="saved_answer",
                    needs_review=False,
                )

            profile_answer = self._resolve_from_profile(
                user_id=user_id,
                question_key=matched_question_key,
            )
            if profile_answer:
                return ResolvedApplicationAnswer(
                    question_text=question_text,
                    matched_question_key=matched_question_key,
                    resolved_answer=profile_answer,
                    source="profile_fallback",
                    needs_review=False,
                )

        return ResolvedApplicationAnswer(
            question_text=question_text,
            matched_question_key=matched_question_key,
            resolved_answer=None,
            source="unresolved",
            needs_review=True,
        )

    def _resolve_from_profile(self, user_id, question_key: str) -> str | None:
        """
        Lightweight profile-based fallbacks for a few canonical question keys.
        """
        profile = self.profile_repository.get_by_user_id(user_id)
        if not profile:
            return None

        if question_key == "linkedin_url" and profile.linkedin_url:
            return profile.linkedin_url

        if question_key == "github_url" and profile.github_url:
            return profile.github_url

        if question_key == "current_title" and profile.current_title:
            return profile.current_title

        if question_key == "work_authorization_us" and profile.work_authorization:
            return profile.work_authorization

        if question_key == "salary_expectation":
            if profile.salary_target is not None:
                return str(profile.salary_target)
            if profile.salary_min is not None:
                return str(profile.salary_min)

        return None