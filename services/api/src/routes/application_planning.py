"""
Application planning API routes.

Provides an endpoint to generate a pre-automation plan for an application.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.deps.auth import get_current_user
from src.domain.application_answers.intents.repository import ApplicationAnswerIntentRepository
from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.application_answers.resolution import ApplicationAnswerResolver
from src.domain.applications.planning import (
    ApplicationPlanningRequest,
    ApplicationPlanningResult,
    ApplicationPlanningService,
)
from src.domain.applications.readiness import ApplicationReadinessService
from src.domain.applications.repository import ApplicationRepository
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.resume.repository import ResumeRepository
from src.infrastructure.db.session import get_db

router = APIRouter(
    prefix="/application-planning",
    tags=["application-planning"],
)


def _build_service(db: Session) -> ApplicationPlanningService:
    readiness_service = ApplicationReadinessService(
        application_repository=ApplicationRepository(db),
        profile_repository=CandidateProfileRepository(db),
        resume_repository=ResumeRepository(db),
        application_answer_repository=ApplicationAnswerRepository(db),
    )

    answer_resolver = ApplicationAnswerResolver(
        answer_repository=ApplicationAnswerRepository(db),
        intent_repository=ApplicationAnswerIntentRepository(db),
        profile_repository=CandidateProfileRepository(db),
    )

    return ApplicationPlanningService(
        readiness_service=readiness_service,
        answer_resolver=answer_resolver,
    )


@router.post("", response_model=ApplicationPlanningResult)
def build_application_plan(
    payload: ApplicationPlanningRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_service(db)

    try:
        return service.build_plan(user_id=current_user.id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))