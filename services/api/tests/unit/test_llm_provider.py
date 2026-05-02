"""
Unit tests for LLMOpenEndedAnswerProvider.

Verifies:
- Resolver match short-circuits before LLM is called
- LLM is called when resolver returns unresolved
- Successful LLM response is persisted via answer_repo
- Failed LLM call does not persist, returns unresolved result
"""

import pytest

from src.domain.application_answers.constants import SOURCE_UNRESOLVED
from src.domain.application_answers.open_ended.llm_provider import (
    LLMOpenEndedAnswerProvider,
    SOURCE_AI_GENERATED,
)
from src.domain.application_answers.open_ended.models import (
    OpenEndedAnswerRequest,
    OpenEndedAnswerResult,
)
from src.domain.application_answers.resolution import ResolvedApplicationAnswer


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


class _MockResolver:
    def __init__(self, resolved_answer=None, source=SOURCE_UNRESOLVED, needs_review=True):
        self._resolved = ResolvedApplicationAnswer(
            resolved_answer=resolved_answer,
            source=source,
            needs_review=needs_review,
            intent_key=None,
        )
        self.calls = []

    def resolve(self, *, user_id, question_text):
        self.calls.append((user_id, question_text))
        return self._resolved


class _MockGroqClient:
    def __init__(self, return_value: str | None = "Generated answer."):
        self._return = return_value
        self._model = "mock-model"
        self.calls = []

    def complete(self, *, system, user, max_tokens=300):
        self.calls.append({"system": system, "user": user})
        return self._return


class _MockAnswerRepo:
    def __init__(self):
        self.saved = []

    def create(self, *, user_id, question_key, question_text, answer_text, category=None):
        self.saved.append(
            {
                "user_id": user_id,
                "question_key": question_key,
                "question_text": question_text,
                "answer_text": answer_text,
                "category": category,
            }
        )


def _make_request(**kwargs):
    defaults = dict(user_id="u-1", question_text="Why this role?")
    defaults.update(kwargs)
    return OpenEndedAnswerRequest(**defaults)


# ---------------------------------------------------------------------------
# Phase 1: resolver short-circuits
# ---------------------------------------------------------------------------


def test_resolver_match_skips_llm():
    resolver = _MockResolver(
        resolved_answer="Saved answer text",
        source="saved_answer_exact",
        needs_review=False,
    )
    openai_client = _MockGroqClient()
    repo = _MockAnswerRepo()
    provider = LLMOpenEndedAnswerProvider(
        resolver=resolver, llm_client=openai_client, answer_repo=repo
    )

    result = provider.get_answer(_make_request())

    assert result.answer_text == "Saved answer text"
    assert result.source == "saved_answer_exact"
    assert result.needs_review is False
    assert len(openai_client.calls) == 0
    assert len(repo.saved) == 0


def test_intent_match_skips_llm():
    resolver = _MockResolver(
        resolved_answer="Default intent answer",
        source="default_intent_answer",
        needs_review=False,
    )
    openai_client = _MockGroqClient()
    repo = _MockAnswerRepo()
    provider = LLMOpenEndedAnswerProvider(
        resolver=resolver, llm_client=openai_client, answer_repo=repo
    )

    result = provider.get_answer(_make_request())

    assert result.answer_text == "Default intent answer"
    assert len(openai_client.calls) == 0


# ---------------------------------------------------------------------------
# Phase 2: LLM is called when resolver returns unresolved
# ---------------------------------------------------------------------------


def test_llm_called_when_resolver_unresolved():
    resolver = _MockResolver(resolved_answer=None)
    openai_client = _MockGroqClient(return_value="Here is my LLM answer.")
    repo = _MockAnswerRepo()
    provider = LLMOpenEndedAnswerProvider(
        resolver=resolver, llm_client=openai_client, answer_repo=repo
    )

    result = provider.get_answer(_make_request(question_text="Describe your biggest strength."))

    assert result.answer_text == "Here is my LLM answer."
    assert result.source == SOURCE_AI_GENERATED
    assert result.needs_review is False
    assert len(openai_client.calls) == 1


# ---------------------------------------------------------------------------
# Phase 3: answer is persisted
# ---------------------------------------------------------------------------


def test_llm_answer_is_persisted():
    resolver = _MockResolver(resolved_answer=None)
    openai_client = _MockGroqClient(return_value="My generated answer.")
    repo = _MockAnswerRepo()
    provider = LLMOpenEndedAnswerProvider(
        resolver=resolver, llm_client=openai_client, answer_repo=repo
    )

    provider.get_answer(_make_request(user_id="user-42", question_text="Tell us about yourself."))

    assert len(repo.saved) == 1
    saved = repo.saved[0]
    assert saved["user_id"] == "user-42"
    assert saved["question_text"] == "Tell us about yourself."
    assert saved["answer_text"] == "My generated answer."
    assert saved["category"] == SOURCE_AI_GENERATED


# ---------------------------------------------------------------------------
# LLM failure path
# ---------------------------------------------------------------------------


def test_llm_failure_returns_unresolved_and_does_not_persist():
    resolver = _MockResolver(resolved_answer=None)
    openai_client = _MockGroqClient(return_value=None)
    repo = _MockAnswerRepo()
    provider = LLMOpenEndedAnswerProvider(
        resolver=resolver, llm_client=openai_client, answer_repo=repo
    )

    result = provider.get_answer(_make_request())

    assert result.answer_text is None
    assert result.source == SOURCE_UNRESOLVED
    assert result.needs_review is True
    assert len(repo.saved) == 0
