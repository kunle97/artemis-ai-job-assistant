"""
Application answer service.

Coordinates creation and retrieval of reusable application answers.
"""

import logging

from src.domain.application_answers.repository import ApplicationAnswerRepository
from src.domain.application_answers.schemas import ApplicationAnswerCreate

logger = logging.getLogger(__name__)


def _normalize_category(category: str | None) -> str | None:
    if category is None:
        return None

    normalized = category.strip().lower().replace(" ", "_")
    if normalized == "ai_generated":
        return "AI Generated"

    return category.strip()


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
            category=_normalize_category(payload.category),
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
        for answer in answers:
            answer.category = _normalize_category(answer.category)
        logger.info("[ApplicationAnswerService] list_answers count=%d", len(answers))
        return answers

    def delete_answer(self, user_id, answer_id: str) -> bool:
        logger.info(
            "[ApplicationAnswerService] delete_answer user_id=%s answer_id=%s",
            user_id,
            answer_id,
        )
        deleted = self.repository.delete_by_id(answer_id=answer_id, user_id=user_id)
        if deleted:
            logger.info("[ApplicationAnswerService] delete_answer complete answer_id=%s", answer_id)
        else:
            logger.warning("[ApplicationAnswerService] delete_answer not found answer_id=%s", answer_id)
        return deleted