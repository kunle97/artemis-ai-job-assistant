"""
Auth service.
"""

import logging

from fastapi import HTTPException
from jose import JWTError

logger = logging.getLogger(__name__)

from datetime import UTC, datetime, timedelta

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

        # Rotate: revoke old refresh token, issue new access + refresh pair.
        old_exp = payload.get("exp")
        old_expires_at = datetime.fromtimestamp(old_exp, tz=UTC) if old_exp else None
        self.repository.revoke_token(jti, expires_at=old_expires_at)

        new_access_token = create_access_token(subject=subject)
        new_refresh_token = create_refresh_token(subject=subject)
        logger.info("refresh_access_token: rotated subject=%s old_jti=%s", subject, jti)
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    def revoke_tokens(self, access_token: str, refresh_token: str | None = None):
        """Revoke access token and optionally the refresh token on logout."""
        logger.info("revoke_tokens: start")

        try:
            access_payload = decode_token(access_token)
        except JWTError as exc:
            logger.warning("revoke_tokens: invalid access token")
            raise HTTPException(status_code=401, detail="Invalid token.") from exc

        access_jti = access_payload.get("jti")
        if not access_jti:
            raise HTTPException(status_code=401, detail="Invalid token.")

        if not self.repository.is_token_revoked(access_jti):
            access_exp = access_payload.get("exp")
            access_expires_at = datetime.fromtimestamp(access_exp, tz=UTC) if access_exp else None
            self.repository.revoke_token(access_jti, expires_at=access_expires_at)
            logger.info("revoke_tokens: access token revoked jti=%s", access_jti)
        else:
            logger.info("revoke_tokens: access token already revoked jti=%s", access_jti)

        if refresh_token:
            try:
                refresh_payload = decode_token(refresh_token)
            except JWTError:
                logger.warning("revoke_tokens: invalid refresh token provided on logout — ignoring")
                return

            if refresh_payload.get("type") != "refresh":
                logger.warning("revoke_tokens: wrong type for refresh token on logout — ignoring")
                return

            refresh_jti = refresh_payload.get("jti")
            if refresh_jti and not self.repository.is_token_revoked(refresh_jti):
                refresh_exp = refresh_payload.get("exp")
                refresh_expires_at = (
                    datetime.fromtimestamp(refresh_exp, tz=UTC) if refresh_exp else None
                )
                self.repository.revoke_token(refresh_jti, expires_at=refresh_expires_at)
                logger.info("revoke_tokens: refresh token revoked jti=%s", refresh_jti)