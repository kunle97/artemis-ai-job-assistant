"""
Application answer API routes.

Thin HTTP endpoints for saving and listing reusable application answers.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.deps.auth import get_current_user
from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.application_answers.schemas import (
    ApplicationAnswerCreate,
    ApplicationAnswerRead,
)
from src.domain.application_answers.service import ApplicationAnswerService
from src.infrastructure.db.session import get_db

router = APIRouter(prefix="/application-answers", tags=["application-answers"])


def _build_service(db: Session) -> ApplicationAnswerService:
    return ApplicationAnswerService(
        repository=ApplicationAnswerRepository(db),
    )


@router.post("", response_model=ApplicationAnswerRead)
def save_application_answer(
    payload: ApplicationAnswerCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_service(db)
    return service.save_answer(user_id=current_user.id, payload=payload)


@router.get("", response_model=list[ApplicationAnswerRead])
def list_application_answers(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_service(db)
    return service.list_answers(current_user.id)


@router.delete("/{answer_id}", status_code=204)
def delete_application_answer(
    answer_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_service(db)
    deleted = service.delete_answer(user_id=current_user.id, answer_id=answer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Answer not found.")