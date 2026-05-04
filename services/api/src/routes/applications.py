"""
Applications API routes.

Thin HTTP endpoints for creating and listing the authenticated user's applications.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from src.core.config import settings
from src.deps.auth import get_current_user
from src.domain.application_answers.intents.repository import ApplicationAnswerIntentRepository
from src.domain.application_answers.open_ended.default_provider import DefaultOpenEndedAnswerProvider
from src.domain.application_answers.open_ended.llm_provider import LLMOpenEndedAnswerProvider
from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.application_answers.resolution import ApplicationAnswerResolver
from src.domain.applications.pipeline_service import ApplicationPipelineService
from src.domain.applications.repository import ApplicationRepository
from src.domain.applications.schemas import ApplicationCreate, ApplicationRead
from src.domain.applications.service import ApplicationService
from src.domain.auth.repository import UserRepository
from src.domain.automation.fill import AutomationFillService
from src.domain.automation.planning.service import AutomationPlanningService
from src.domain.automation.service import AutomationService
from src.domain.jobs.repository import JobRepository
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.resume.repository import ResumeRepository
from src.infrastructure.db.session import get_db
from src.integrations.automation.page_inspector import ApplicationPageInspector
from src.integrations.groq.client import GroqClient

router = APIRouter(prefix="/applications", tags=["applications"])


def _build_application_service(db: Session) -> ApplicationService:
    return ApplicationService(
        repository=ApplicationRepository(db),
        job_repository=JobRepository(db),
        profile_repository=CandidateProfileRepository(db),
        resume_repository=ResumeRepository(db),
    )


def _build_pipeline_service(db: Session) -> ApplicationPipelineService:
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
    fill_service = AutomationFillService(
        planning_service=planning_service,
        application_repository=ApplicationRepository(db),
        resume_repository=ResumeRepository(db),
    )
    return ApplicationPipelineService(
        application_repo=ApplicationRepository(db),
        job_repo=JobRepository(db),
        automation_service=AutomationService(page_inspector=ApplicationPageInspector()),
        planning_service=planning_service,
        fill_service=fill_service,
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


@router.post("/{application_id}/run", response_model=ApplicationRead)
def run_application_pipeline(
    application_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_pipeline_service(db)

    try:
        return service.run_pipeline(user_id=current_user.id, application_id=application_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


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
