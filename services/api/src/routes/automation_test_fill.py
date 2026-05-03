"""
Automation test-fill route.

Runs inspect first, then immediately runs fill using the inspected fields.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel
from fastapi import APIRouter, Depends

from src.core.config import settings
from src.deps.auth import get_current_user
from src.domain.application_answers.intents.repository import ApplicationAnswerIntentRepository
from src.domain.application_answers.open_ended.default_provider import DefaultOpenEndedAnswerProvider
from src.domain.application_answers.open_ended.llm_provider import LLMOpenEndedAnswerProvider
from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.application_answers.resolution import ApplicationAnswerResolver
from src.domain.automation.fill import AutomationFillRequest, AutomationFillService
from src.domain.automation.service import AutomationService
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.auth.repository import UserRepository
from src.domain.applications.repository import ApplicationRepository
from src.domain.resume.repository import ResumeRepository
from src.domain.automation.planning.service import AutomationPlanningService
from src.infrastructure.db.session import get_db
from src.integrations.automation.page_inspector import ApplicationPageInspector
from src.integrations.groq.client import GroqClient

router = APIRouter(prefix="/automation", tags=["automation"])


class AutomationTestFillRequest(BaseModel):
    application_url: str
    application_id: UUID | None = None
    resume_file_path: str | None = None


def _build_open_ended_provider(db, profile_repo):
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


def _build_services(db):
    profile_repo = CandidateProfileRepository(db)
    open_ended_provider = _build_open_ended_provider(db, profile_repo)
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
    automation_service = AutomationService(page_inspector=ApplicationPageInspector())
    return automation_service, fill_service


@router.post("/test-fill")
def test_fill_application(
    payload: AutomationTestFillRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    automation_service, fill_service = _build_services(db)

    inspect_result = automation_service.inspect_application_page(payload.application_url)

    fill_result = fill_service.fill_safe_fields(
        user_id=current_user.id,
        payload=AutomationFillRequest(
            application_url=payload.application_url,
            inspected_fields=inspect_result["fields"],
            application_id=payload.application_id,
            resume_file_path=payload.resume_file_path,
            page_title=inspect_result.get("title"),
            job_context=inspect_result.get("job_context"),
        ),
    )

    return {
        "inspect": inspect_result,
        "fill": fill_result.model_dump(),
    }