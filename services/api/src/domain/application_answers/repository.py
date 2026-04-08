"""
Application answer repository.

Handles database operations for reusable application answers.
"""

from sqlalchemy.orm import Session

from src.domain.application_answers.models import ApplicationAnswer


class ApplicationAnswerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_and_key(self, user_id, question_key: str):
        return (
            self.db.query(ApplicationAnswer)
            .filter(
                ApplicationAnswer.user_id == user_id,
                ApplicationAnswer.question_key == question_key,
            )
            .first()
        )

    def create(self, **answer_data):
        answer = ApplicationAnswer(**answer_data)
        self.db.add(answer)
        self.db.commit()
        self.db.refresh(answer)
        return answer

    def update(self, answer: ApplicationAnswer, **answer_data):
        for key, value in answer_data.items():
            setattr(answer, key, value)

        self.db.add(answer)
        self.db.commit()
        self.db.refresh(answer)
        return answer

    def upsert(
        self,
        user_id,
        question_key: str,
        category: str | None,
        question_text: str | None,
        answer_text: str,
    ):
        existing = self.get_by_user_and_key(user_id=user_id, question_key=question_key)
        if existing:
            return self.update(
                existing,
                category=category,
                question_text=question_text,
                answer_text=answer_text,
            )

        return self.create(
            user_id=user_id,
            question_key=question_key,
            category=category,
            question_text=question_text,
            answer_text=answer_text,
        )

    def list_by_user_id(self, user_id):
        return (
            self.db.query(ApplicationAnswer)
            .filter(ApplicationAnswer.user_id == user_id)
            .order_by(ApplicationAnswer.created_at.desc())
            .all()
        )