"""
Auth API routes.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.core.rate_limiter import limiter
from src.deps.auth import get_current_user
from src.deps.auth import oauth2_scheme
from src.domain.auth.models import User
from src.domain.auth.repository import UserRepository
from src.domain.auth.schemas import LogoutRequest, RefreshTokenRequest, UserCreate, UserRead
from src.domain.auth.service import AuthService
from src.infrastructure.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_service(db: Session) -> AuthService:
    return AuthService(UserRepository(db))


@router.post("/register", response_model=UserRead)
@limiter.limit("10/minute")
def register_user(
    request: Request,
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    _ = request
    service = _build_service(db)
    return service.register_user(payload)


@router.post("/login")
@limiter.limit("10/minute")
def login_user(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    _ = request
    service = _build_service(db)
    return service.login_user(email=form_data.username, password=form_data.password)


@router.post("/refresh")
def refresh_access_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    service = _build_service(db)
    return service.refresh_access_token(refresh_token=payload.refresh_token)


@router.post("/logout")
def logout_user(
    payload: LogoutRequest = None,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    service = _build_service(db)
    refresh_token = payload.refresh_token if payload else None
    service.revoke_tokens(access_token=token, refresh_token=refresh_token)
    return {"message": "Logged out successfully."}


@router.get("/session", response_model=UserRead)
def get_session(current_user: User = Depends(get_current_user)):
    return current_user