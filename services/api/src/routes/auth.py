"""
Auth API routes.
"""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.deps.auth import get_current_user
from src.domain.auth.models import User
from src.domain.auth.repository import UserRepository
from src.domain.auth.schemas import UserCreate, UserLogin, UserRead
from src.domain.auth.service import AuthService
from src.infrastructure.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_service(db: Session) -> AuthService:
    return AuthService(UserRepository(db))


@router.post("/register", response_model=UserRead)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    service = _build_service(db)
    return service.register_user(payload)


@router.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    service = _build_service(db)
    return service.login_user(email=form_data.username, password=form_data.password)


@router.get("/session", response_model=UserRead)
def get_session(current_user: User = Depends(get_current_user)):
    return current_user