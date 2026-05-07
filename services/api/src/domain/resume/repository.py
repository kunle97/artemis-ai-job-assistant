"""
Resume domain repository.

Encapsulates database access for resume records.
"""

from sqlalchemy.orm import Session

from src.domain.resume.models import Resume


class ResumeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **resume_data):
        resume = Resume(**resume_data)
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def get_by_user_id(self, user_id):
        return (
            self.db.query(Resume)
            .filter(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
            .all()
        )

    def get_by_id_and_user_id(self, resume_id, user_id):
        return (
            self.db.query(Resume)
            .filter(Resume.id == resume_id, Resume.user_id == user_id)
            .first()
        )

    def delete(self, resume):
        self.db.delete(resume)
        self.db.commit()