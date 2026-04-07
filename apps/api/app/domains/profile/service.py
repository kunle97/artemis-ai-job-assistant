"""
Profile domain service.

Contains business logic for candidate profiles and coordinates profile-related operations.
"""

from app.domains.profile.repository import CandidateProfileRepository
from app.domains.profile.schemas import CandidateProfileCreate


class CandidateProfileService:
    def __init__(self, repository: CandidateProfileRepository):
        self.repository = repository

    def get_profile_by_user_id(self, user_id):
        return self.repository.get_by_user_id(user_id)

    def create_profile(self, payload: CandidateProfileCreate):
        existing_profile = self.repository.get_by_user_id(payload.user_id)
        if existing_profile:
            raise ValueError("This user already has a candidate profile.")

        return self.repository.create(**payload.model_dump())