"""
Auth dependencies.

Provides reusable FastAPI dependencies for authentication.
"""

import uuid

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from src.domain.auth.repository import UserRepository
from src.infrastructure.db.session import get_db
from src.integrations.auth.jwt import decode_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Resolve the currently authenticated user from a bearer token.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        user_id_str = payload.get("sub")
        token_jti = payload.get("jti")
        if not user_id_str or not token_jti:
            raise credentials_exception

        if payload.get("type") != "access":
            raise credentials_exception

        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError) as exc:
        raise credentials_exception from exc

    repository = UserRepository(db)
    if repository.is_token_revoked(token_jti):
        raise credentials_exception
    user = repository.get_by_id(user_id)

    if not user:
        raise credentials_exception

    return user