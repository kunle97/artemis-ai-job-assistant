"""
Application answer resolution API routes.

Provides an endpoint to resolve a raw question into the best available answer.
"""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.deps.auth import get_current_user
from src.domain.application_answers.intents.repository import ApplicationAnswerIntentRepository
from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.application_answers.resolution import (
    ApplicationAnswerResolver,
    ResolvedApplicationAnswer,
)
from src.domain.profile.repository import CandidateProfileRepository
from src.infrastructure.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/application-answer-resolution",
    tags=["application-answer-resolution"],
)


class ResolveApplicationAnswerRequest(BaseModel):
    question_text: str


def _build_resolver(db: Session) -> ApplicationAnswerResolver:
    return ApplicationAnswerResolver(
        answer_repository=ApplicationAnswerRepository(db),
        intent_repository=ApplicationAnswerIntentRepository(db),
        profile_repository=CandidateProfileRepository(db),
    )


@router.post("", response_model=ResolvedApplicationAnswer)
def resolve_application_answer(
    payload: ResolveApplicationAnswerRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resolver = _build_resolver(db)
    logger.info(
        "[ApplicationAnswerResolutionRoute] Resolve request user_id=%s question_text=%s",
        current_user.id,
        (payload.question_text or "")[:180],
    )
    result = resolver.resolve(user_id=current_user.id, question_text=payload.question_text)
    logger.info(
        "[ApplicationAnswerResolutionRoute] Resolve result user_id=%s source=%s resolved=%s intent_key=%s",
        current_user.id,
        result.source,
        bool(result.resolved_answer),
        result.intent_key,
    )
    return result