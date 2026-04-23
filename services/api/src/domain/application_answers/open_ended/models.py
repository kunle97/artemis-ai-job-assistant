from dataclasses import dataclass


@dataclass
class OpenEndedAnswerRequest:
    user_id: str
    question_text: str


@dataclass
class OpenEndedAnswerResult:
    answer_text: str | None
    source: str
    needs_review: bool
    intent_key: str | None = None