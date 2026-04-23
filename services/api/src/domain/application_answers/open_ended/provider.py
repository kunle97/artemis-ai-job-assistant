from src.domain.application_answers.open_ended.models import (
    OpenEndedAnswerRequest,
    OpenEndedAnswerResult,
)


class OpenEndedAnswerProvider:
    def get_answer(self, request: OpenEndedAnswerRequest) -> OpenEndedAnswerResult:
        raise NotImplementedError