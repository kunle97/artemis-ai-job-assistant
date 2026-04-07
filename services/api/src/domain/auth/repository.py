"""
Auth domain repository.

Encapsulates database access for user records so route handlers and services
do not talk to the ORM directly.
"""

from sqlalchemy.orm import Session

from src.domain.auth.models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id):
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()

    def create(self, email: str, password_hash: str | None = None, full_name: str | None = None):
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user