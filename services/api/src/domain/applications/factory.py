"""
Application pipeline service factory.

Builds a fully wired ApplicationPipelineService instance from a DB session
for use by API routes and worker tasks.
"""

from sqlalchemy.orm import Session

from src.core.config import settings
from src.domain.application_answers.intents.repository import ApplicationAnswerIntentRepository
from src.domain.application_answers.open_ended.default_provider import DefaultOpenEndedAnswerProvider
from src.domain.application_answers.open_ended.llm_provider import LLMOpenEndedAnswerProvider
from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.application_answers.resolution import ApplicationAnswerResolver
from src.domain.applications.pipeline_service import ApplicationPipelineService
from src.domain.applications.repository import ApplicationRepository
from src.domain.auth.repository import UserRepository
from src.domain.automation.fill import AutomationFillService
from src.domain.automation.planning.service import AutomationPlanningService
from src.domain.automation.service import AutomationService
from src.domain.jobs.repository import JobRepository
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.resume.repository import ResumeRepository
from src.integrations.automation.page_inspector import ApplicationPageInspector
from src.integrations.groq.client import GroqClient


def build_pipeline_service(db: Session) -> ApplicationPipelineService:
    """Construct and return a configured ApplicationPipelineService."""
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
