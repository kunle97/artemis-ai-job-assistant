"""
Auth API routes.

Handles user creation and retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.infrastructure.db.session import get_db
from app.domains.auth.repository import UserRepository
from app.domains.auth.schemas import UserCreate, UserRead
from app.domains.auth.service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    repository = UserRepository(db)
    service = UserService(repository)

    try:
        return service.create_user(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    repository = UserRepository(db)
    service = UserService(repository)

    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    return user