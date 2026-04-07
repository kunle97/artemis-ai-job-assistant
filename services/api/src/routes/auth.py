"""
Auth API routes.

Handles user registration, login, and authenticated session retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.deps.auth import get_current_user
from src.domain.auth.repository import UserRepository
from src.domain.auth.schemas import TokenRead, UserCreate, UserLogin, UserRead
from src.domain.auth.service import UserService
from src.infrastructure.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    repository = UserRepository(db)
    service = UserService(repository)

    try:
        return service.create_user(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/login", response_model=TokenRead)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    repository = UserRepository(db)
    service = UserService(repository)

    try:
        token = service.login_user(payload)
        return TokenRead(access_token=token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.get("/session", response_model=UserRead)
def read_current_session(current_user=Depends(get_current_user)):
    """
    Return the currently authenticated user.
    """
    return current_user