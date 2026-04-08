"""
Application answer service.

Coordinates creation and retrieval of reusable application answers.
"""

from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.application_answers.schemas import ApplicationAnswerCreate


class ApplicationAnswerService:
    def __init__(self, repository: ApplicationAnswerRepository):
        self.repository = repository

    def save_answer(self, user_id, payload: ApplicationAnswerCreate):
        return self.repository.upsert(
            user_id=user_id,
            question_key=payload.question_key,
            category=payload.category,
            question_text=payload.question_text,
            answer_text=payload.answer_text,
        )

    def list_answers(self, user_id):
        return self.repository.list_by_user_id(user_id)