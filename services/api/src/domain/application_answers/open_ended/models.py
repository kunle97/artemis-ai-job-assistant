from dataclasses import dataclass, field


@dataclass
class OpenEndedAnswerRequest:
    user_id: str
    question_text: str
    first_name: str | None = field(default=None)
    last_name: str | None = field(default=None)
    skills_summary: str | None = field(default=None)
    experience_summary: str | None = field(default=None)
    current_location: str | None = field(default=None)
    preferred_relocation_cities: list | None = field(default=None)


@dataclass
class OpenEndedAnswerResult:
    answer_text: str | None
    source: str
    needs_review: bool
    intent_key: str | None = None