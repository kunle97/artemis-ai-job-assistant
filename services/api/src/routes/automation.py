"""
Automation API routes.

Provides endpoints for application page inspection.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.deps.auth import get_current_user
from src.domain.automation.schemas import (
    ApplicationPageIntakeRequest,
    ApplicationPageIntakeResult,
)
from src.domain.automation.service import AutomationService
from src.infrastructure.db.session import get_db

router = APIRouter(prefix="/automation", tags=["automation"])


def _build_service(db: Session) -> AutomationService:
    return AutomationService()


@router.post("/inspect", response_model=ApplicationPageIntakeResult)
def inspect_application_page(
    payload: ApplicationPageIntakeRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_service(db)
    return service.inspect_application_page(payload)