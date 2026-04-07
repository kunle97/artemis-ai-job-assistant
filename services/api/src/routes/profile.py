"""
Profile API routes.

Thin HTTP endpoints for creating and retrieving the authenticated user's
candidate profile.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.deps.auth import get_current_user
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.profile.schemas import (
    CandidateProfileCreate,
    CandidateProfileRead,
    CandidateProfileWrite,
)
from src.domain.profile.service import CandidateProfileService
from src.infrastructure.db.session import get_db

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("", response_model=CandidateProfileRead)
def create_profile(
    payload: CandidateProfileWrite,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a profile for the authenticated user.
    """
    repository = CandidateProfileRepository(db)
    service = CandidateProfileService(repository)

    safe_payload = CandidateProfileCreate(
        user_id=current_user.id,
        **payload.model_dump(),
    )

    try:
        return service.create_profile(safe_payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=CandidateProfileRead)
def get_profile(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the authenticated user's profile.
    """
    repository = CandidateProfileRepository(db)
    service = CandidateProfileService(repository)

    profile = service.get_profile_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    return profile