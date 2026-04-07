"""
Profile domain repository.

Encapsulates database operations for candidate profiles.
"""

from sqlalchemy.orm import Session

from src.domain.profile.models import CandidateProfile


class CandidateProfileRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id):
        return self.db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()

    def create(self, **profile_data):
        profile = CandidateProfile(**profile_data)
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def update(self, profile: CandidateProfile, **profile_data):
        for key, value in profile_data.items():
            setattr(profile, key, value)

        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile