"""
Automation API routes.

Provides endpoints for application page inspection.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.deps.auth import get_current_user
from src.domain.automation.schemas import (
    ApplicationPageIntakeRequest,
    ApplicationPageIntakeResult,
)
from src.domain.automation.service import AutomationService
from src.infrastructure.db.session import get_db
from src.integrations.automation.page_inspector import ApplicationPageInspector

router = APIRouter(prefix="/automation", tags=["automation"])
logger = logging.getLogger(__name__)


def _build_service(db: Session) -> AutomationService:
    return AutomationService(page_inspector=ApplicationPageInspector())


@router.post("/inspect", response_model=ApplicationPageIntakeResult)
def inspect_application_page(
    payload: ApplicationPageIntakeRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info("[AutomationRoute] inspect start user_id=%s url=%s", current_user.id, payload.application_url)
    service = _build_service(db)
    result = service.inspect_application_page(payload)
    field_count = len(result.get("fields", [])) if isinstance(result, dict) else len(result.fields)
    logger.info(
        "[AutomationRoute] inspect complete user_id=%s url=%s fields=%s",
        current_user.id,
        payload.application_url,
        field_count,
    )
    return result