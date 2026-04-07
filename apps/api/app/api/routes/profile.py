"""
Profile API routes.

Thin HTTP endpoints for creating and retrieving candidate profiles.
Business logic should remain in the profile service layer.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.infrastructure.db.session import get_db
from app.domains.profile.repository import CandidateProfileRepository
from app.domains.profile.schemas import CandidateProfileCreate, CandidateProfileRead
from app.domains.profile.service import CandidateProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("", response_model=CandidateProfileRead)
def create_profile(payload: CandidateProfileCreate, db: Session = Depends(get_db)):
    repository = CandidateProfileRepository(db)
    service = CandidateProfileService(repository)

    try:
        return service.create_profile(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{user_id}", response_model=CandidateProfileRead)
def get_profile(user_id: UUID, db: Session = Depends(get_db)):
    repository = CandidateProfileRepository(db)
    service = CandidateProfileService(repository)

    profile = service.get_profile_by_user_id(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    return profile