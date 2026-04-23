# application_answers/intents/resolution.py

from dataclasses import dataclass

from src.domain.application_answers.constants import (
    SOURCE_DEFAULT_INTENT_ANSWER,
    SOURCE_UNRESOLVED,
    SOURCE_USER_INTENT_ANSWER,
)
from src.domain.application_answers.intents.constants import DEFAULT_INTENT_ANSWERS
from src.domain.application_answers.intents.detector import IntentDetector


@dataclass
class ResolvedIntentAnswer:
    resolved_answer: str | None
    source: str
    intent_key: str | None
    needs_review: bool


class IntentAnswerResolver:
    def __init__(self, intent_repository, detector: IntentDetector):
        self.intent_repository = intent_repository
        self.detector = detector

    def resolve(self, *, user_id, question_text: str) -> ResolvedIntentAnswer:
        intent_key = self.detector.detect(question_text)
        if not intent_key:
            return ResolvedIntentAnswer(
                resolved_answer=None,
                source=SOURCE_UNRESOLVED,
                intent_key=None,
                needs_review=True,
            )

        user_answer = self.intent_repository.get_by_user_and_intent(
            user_id=user_id,
            intent_key=intent_key,
        )
        if user_answer:
            return ResolvedIntentAnswer(
                resolved_answer=user_answer.answer_text,
                source=SOURCE_USER_INTENT_ANSWER,
                intent_key=intent_key,
                needs_review=False,
            )

        default_answer = DEFAULT_INTENT_ANSWERS.get(intent_key)
        if default_answer:
            return ResolvedIntentAnswer(
                resolved_answer=default_answer,
                source=SOURCE_DEFAULT_INTENT_ANSWER,
                intent_key=intent_key,
                needs_review=False,
            )

        return ResolvedIntentAnswer(
            resolved_answer=None,
            source=SOURCE_UNRESOLVED,
            intent_key=intent_key,
            needs_review=True,
        )