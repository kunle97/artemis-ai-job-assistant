"""
Unit tests for open-ended field autofill via resolve_field_value().

Verifies:
- FIELD_ROLE_OPEN_ENDED with no provider returns (None, True)
- FIELD_ROLE_OPEN_ENDED with empty label returns (None, True)
- Provider is called with the field label as question_text
- Provider result is returned correctly (answer_text + needs_review)
- Provider returning None answer yields (None, True)
- Profile and user context is built into the request
"""

import pytest

from src.domain.application_answers.open_ended.models import (
    OpenEndedAnswerRequest,
    OpenEndedAnswerResult,
)
from src.domain.automation.planning.constants import FIELD_ROLE_OPEN_ENDED, FIELD_ROLE_UNKNOWN
from src.domain.automation.planning.helpers import resolve_field_value, _build_open_ended_request


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


class _User:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", "user-123")
        self.first_name = kwargs.get("first_name", "Jane")
        self.last_name = kwargs.get("last_name", "Doe")


class _Profile:
    def __init__(self, **kwargs):
        self.first_name = kwargs.get("first_name", None)
        self.last_name = kwargs.get("last_name", None)
        self.skills = kwargs.get("skills", [])
        self.experience_sections = kwargs.get("experience_sections", [])
        self.current_company = kwargs.get("current_company", None)
        self.work_arrangement = kwargs.get("work_arrangement", None)
        self.salary_target = kwargs.get("salary_target", None)
        self.city = kwargs.get("city", None)
        self.state = kwargs.get("state", None)
        self.preferred_relocation_cities = kwargs.get("preferred_relocation_cities", None)
        self.work_authorization = kwargs.get("work_authorization", None)
        self.visa_sponsorship = kwargs.get("visa_sponsorship", None)


class _MockProvider:
    def __init__(self, result: OpenEndedAnswerResult):
        self._result = result
        self.calls: list[OpenEndedAnswerRequest] = []

    def get_answer(self, request: OpenEndedAnswerRequest) -> OpenEndedAnswerResult:
        self.calls.append(request)
        return self._result


# ---------------------------------------------------------------------------
# No provider
# ---------------------------------------------------------------------------


def test_open_ended_no_provider_returns_none():
    value, needs_review = resolve_field_value(
        classified_role=FIELD_ROLE_OPEN_ENDED,
        inspected_field={"label": "Why do you want this role?"},
        user=_User(),
        profile=_Profile(),
        open_ended_provider=None,
    )
    assert value is None
    assert needs_review is True


# ---------------------------------------------------------------------------
# Empty label
# ---------------------------------------------------------------------------


def test_open_ended_empty_label_returns_none():
    provider = _MockProvider(
        OpenEndedAnswerResult(answer_text="some answer", source="saved", needs_review=False)
    )
    value, needs_review = resolve_field_value(
        classified_role=FIELD_ROLE_OPEN_ENDED,
        inspected_field={"label": "   ", "placeholder": ""},
        user=_User(),
        profile=_Profile(),
        open_ended_provider=provider,
    )
    assert value is None
    assert needs_review is True
    assert len(provider.calls) == 0


# ---------------------------------------------------------------------------
# Provider returns an answer
# ---------------------------------------------------------------------------


def test_open_ended_uses_label_as_question_text():
    provider = _MockProvider(
        OpenEndedAnswerResult(
            answer_text="I'm excited about the impact.",
            source="default_intent_answer",
            needs_review=False,
        )
    )
    value, needs_review = resolve_field_value(
        classified_role=FIELD_ROLE_OPEN_ENDED,
        inspected_field={"label": "Why are you interested in this role?"},
        user=_User(),
        profile=_Profile(),
        open_ended_provider=provider,
    )
    assert value == "I'm excited about the impact."
    assert needs_review is False
    assert len(provider.calls) == 1
    assert provider.calls[0].question_text == "Why are you interested in this role?"


def test_open_ended_falls_back_to_placeholder_when_no_label():
    provider = _MockProvider(
        OpenEndedAnswerResult(answer_text="My answer", source="saved", needs_review=True)
    )
    value, needs_review = resolve_field_value(
        classified_role=FIELD_ROLE_OPEN_ENDED,
        inspected_field={"label": "", "placeholder": "Tell us about yourself"},
        user=_User(),
        profile=_Profile(),
        open_ended_provider=provider,
    )
    assert value == "My answer"
    assert provider.calls[0].question_text == "Tell us about yourself"


def test_open_ended_needs_review_true_propagated():
    provider = _MockProvider(
        OpenEndedAnswerResult(answer_text="Draft answer", source="ai_generated", needs_review=True)
    )
    _, needs_review = resolve_field_value(
        classified_role=FIELD_ROLE_OPEN_ENDED,
        inspected_field={"label": "What are your salary expectations?"},
        user=_User(),
        profile=_Profile(),
        open_ended_provider=provider,
    )
    assert needs_review is True


# ---------------------------------------------------------------------------
# Provider returns no answer
# ---------------------------------------------------------------------------


