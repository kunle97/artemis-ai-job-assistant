"""
Application planning service.

Builds a pre-automation plan for a job application by resolving each
question/field into an answer or marking it for review.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.application_answers.resolution import ApplicationAnswerResolver
from src.domain.applications.readiness import ApplicationReadinessService


class ApplicationPlanningItem(BaseModel):
    """
    One planned field/question resolution result.
    """

    field_key: str
    question_text: str
    matched_question_key: str | None = None
    resolved_answer: str | None = None
    source: str
    needs_review: bool


class ApplicationPlanningRequest(BaseModel):
    """
    Incoming request to evaluate a set of questions/fields for an application.
    """

    application_id: UUID
    questions: list[str] = Field(default_factory=list)


class ApplicationPlanningResult(BaseModel):
    """
    Final structured plan for one application.
    """

    application_id: UUID
    readiness_status: Literal["ready", "needs_review"]
    missing_items: list[str] = Field(default_factory=list)
    items: list[ApplicationPlanningItem] = Field(default_factory=list)


class ApplicationPlanningService:
    """
    Build an action plan for an application before automation runs.
    """

    def __init__(
        self,
        readiness_service: ApplicationReadinessService,
        answer_resolver: ApplicationAnswerResolver,
    ):
        self.readiness_service = readiness_service
        self.answer_resolver = answer_resolver

    def build_plan(self, user_id, payload: ApplicationPlanningRequest) -> ApplicationPlanningResult:
        readiness = self.readiness_service.evaluate_application(
            user_id=user_id,
            application_id=payload.application_id,
        )

        items: list[ApplicationPlanningItem] = []

        for question_text in payload.questions:
            resolved = self.answer_resolver.resolve(
                user_id=user_id,
                question_text=question_text,
            )

            items.append(
                ApplicationPlanningItem(
                    field_key=self._derive_field_key(question_text),
                    question_text=question_text,
                    matched_question_key=resolved.matched_question_key,
                    resolved_answer=resolved.resolved_answer,
                    source=resolved.source,
                    needs_review=resolved.needs_review,
                )
            )

        any_item_needs_review = any(item.needs_review for item in items)
        readiness_status = "ready"
        if readiness.missing_items or any_item_needs_review:
            readiness_status = "needs_review"

        return ApplicationPlanningResult(
            application_id=payload.application_id,
            readiness_status=readiness_status,
            missing_items=readiness.missing_items,
            items=items,
        )

    def _derive_field_key(self, question_text: str) -> str:
        """
        Lightweight deterministic field key for debugging/tracing.
        """
        normalized = (
            question_text.strip()
            .lower()
            .replace("’", "'")
            .replace("?", "")
            .replace("*", "")
            .replace(" ", "_")
        )
        return normalized[:120]