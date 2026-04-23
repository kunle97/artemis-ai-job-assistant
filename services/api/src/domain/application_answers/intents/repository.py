"""
Intent answer repository.
"""

from sqlalchemy.orm import Session

from src.domain.application_answers.intents.models import ApplicationAnswerIntent


class ApplicationAnswerIntentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_and_intent(self, user_id, intent_key: str):
        return (
            self.db.query(ApplicationAnswerIntent)
            .filter(
                ApplicationAnswerIntent.user_id == user_id,
                ApplicationAnswerIntent.intent_key == intent_key,
            )
            .first()
        )

    def upsert(self, user_id, intent_key: str, answer_text: str):
        existing = self.get_by_user_and_intent(user_id, intent_key)

        if existing:
            existing.answer_text = answer_text
            self.db.commit()
            self.db.refresh(existing)
            return existing

        record = ApplicationAnswerIntent(
            user_id=user_id,
            intent_key=intent_key,
            answer_text=answer_text,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_by_user(self, user_id):
        return (
            self.db.query(ApplicationAnswerIntent)
            .filter(ApplicationAnswerIntent.user_id == user_id)
            .all()
        )