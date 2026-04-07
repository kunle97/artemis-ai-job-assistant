"""
Auth domain service.

Contains user-related business logic and coordinates auth domain operations.
"""

from app.domains.auth.repository import UserRepository
from app.domains.auth.schemas import UserCreate


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def create_user(self, payload: UserCreate):
        existing_user = self.repository.get_by_email(payload.email)
        if existing_user:
            raise ValueError("A user with this email already exists.")

        # Password hashing will be added later.
        password_hash = payload.password

        return self.repository.create(
            email=payload.email,
            password_hash=password_hash,
            full_name=payload.full_name,
        )

    def get_user(self, user_id):
        return self.repository.get_by_id(user_id)