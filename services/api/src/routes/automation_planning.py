"""
Automation planning API routes.

Builds a fill plan from inspected form fields before any browser actions run.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.config import settings
from src.deps.auth import get_current_user
from src.domain.application_answers.intents.repository import ApplicationAnswerIntentRepository
from src.domain.application_answers.open_ended.default_provider import DefaultOpenEndedAnswerProvider
from src.domain.application_answers.open_ended.llm_provider import LLMOpenEndedAnswerProvider
from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.application_answers.resolution import ApplicationAnswerResolver
from src.domain.auth.repository import UserRepository
from src.domain.automation.planning.models import (
    AutomationFillPlanRequest,
    AutomationFillPlan,
)
from src.domain.automation.planning.service import AutomationPlanningService
from src.domain.profile.repository import CandidateProfileRepository
from src.infrastructure.db.session import get_db
from src.integrations.groq.client import GroqClient

router = APIRouter(prefix="/automation-planning", tags=["automation-planning"])
logger = logging.getLogger(__name__)


def _build_open_ended_provider(db: Session, profile_repo: CandidateProfileRepository):
    answer_repo = ApplicationAnswerRepository(db)
    intent_repo = ApplicationAnswerIntentRepository(db)
    resolver = ApplicationAnswerResolver(
        answer_repository=answer_repo,
        intent_repository=intent_repo,
        profile_repository=profile_repo,
    )
    if settings.groq_api_key:
        groq_client = GroqClient(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
        )
        return LLMOpenEndedAnswerProvider(
            resolver=resolver,
            llm_client=groq_client,
            answer_repo=answer_repo,
        )
    return DefaultOpenEndedAnswerProvider(resolver=resolver)


def _build_service(db: Session) -> AutomationPlanningService:
    profile_repo = CandidateProfileRepository(db)
    answer_repo = ApplicationAnswerRepository(db)
    intent_repo = ApplicationAnswerIntentRepository(db)
    resolver = ApplicationAnswerResolver(
        answer_repository=answer_repo,
        intent_repository=intent_repo,
        profile_repository=profile_repo,
    )
    open_ended_provider = _build_open_ended_provider(db, profile_repo)
    return AutomationPlanningService(
        user_repo=UserRepository(db),
        profile_repo=profile_repo,
        answer_resolver=resolver,
        open_ended_provider=open_ended_provider,
    )


@router.post("", response_model=AutomationFillPlan)
def build_automation_fill_plan(
    payload: AutomationFillPlanRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        "[AutomationPlanningRoute] build start user_id=%s url=%s inspected_fields=%s",
        current_user.id,
        payload.application_url,
        len(payload.inspected_fields),
    )
    service = _build_service(db)
    result = service.build_fill_plan(user_id=current_user.id, payload=payload)
    logger.info(
        "[AutomationPlanningRoute] build complete user_id=%s url=%s planned_fields=%s",
        current_user.id,
        payload.application_url,
        len(result.fields),
    )
    return result