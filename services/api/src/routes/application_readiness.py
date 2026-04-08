"""
Application readiness API routes.

Provides endpoints to evaluate whether applications are ready for automation.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.deps.auth import get_current_user
from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.applications.readiness import (
    ApplicationReadinessResult,
    ApplicationReadinessService,
)
from src.domain.applications.repository import ApplicationRepository
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.resume.repository import ResumeRepository
from src.infrastructure.db.session import get_db

router = APIRouter(
    prefix="/application-readiness",
    tags=["application-readiness"],
)


def _build_service(db: Session) -> ApplicationReadinessService:
    return ApplicationReadinessService(
        application_repository=ApplicationRepository(db),
        profile_repository=CandidateProfileRepository(db),
        resume_repository=ResumeRepository(db),
        application_answer_repository=ApplicationAnswerRepository(db),
    )


@router.get("", response_model=list[ApplicationReadinessResult])
def evaluate_my_applications(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_service(db)
    return service.evaluate_all_for_user(current_user.id)


@router.get("/{application_id}", response_model=ApplicationReadinessResult)
def evaluate_one_application(
    application_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_service(db)

    try:
        return service.evaluate_application(
            user_id=current_user.id,
            application_id=application_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))