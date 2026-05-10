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
    willing_to_relocate: bool | None = field(default=None)
    current_company: str | None = field(default=None)
    work_arrangement: str | None = field(default=None)
    salary_target: str | None = field(default=None)
    desired_start_date: str | None = field(default=None)
    page_title: str | None = field(default=None)
    job_context: str | None = field(default=None)


@dataclass
class OpenEndedAnswerResult:
    answer_text: str | None
    source: str
    needs_review: bool
    intent_key: str | None = None