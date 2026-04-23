"""
Automation planning API routes.

Builds a fill plan from inspected form fields before any browser actions run.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.deps.auth import get_current_user
from src.domain.application_answers.intents.repository import ApplicationAnswerIntentRepository
from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.auth.repository import UserRepository
from src.domain.automation.planning.models import (
    AutomationFillPlanRequest,
    AutomationFillPlan,
)
from src.domain.automation.planning.service import AutomationPlanningService
from src.domain.profile.repository import CandidateProfileRepository
from src.infrastructure.db.session import get_db

router = APIRouter(prefix="/automation-planning", tags=["automation-planning"])


def _build_service(db: Session) -> AutomationPlanningService:
    return AutomationPlanningService(
        user_repo=UserRepository(db),
        profile_repo=CandidateProfileRepository(db),
    )


@router.post("", response_model=AutomationFillPlan)
def build_automation_fill_plan(
    payload: AutomationFillPlanRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_service(db)
    return service.build_fill_plan(user_id=current_user.id, payload=payload)