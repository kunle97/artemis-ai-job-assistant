"""
Application answer repository.

Stores and retrieves reusable answers to common application questions.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.domain.application_answers.models import ApplicationAnswer


class ApplicationAnswerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        user_id,
        question_key: str,
        question_text: str | None,
        answer_text: str,
        category: str | None = None,
    ) -> ApplicationAnswer:
        record = ApplicationAnswer(
            user_id=user_id,
            question_key=question_key,
            question_text=question_text,
            answer_text=answer_text,
            category=category,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def upsert(
        self,
        *,
        user_id,
        question_key: str,
        question_text: str | None,
        answer_text: str,
        category: str | None = None,
    ) -> ApplicationAnswer:
        record = (
            self.db.query(ApplicationAnswer)
            .filter(
                ApplicationAnswer.user_id == user_id,
                ApplicationAnswer.question_key == question_key,
            )
            .first()
        )
        if record:
            record.question_text = question_text
            record.answer_text = answer_text
            record.category = category
        else:
            record = ApplicationAnswer(
                user_id=user_id,
                question_key=question_key,
                question_text=question_text,
                answer_text=answer_text,
                category=category,
            )
            self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_by_user_id(self, user_id) -> list[ApplicationAnswer]:
        return (
            self.db.query(ApplicationAnswer)
            .filter(ApplicationAnswer.user_id == user_id)
            .order_by(ApplicationAnswer.created_at.desc())
            .all()
        )

    def delete_by_id(self, *, answer_id: str, user_id) -> bool:
        record = (
            self.db.query(ApplicationAnswer)
            .filter(
                ApplicationAnswer.id == answer_id,
                ApplicationAnswer.user_id == user_id,
            )
            .first()
        )
        if not record:
            return False
        self.db.delete(record)
        self.db.commit()
        return True