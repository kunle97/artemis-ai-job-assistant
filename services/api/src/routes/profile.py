"""
Candidate profile routes.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.deps.auth import get_current_user
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.profile.schemas import (
    CandidateProfileResponse,
    CandidateProfileUpsertRequest,
)
from src.infrastructure.db.session import get_db

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=CandidateProfileResponse)
def get_profile(current_user=Depends(get_current_user), db=Depends(get_db)):
    repo = CandidateProfileRepository(db)
    profile = repo.get_or_create_by_user_id(current_user.id)
    return profile


@router.post("", response_model=CandidateProfileResponse)
def create_or_update_profile(
    payload: CandidateProfileUpsertRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    repo = CandidateProfileRepository(db)
    profile = repo.upsert_by_user_id(current_user.id, payload)
    return profile


@router.put("", response_model=CandidateProfileResponse)
def update_profile(
    payload: CandidateProfileUpsertRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    repo = CandidateProfileRepository(db)
    profile = repo.upsert_by_user_id(current_user.id, payload)
    return profile