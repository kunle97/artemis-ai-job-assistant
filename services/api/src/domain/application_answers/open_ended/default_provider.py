from src.domain.application_answers.open_ended.models import (
    OpenEndedAnswerRequest,
    OpenEndedAnswerResult,
)
from src.domain.application_answers.open_ended.provider import OpenEndedAnswerProvider
from src.domain.application_answers.resolution import ApplicationAnswerResolver


class DefaultOpenEndedAnswerProvider(OpenEndedAnswerProvider):
    def __init__(self, resolver: ApplicationAnswerResolver):
        self.resolver = resolver

    def get_answer(self, request: OpenEndedAnswerRequest) -> OpenEndedAnswerResult:
        resolved = self.resolver.resolve(
            user_id=request.user_id,
            question_text=request.question_text,
        )
        return OpenEndedAnswerResult(
            answer_text=resolved.resolved_answer,
            source=resolved.source,
            needs_review=resolved.needs_review,
            intent_key=resolved.intent_key,
        )