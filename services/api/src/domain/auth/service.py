"""
Auth service.
"""

import logging

from fastapi import HTTPException
from jose import JWTError

logger = logging.getLogger(__name__)

from src.domain.auth.schemas import UserCreate
from src.integrations.auth.passwords import (
    dummy_verify_password,
    hash_password,
    verify_password,
)
from src.integrations.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)


class AuthService:
    def __init__(self, repository):
        self.repository = repository

    def register_user(self, payload: UserCreate):
        logger.info("register_user: start email=%s", payload.email)
        existing_user = self.repository.get_by_email(payload.email)
        if existing_user:
            logger.warning("register_user: duplicate email=%s", payload.email)
            raise HTTPException(status_code=400, detail="User already exists.")

        user = self.repository.create(
            email=payload.email,
            password=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
        logger.info("register_user: complete user_id=%s", user.id)
        return user

    def login_user(self, email: str, password: str):
        logger.info("login_user: start email=%s", email)
        user = self.repository.get_by_email(email)
        if not user or not user.password:
            dummy_verify_password()
            logger.warning("login_user: unknown email=%s", email)
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        if not verify_password(password, user.password):
            logger.warning("login_user: bad password user_id=%s", user.id)
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        logger.info("login_user: complete user_id=%s", user.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def refresh_access_token(self, refresh_token: str):
        logger.info("refresh_access_token: start")
        try:
            payload = decode_token(refresh_token)
        except JWTError as exc:
            logger.warning("refresh_access_token: invalid token")
            raise HTTPException(status_code=401, detail="Invalid refresh token.") from exc

        if payload.get("type") != "refresh":
            logger.warning("refresh_access_token: wrong token type")
            raise HTTPException(status_code=401, detail="Invalid refresh token.")

        jti = payload.get("jti")
        if not jti or self.repository.is_token_revoked(jti):
            logger.warning("refresh_access_token: revoked jti=%s", jti)
            raise HTTPException(status_code=401, detail="Refresh token has been revoked.")

        subject = payload.get("sub")
        if not subject:
            raise HTTPException(status_code=401, detail="Invalid refresh token.")

        logger.info("refresh_access_token: complete subject=%s", subject)
        return {
            "access_token": create_access_token(subject=subject),
            "token_type": "bearer",
        }

    def revoke_access_token(self, access_token: str):
        logger.info("revoke_access_token: start")
        try:
            payload = decode_token(access_token)
        except JWTError as exc:
            logger.warning("revoke_access_token: invalid token")
            raise HTTPException(status_code=401, detail="Invalid token.") from exc

        jti = payload.get("jti")
        if not jti:
            raise HTTPException(status_code=401, detail="Invalid token.")

        if not self.repository.is_token_revoked(jti):
            self.repository.revoke_token(jti)
            logger.info("revoke_access_token: token revoked jti=%s", jti)
        else:
            logger.info("revoke_access_token: token already revoked jti=%s", jti)