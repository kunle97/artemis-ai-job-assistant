"""
Automation fill API routes.

Executes safe high-confidence field entry without submitting the form.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.config import settings
from src.deps.auth import get_current_user
from src.domain.application_answers.intents.repository import ApplicationAnswerIntentRepository
from src.domain.application_answers.open_ended.default_provider import DefaultOpenEndedAnswerProvider
from src.domain.application_answers.open_ended.llm_provider import LLMOpenEndedAnswerProvider
from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.application_answers.resolution import ApplicationAnswerResolver
from src.domain.auth.repository import UserRepository
from src.domain.applications.repository import ApplicationRepository
from src.domain.automation.fill import (
    AutomationFillRequest,
    AutomationFillResult,
    AutomationFillService,
)
from src.domain.automation.planning.service import AutomationPlanningService
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.resume.repository import ResumeRepository
from src.infrastructure.db.session import get_db
from src.integrations.groq.client import GroqClient

router = APIRouter(prefix="/automation-fill", tags=["automation-fill"])


def _build_service(db: Session) -> AutomationFillService:
    profile_repo = CandidateProfileRepository(db)
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
        open_ended_provider = LLMOpenEndedAnswerProvider(
            resolver=resolver,
            llm_client=groq_client,
            answer_repo=answer_repo,
        )
    else:
        open_ended_provider = DefaultOpenEndedAnswerProvider(resolver=resolver)

    planning_service = AutomationPlanningService(
        user_repo=UserRepository(db),
        profile_repo=profile_repo,
        open_ended_provider=open_ended_provider,
    )
    return AutomationFillService(
        planning_service=planning_service,
        application_repository=ApplicationRepository(db),
        resume_repository=ResumeRepository(db),
    )


@router.post("", response_model=AutomationFillResult)
def fill_application_safely(
    payload: AutomationFillRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_service(db)
    try:
        return service.fill_safe_fields(user_id=current_user.id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))