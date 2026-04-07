"""
Auth domain service.

Contains user-related business logic and coordinates auth domain operations.
"""

from src.domain.auth.repository import UserRepository
from src.domain.auth.schemas import UserCreate, UserLogin
from src.integrations.auth.jwt import create_access_token


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

    def login_user(self, payload: UserLogin) -> str:
        user = self.repository.get_by_email(payload.email)
        if not user:
            raise ValueError("Invalid email or password.")

        # TODO: replace with hashed password check before production
        if user.password_hash != payload.password:
            raise ValueError("Invalid email or password.")

        return create_access_token(subject=str(user.id))