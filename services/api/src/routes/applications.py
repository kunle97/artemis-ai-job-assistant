"""
Applications API routes.

Thin HTTP endpoints for creating and listing the authenticated user's applications.
"""

from celery import Celery
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from src.core.config import settings
from src.deps.auth import get_current_user
from src.domain.applications.factory import build_pipeline_service
from src.domain.applications.repository import ApplicationRepository
from src.domain.applications.schemas import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationRunDispatchRead,
)
from src.domain.applications.service import ApplicationService
from src.domain.jobs.repository import JobRepository
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.resume.repository import ResumeRepository
from src.infrastructure.db.session import get_db

router = APIRouter(prefix="/applications", tags=["applications"])
celery_dispatch = Celery(
    "artemis_api_dispatch",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


def _build_application_service(db: Session) -> ApplicationService:
    return ApplicationService(
        repository=ApplicationRepository(db),
        job_repository=JobRepository(db),
        profile_repository=CandidateProfileRepository(db),
        resume_repository=ResumeRepository(db),
    )


def _build_pipeline_service(db: Session):
    return build_pipeline_service(db)


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


@router.post("/{application_id}/authorize", response_model=ApplicationRead)
def authorize_submission(
    application_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_application_service(db)

    try:
        return service.authorize_submission(user_id=current_user.id, application_id=application_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{application_id}/run", response_model=ApplicationRunDispatchRead)
def run_application_pipeline(
    application_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_application_service(db)

    try:
        service.get_application(user_id=current_user.id, application_id=application_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    async_result = celery_dispatch.send_task(
        "run_application_pipeline_async",
        kwargs={
            "user_id": str(current_user.id),
            "application_id": str(application_id),
        },
    )
    return ApplicationRunDispatchRead(
        application_id=application_id,
        task_id=async_result.id,
        status="queued",
    )


@router.post("/{application_id}/submit", response_model=ApplicationRead)
def submit_application(
    application_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_pipeline_service(db)

    try:
        return service.submit_application(user_id=current_user.id, application_id=application_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