def test_open_ended_provider_returns_none_answer_yields_none():
    provider = _MockProvider(
        OpenEndedAnswerResult(answer_text=None, source="unresolved", needs_review=True)
    )
    value, needs_review = resolve_field_value(
        classified_role=FIELD_ROLE_OPEN_ENDED,
        inspected_field={"label": "Describe a challenge you overcame."},
        user=_User(),
        profile=_Profile(),
        open_ended_provider=provider,
    )
    assert value is None
    assert needs_review is True


# ---------------------------------------------------------------------------
# _build_open_ended_request context extraction
# ---------------------------------------------------------------------------


def test_build_request_extracts_user_name_from_user():
    user = _User(first_name="Alice", last_name="Smith")
    profile = _Profile()
    req = _build_open_ended_request(
        user_id="u-1",
        question_text="Why this role?",
        user=user,
        profile=profile,
    )
    assert req.first_name == "Alice"
    assert req.last_name == "Smith"


def test_build_request_prefers_profile_name_over_user():
    user = _User(first_name="Fallback", last_name="User")
    profile = _Profile(first_name="Jane", last_name="Profile")
    req = _build_open_ended_request(
        user_id="u-1",
        question_text="Why this company?",
        user=user,
        profile=profile,
    )
    assert req.first_name == "Jane"
    assert req.last_name == "Profile"


def test_build_request_extracts_skills_summary():
    profile = _Profile(skills=[{"name": "Python"}, {"name": "React"}, {"name": "SQL"}])
    req = _build_open_ended_request(
        user_id="u-1",
        question_text="Q",
        user=_User(),
        profile=profile,
    )
    assert "Python" in req.skills_summary
    assert "React" in req.skills_summary
    assert "SQL" in req.skills_summary


def test_build_request_extracts_experience_summary():
    profile = _Profile(
        experience_sections=[
            {"title": "Senior Engineer", "company": "Acme"},
            {"title": "Engineer", "company": "Beta Corp"},
        ]
    )
    req = _build_open_ended_request(
        user_id="u-1",
        question_text="Q",
        user=_User(),
        profile=profile,
    )
    assert "Senior Engineer" in req.experience_summary
    assert "Acme" in req.experience_summary


def test_build_request_includes_job_and_profile_context():
    profile = _Profile(
        current_company="Acme",
        work_arrangement="hybrid",
        salary_target="220000",
    )
    req = _build_open_ended_request(
        user_id="u-1",
        question_text="Why are you interested in this role?",
        user=_User(),
        profile=profile,
        page_title="Job Application for Senior Software Engineer at Cognitiv",
        job_context="AdTech platform, AWS, cloud-native systems, measurement.",
    )
    assert req.current_company == "Acme"
    assert req.work_arrangement == "hybrid"
    assert req.salary_target == "220000"
    assert req.page_title == "Job Application for Senior Software Engineer at Cognitiv"
    assert "cloud-native" in req.job_context


def test_build_request_skills_none_when_empty():
    profile = _Profile(skills=[])
    req = _build_open_ended_request(
        user_id="u-1",
        question_text="Q",
        user=_User(),
        profile=profile,
    )
    assert req.skills_summary is None


# ---------------------------------------------------------------------------
# Unknown yes/no fallback via provider
# ---------------------------------------------------------------------------


def test_unknown_yes_no_no_provider_returns_none():
    value, needs_review = resolve_field_value(
        classified_role=FIELD_ROLE_UNKNOWN,
        inspected_field={
            "field_type": "select_like",
            "label": "Are you willing to travel?",
            "options": ["Yes", "No"],
        },
        user=_User(),
        profile=_Profile(),
        open_ended_provider=None,
    )
    assert value is None
    assert needs_review is True


def test_unknown_yes_no_uses_provider_and_coerces_yes():
    provider = _MockProvider(
        OpenEndedAnswerResult(answer_text="Yes", source="ai_generated", needs_review=False)
    )
    value, needs_review = resolve_field_value(
        classified_role=FIELD_ROLE_UNKNOWN,
        inspected_field={
            "field_type": "select_like",
            "label": "Are you legally eligible to work in the United States?",
            "options": ["Yes", "No"],
        },
        user=_User(),
        profile=_Profile(),
        open_ended_provider=provider,
    )
    assert value == "Yes"
    assert needs_review is False
    assert len(provider.calls) == 1


def test_unknown_yes_no_coerces_sentence_to_no():
    provider = _MockProvider(
        OpenEndedAnswerResult(
            answer_text="No, I would not require sponsorship.",
            source="ai_generated",
            needs_review=False,
        )
    )
    value, needs_review = resolve_field_value(
        classified_role=FIELD_ROLE_UNKNOWN,
        inspected_field={
            "field_type": "radio_group",
            "label": "Do you require sponsorship?",
            "options": [{"label": "Yes", "value": "yes"}, {"label": "No", "value": "no"}],
        },
        user=_User(),
        profile=_Profile(),
        open_ended_provider=provider,
    )
    assert value == "No"
    assert needs_review is False


