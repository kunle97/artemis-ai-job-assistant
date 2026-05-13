"""
Application answer generation API routes.

Provides an endpoint that can use LLM-backed open-ended generation when the
saved/intents resolver has no answer.
"""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.config import settings
from src.deps.auth import get_current_user
from src.domain.application_answers.intents.repository import ApplicationAnswerIntentRepository
from src.domain.application_answers.open_ended.default_provider import DefaultOpenEndedAnswerProvider
from src.domain.application_answers.open_ended.llm_provider import LLMOpenEndedAnswerProvider
from src.domain.application_answers.open_ended.service import OpenEndedApplicationAnswerService
from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.application_answers.resolution import ApplicationAnswerResolver
from src.domain.auth.repository import UserRepository
from src.domain.profile.repository import CandidateProfileRepository
from src.infrastructure.db.session import get_db
from src.integrations.groq.client import GroqClient

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/application-answer-generation",
    tags=["application-answer-generation"],
)


class GenerateApplicationAnswerRequest(BaseModel):
    question_text: str
    page_title: str | None = None
    job_context: str | None = None


class GenerateApplicationAnswerResponse(BaseModel):
    answer_text: str | None
    source: str
    needs_review: bool
    intent_key: str | None = None


def _build_service(db: Session) -> OpenEndedApplicationAnswerService:
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
        provider = LLMOpenEndedAnswerProvider(
            resolver=resolver,
            llm_client=groq_client,
            answer_repo=answer_repo,
        )
    else:
        provider = DefaultOpenEndedAnswerProvider(resolver=resolver)

    return OpenEndedApplicationAnswerService(
        user_repo=UserRepository(db),
        profile_repo=profile_repo,
        provider=provider,
    )


@router.post("", response_model=GenerateApplicationAnswerResponse)
def generate_application_answer(
    payload: GenerateApplicationAnswerRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        "[ApplicationAnswerGenerationRoute] Generate request user_id=%s question_text=%s",
        current_user.id,
        (payload.question_text or "")[:180],
    )
    service = _build_service(db)
    result = service.generate(
        user_id=current_user.id,
        question_text=payload.question_text,
        page_title=payload.page_title,
        job_context=payload.job_context,
    )
    logger.info(
        "[ApplicationAnswerGenerationRoute] Generate result user_id=%s source=%s resolved=%s intent_key=%s",
        current_user.id,
        result.source,
        bool(result.answer_text),
        result.intent_key,
    )
    return GenerateApplicationAnswerResponse(
        answer_text=result.answer_text,
        source=result.source,
        needs_review=result.needs_review,
        intent_key=result.intent_key,
    )