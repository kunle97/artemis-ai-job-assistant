from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.deps.auth import get_current_user
from src.domain.application_answers.intents.repository import ApplicationAnswerIntentRepository
from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.application_answers.resolution import ApplicationAnswerResolver
from src.domain.auth.repository import UserRepository
from src.domain.applications.repository import ApplicationRepository
from src.domain.automation.fill.service import AutomationFillService
from src.domain.automation.manual_fill.models import AutomationManualFillRequest
from src.domain.automation.manual_fill.service import AutomationManualFillService
from src.domain.automation.planning.service import AutomationPlanningService
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.resume.repository import ResumeRepository
from src.domain.automation.service import AutomationService
from src.infrastructure.db.session import get_db
from src.integrations.automation.page_inspector import ApplicationPageInspector

router = APIRouter(prefix="/automation-manual-fill", tags=["automation-manual-fill"])


def _build_planning_service(db: Session) -> AutomationPlanningService:
    profile_repo = CandidateProfileRepository(db)
    answer_repo = ApplicationAnswerRepository(db)
    intent_repo = ApplicationAnswerIntentRepository(db)
    resolver = ApplicationAnswerResolver(
        answer_repository=answer_repo,
        intent_repository=intent_repo,
        profile_repository=profile_repo,
    )
    return AutomationPlanningService(
        user_repo=UserRepository(db),
        profile_repo=profile_repo,
        answer_resolver=resolver,
    )


@router.post("")
def manual_fill_application(
    payload: AutomationManualFillRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    planning_service = _build_planning_service(db)

    automation_service = AutomationService(
        page_inspector=ApplicationPageInspector()
    )

    fill_service = AutomationFillService(
        planning_service=planning_service,
        application_repository=ApplicationRepository(db),
        resume_repository=ResumeRepository(db),
    )

    manual_fill_service = AutomationManualFillService(
        automation_service=automation_service,
        fill_service=fill_service,
    )

    return manual_fill_service.manual_fill(
        user_id=current_user.id,
        payload=payload,
    )