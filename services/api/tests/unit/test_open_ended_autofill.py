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
