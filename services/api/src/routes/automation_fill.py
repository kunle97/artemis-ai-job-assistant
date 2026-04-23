"""
Automation fill API routes.

Executes safe high-confidence field entry without submitting the form.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.deps.auth import get_current_user
from src.domain.application_answers.intents.repository import ApplicationAnswerIntentRepository
from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.auth.repository import UserRepository
from src.domain.automation.fill import (
    AutomationFillRequest,
    AutomationFillResult,
    AutomationFillService,
)
from src.domain.automation.planning.service import AutomationPlanningService
from src.domain.profile.repository import CandidateProfileRepository
from src.infrastructure.db.session import get_db

router = APIRouter(prefix="/automation-fill", tags=["automation-fill"])


def _build_service(db: Session) -> AutomationFillService:
    planning_service = AutomationPlanningService(
        user_repo=UserRepository(db),
        profile_repo=CandidateProfileRepository(db),
    )
    return AutomationFillService(planning_service=planning_service)


@router.post("", response_model=AutomationFillResult)
def fill_application_safely(
    payload: AutomationFillRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_service(db)
    return service.fill_safe_fields(user_id=current_user.id, payload=payload)