def test_unknown_non_binary_options_does_not_call_provider():
    provider = _MockProvider(
        OpenEndedAnswerResult(answer_text="Yes", source="ai_generated", needs_review=False)
    )
    value, needs_review = resolve_field_value(
        classified_role=FIELD_ROLE_UNKNOWN,
        inspected_field={
            "field_type": "select_like",
            "label": "What is your preferred work model?",
            "options": ["Hybrid", "Remote", "On-site"],
        },
        user=_User(),
        profile=_Profile(),
        open_ended_provider=provider,
    )
    assert value is None
    assert needs_review is True
    assert len(provider.calls) == 0


def test_unknown_yes_no_works_when_options_are_missing():
    provider = _MockProvider(
        OpenEndedAnswerResult(answer_text="Yes", source="ai_generated", needs_review=False)
    )
    value, needs_review = resolve_field_value(
        classified_role=FIELD_ROLE_UNKNOWN,
        inspected_field={
            "field_type": "select_like",
            "label": "Do you have strong AWS experience designing and operating cloud-native systems?",
            "options": [],
        },
        user=_User(),
        profile=_Profile(),
        open_ended_provider=provider,
    )
    assert value == "Yes"
    assert needs_review is False
    assert len(provider.calls) == 1


def test_unknown_textarea_open_ended_uses_provider_with_job_context():
    provider = _MockProvider(
        OpenEndedAnswerResult(
            answer_text="I'm excited by the combination of cloud-native systems and applied AI.",
            source="ai_generated",
            needs_review=False,
        )
    )
    value, needs_review = resolve_field_value(
        classified_role=FIELD_ROLE_UNKNOWN,
        inspected_field={
            "field_type": "textarea",
            "label": "Why Cognitiv? Why are you interested in this role with us?",
        },
        user=_User(),
        profile=_Profile(skills=[{"name": "AWS"}], experience_sections=[{"title": "Senior Engineer", "company": "Acme"}]),
        open_ended_provider=provider,
        page_title="Job Application for Senior Software Engineer at Cognitiv",
        job_context="AdTech platform, cloud-native systems, reporting and measurement.",
    )
    assert value is not None
    assert needs_review is False
    assert provider.calls[0].page_title == "Job Application for Senior Software Engineer at Cognitiv"
    assert "AdTech" in provider.calls[0].job_context


def test_work_arrangement_binary_question_uses_profile_and_location():
    value, needs_review = resolve_field_value(
        classified_role=FIELD_ROLE_UNKNOWN,
        inspected_field={
            "field_type": "select_like",
            "label": "We have a hybrid culture. Are you able to work out of our NY office Monday, Tuesday and Wednesday?*",
            "options": [],
        },
        user=_User(),
        profile=_Profile(
            work_arrangement="hybrid",
            city="Jersey City",
            state="NJ",
        ),
        open_ended_provider=None,
    )
    assert value == "Yes"
    assert needs_review is False


def test_work_authorization_binary_question_coerces_us_citizen_to_yes():
    value, needs_review = resolve_field_value(
        classified_role="work_authorization",
        inspected_field={
            "field_type": "select_like",
            "label": "Are you legally authorized to work in the United States?*",
            "options": [],
        },
        user=_User(),
        profile=_Profile(work_authorization="U.S. Citizen"),
        open_ended_provider=None,
    )
    assert value == "Yes"
    assert needs_review is False


def test_work_authorization_binary_question_uses_visa_sponsorship_yes_no():
    value, needs_review = resolve_field_value(
        classified_role="work_authorization",
        inspected_field={
            "field_type": "select_like",
            "label": "Will you now or in the future require sponsorship for employment visa status?*",
            "options": [],
        },
        user=_User(),
        profile=_Profile(visa_sponsorship="No"),
        open_ended_provider=None,
    )
    assert value == "No"
    assert needs_review is False


def test_work_authorization_handles_common_label_typo_leagally():
    value, needs_review = resolve_field_value(
        classified_role="unknown",
        inspected_field={
            "field_type": "select_like",
            "label": "Are you leagally authorized to work in the united states?",
            "options": [],
        },
        user=_User(),
        profile=_Profile(work_authorization="U.S. Citizen"),
        open_ended_provider=None,
    )
    assert value == "Yes"
    assert needs_review is False


def test_work_arrangement_nyc_commute_question_uses_location_without_work_arrangement():
    value, needs_review = resolve_field_value(
        classified_role="work_arrangement",
        inspected_field={
            "field_type": "select_like",
            "label": "Are you currently based a commutable distance to manhatten for in person collaboration 2 times per week?",
            "options": [],
        },
        user=_User(),
        profile=_Profile(city="Jersey City", state="NJ", work_arrangement=None),
        open_ended_provider=None,
    )
    assert value == "Yes"
    assert needs_review is False


def test_salary_expectation_yes_no_question_uses_range_not_raw_target():
    value, needs_review = resolve_field_value(
        classified_role="salary_expectation",
        inspected_field={
            "field_type": "select_like",
            "label": "The base salary for this role is $160,000 - $210,000 USD + Equity. Does this align with your compensation expectations?*",
            "options": [],
        },
        user=_User(),
        profile=_Profile(salary_target="250000"),
        open_ended_provider=None,
    )
    assert value == "No"
    assert needs_review is False
