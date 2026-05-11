"""
Applications API routes.

Thin HTTP endpoints for creating and listing the authenticated user's applications.
"""

from celery import Celery
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from src.core.config import settings
from src.deps.auth import get_current_user
from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.applications.readiness import ApplicationReadinessService
from src.domain.applications.factory import build_pipeline_service
from src.domain.applications.repository import ApplicationRepository
from src.domain.applications.schemas import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationRunDispatchRead,
    ApplicationStatusRead,
    ApplicationLifecycleStatusUpdate,
)
from src.domain.applications.analytics.repository import ApplicationPatternRepository
from src.domain.applications.followup.repository import FollowUpRepository
from src.domain.applications.analytics.schemas import ApplicationPatternsResponse
from src.domain.applications.analytics.service import ApplicationPatternService
from src.domain.applications.service import ApplicationService
from src.domain.jobs.repository import JobRepository
from src.domain.jobs.repository import JobUserFeedRepository
from src.domain.jobs.scoring.repository import ApplicationScoreRepository
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
        job_user_feed_repository=JobUserFeedRepository(db),
        follow_up_repository=FollowUpRepository(db),
        application_score_repository=ApplicationScoreRepository(db),
        profile_repository=CandidateProfileRepository(db),
        resume_repository=ResumeRepository(db),
    )


def _build_pipeline_service(db: Session):
    return build_pipeline_service(db)


def _build_readiness_service(db: Session) -> ApplicationReadinessService:
    return ApplicationReadinessService(
        application_repository=ApplicationRepository(db),
        profile_repository=CandidateProfileRepository(db),
        resume_repository=ResumeRepository(db),
        application_answer_repository=ApplicationAnswerRepository(db),
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


@router.get("/patterns", response_model=ApplicationPatternsResponse)
def get_application_patterns(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return per-user application pattern analytics.

    Scoped exclusively to the authenticated user — no user_id query parameter
    is accepted. Returns an ``is_sufficient_data=False`` response when the
    user has fewer than the minimum threshold of meaningful applications.
    """
    pattern_repository = ApplicationPatternRepository(
        db=db,
        score_repository=ApplicationScoreRepository(db),
    )
    service = ApplicationPatternService(repository=pattern_repository)

    try:
        return service.compute_patterns(user_id=current_user.id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


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


@router.delete("/{application_id}", status_code=204)
def delete_application(
    application_id: UUID,
    restore_to_feed: bool = Query(default=True),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_application_service(db)

    try:
        service.delete_unsubmitted_application(
            user_id=current_user.id,
            application_id=application_id,
            restore_to_feed=restore_to_feed,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if detail == "Application not found." else 400
        raise HTTPException(status_code=status_code, detail=detail)


@router.get("/{application_id}/status", response_model=ApplicationStatusRead)
def get_application_status(
    application_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_application_service(db)
    readiness_service = _build_readiness_service(db)

    try:
        application = service.get_application(
            user_id=current_user.id,
            application_id=application_id,
        )
        readiness = readiness_service.evaluate_application(
            user_id=current_user.id,
            application_id=application_id,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if detail == "Application not found." else 403
        raise HTTPException(status_code=status_code, detail=detail)

    return ApplicationStatusRead(
        application_id=application.id,
        status=application.status,
        is_ready_for_automation=application.is_ready_for_automation,
        manual_review_required=application.manual_review_required,
        is_authorized_to_submit=application.is_authorized_to_submit,
        failure_reason=application.failure_reason,
        missing_items=readiness.missing_items,
        available_answer_keys=readiness.available_answer_keys,
    )


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


@router.post("/{application_id}/authorize-submit", response_model=ApplicationRead)
def authorize_submit_application(
    application_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return authorize_submission(application_id=application_id, current_user=current_user, db=db)


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


@router.patch("/{application_id}/lifecycle-status", response_model=ApplicationRead)
def update_lifecycle_status(
    application_id: UUID,
    payload: ApplicationLifecycleStatusUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_application_service(db)

    try:
        return service.update_lifecycle_status(
            user_id=current_user.id,
            application_id=application_id,
            new_status=payload.status,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

