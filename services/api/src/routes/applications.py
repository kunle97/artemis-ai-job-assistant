"""
Applications API routes.

Thin HTTP endpoints for creating and listing the authenticated user's applications.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from src.deps.auth import get_current_user
from src.domain.applications.repository import ApplicationRepository
from src.domain.applications.schemas import ApplicationCreate, ApplicationRead
from src.domain.applications.service import ApplicationService
from src.domain.jobs.repository import JobRepository
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.resume.repository import ResumeRepository
from src.infrastructure.db.session import get_db

router = APIRouter(prefix="/applications", tags=["applications"])


def _build_application_service(db: Session) -> ApplicationService:
    return ApplicationService(
        repository=ApplicationRepository(db),
        job_repository=JobRepository(db),
        profile_repository=CandidateProfileRepository(db),
        resume_repository=ResumeRepository(db),
    )


@router.post("", response_model=ApplicationRead)
def create_application(
    payload: ApplicationCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_application_service(db)

    try:
        return service.create_application(user_id=current_user.id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=list[ApplicationRead])
def list_applications(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_application_service(db)
    return service.list_applications(current_user.id)


@router.get("/{application_id}", response_model=ApplicationRead)
def get_application(
    application_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_application_service(db)

    try:
        return service.get_application(user_id=current_user.id, application_id=application_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))