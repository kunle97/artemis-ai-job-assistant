"""
Application answer service.

Coordinates creation and retrieval of reusable application answers.
"""

import logging

from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.application_answers.schemas import ApplicationAnswerCreate

logger = logging.getLogger(__name__)


class ApplicationAnswerService:
    def __init__(self, repository: ApplicationAnswerRepository):
        self.repository = repository

    def save_answer(self, user_id, payload: ApplicationAnswerCreate):
        logger.info(
            "[ApplicationAnswerService] save_answer start user_id=%s question_key=%s",
            user_id,
            payload.question_key,
        )
        answer = self.repository.upsert(
            user_id=user_id,
            question_key=payload.question_key,
            category=payload.category,
            question_text=payload.question_text,
            answer_text=payload.answer_text,
        )
        logger.info(
            "[ApplicationAnswerService] save_answer complete answer_id=%s",
            answer.id,
        )
        return answer

    def list_answers(self, user_id):
        logger.info("[ApplicationAnswerService] list_answers user_id=%s", user_id)
        answers = self.repository.list_by_user_id(user_id)
        logger.info("[ApplicationAnswerService] list_answers count=%d", len(answers))
        return answers