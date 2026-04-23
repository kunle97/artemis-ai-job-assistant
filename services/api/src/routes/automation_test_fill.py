"""
Automation test-fill route.

Runs inspect first, then immediately runs fill using the inspected fields.
"""

from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, Depends

from src.deps.auth import get_current_user
from src.domain.automation.fill import AutomationFillRequest, AutomationFillService
from src.domain.automation.service import AutomationService
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.auth.repository import UserRepository
from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.automation.planning.service import AutomationPlanningService
from src.infrastructure.db.session import get_db
from src.integrations.automation.page_inspector import ApplicationPageInspector

router = APIRouter(prefix="/automation", tags=["automation"])


class AutomationTestFillRequest(BaseModel):
    application_url: str
    resume_file_path: str | None = None


def _build_services(db):
    planning_service = AutomationPlanningService(
        user_repo=UserRepository(db),
        profile_repo=CandidateProfileRepository(db),
    )
    fill_service = AutomationFillService(planning_service=planning_service)
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
            resume_file_path=payload.resume_file_path,
        ),
    )

    return {
        "inspect": inspect_result,
        "fill": fill_result.model_dump(),
    }