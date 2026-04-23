"""
Auth service.
"""

from fastapi import HTTPException

from src.domain.auth.schemas import UserCreate
from src.integrations.auth.passwords import hash_password, verify_password
from src.integrations.auth.jwt import create_access_token


class AuthService:
    def __init__(self, repository):
        self.repository = repository

    def register_user(self, payload: UserCreate):
        existing_user = self.repository.get_by_email(payload.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists.")

        return self.repository.create(
            email=payload.email,
            password=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
        )

    def login_user(self, email: str, password: str):
        user = self.repository.get_by_email(email)
        if not user or not verify_password(password, user.password):
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        access_token = create_access_token(subject=str(user.id))
        return {
            "access_token": access_token,
            "token_type": "bearer",
        }