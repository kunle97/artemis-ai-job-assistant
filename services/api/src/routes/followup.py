"""
Follow-up API routes.

Endpoints for retrieving follow-up recommendations for active applications.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.deps.auth import get_current_user
from src.infrastructure.db.session import get_db
from src.domain.applications.followup.schemas import FollowUpListResponse, FollowUpRead
from src.domain.applications.followup.service import FollowUpService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/applications", tags=["follow-ups"])


@router.get(
    "/follow-ups",
    response_model=FollowUpListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get follow-up recommendations",
    description="Returns overdue, urgent, and upcoming follow-ups for the authenticated user's active applications.",
)
def get_followups(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FollowUpListResponse:
    """
    Retrieve follow-up recommendations grouped by urgency.

    Returns:
        - overdue: Follow-ups past their due date
        - urgent: Follow-ups due within 1-2 days
        - upcoming: Future follow-ups
    """
    user_id = current_user.id

    try:
        service = FollowUpService(db)
        followup_data = service.get_followups_for_user(user_id)

        # Convert FollowUp models to FollowUpRead schemas
        overdue = [FollowUpRead.model_validate(f) for f in followup_data['overdue']]
        urgent = [FollowUpRead.model_validate(f) for f in followup_data['urgent']]
        upcoming = [FollowUpRead.model_validate(f) for f in followup_data['upcoming']]

        logger.info(
            f"Returning {len(overdue)} overdue, {len(urgent)} urgent, "
            f"{len(upcoming)} upcoming follow-ups for user {user_id}"
        )

        return FollowUpListResponse(
            overdue=overdue,
            urgent=urgent,
            upcoming=upcoming,
            total=followup_data['total'],
        )

    except Exception as e:
        logger.error(f"Error retrieving follow-ups for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve follow-ups",
        )
