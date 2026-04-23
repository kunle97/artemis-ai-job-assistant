"""
Application answer resolution.

Resolution order:
1. exact saved question match
2. fuzzy saved question match
3. user-specific intent answer
4. default intent answer
5. unresolved
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.domain.application_answers.constants import (
    CONTAINMENT_SCORE_MULTIPLIER,
    MIN_PREFIX_TOKEN_COUNT,
    MIN_SHARED_PREFIX_TOKENS,
    NON_ALPHANUMERIC_PATTERN,
    NORMALIZE_APOSTROPHE_SOURCE,
    NORMALIZE_APOSTROPHE_TARGET,
    PREFIX_SIMILARITY_BONUS,
    PREFIX_TOKEN_WINDOW,
    SAVED_ANSWER_FUZZY_MATCH_THRESHOLD,
    SOURCE_DEFAULT_INTENT_ANSWER,
    SOURCE_SAVED_ANSWER_EXACT,
    SOURCE_SAVED_ANSWER_FUZZY,
    SOURCE_UNRESOLVED,
    SOURCE_USER_INTENT_ANSWER,
    STOP_WORDS,
    TOKEN_PATTERN,
    WHITESPACE_PATTERN,
)
from src.domain.application_answers.intents.constants import DEFAULT_INTENT_ANSWERS
from src.domain.application_answers.intents.detector import IntentDetector


@dataclass
class ResolvedApplicationAnswer:
    resolved_answer: str | None
    source: str
    needs_review: bool
    intent_key: str | None = None


class ApplicationAnswerResolver:
    def __init__(self, answer_repository, intent_repository, profile_repository):
        self.answer_repository = answer_repository
        self.intent_repository = intent_repository
        self.profile_repository = profile_repository
        self.intent_detector = IntentDetector(
            normalize_fn=self._normalize_text,
            similarity_fn=self._similarity_score,
        )

    def resolve(self, *, user_id, question_text: str) -> ResolvedApplicationAnswer:
        normalized_question = self._normalize_text(question_text)
        if not normalized_question:
            return ResolvedApplicationAnswer(
                resolved_answer=None,
                source=SOURCE_UNRESOLVED,
                needs_review=True,
                intent_key=None,
            )

        detected_intent = self.intent_detector.detect(question_text)
        saved_answers = self.answer_repository.list_by_user_id(user_id)

        exact_match = self._find_exact_saved_match(saved_answers, normalized_question)
        if exact_match:
            return ResolvedApplicationAnswer(
                resolved_answer=exact_match.answer_text,
                source=SOURCE_SAVED_ANSWER_EXACT,
                needs_review=False,
                intent_key=detected_intent,
            )

        fuzzy_saved_match = self._find_best_saved_match(saved_answers, normalized_question)
        if fuzzy_saved_match:
            return ResolvedApplicationAnswer(
                resolved_answer=fuzzy_saved_match.answer_text,
                source=SOURCE_SAVED_ANSWER_FUZZY,
                needs_review=False,
                intent_key=detected_intent,
            )

        if detected_intent:
            user_intent_answer = self.intent_repository.get_by_user_and_intent(
                user_id=user_id,
                intent_key=detected_intent,
            )
            if user_intent_answer:
                return ResolvedApplicationAnswer(
                    resolved_answer=user_intent_answer.answer_text,
                    source=SOURCE_USER_INTENT_ANSWER,
                    needs_review=False,
                    intent_key=detected_intent,
                )

            default_intent_answer = DEFAULT_INTENT_ANSWERS.get(detected_intent)
            if default_intent_answer:
                return ResolvedApplicationAnswer(
                    resolved_answer=default_intent_answer,
                    source=SOURCE_DEFAULT_INTENT_ANSWER,
                    needs_review=False,
                    intent_key=detected_intent,
                )

        return ResolvedApplicationAnswer(
            resolved_answer=None,
            source=SOURCE_UNRESOLVED,
            needs_review=True,
            intent_key=detected_intent,
        )

    def _find_exact_saved_match(self, saved_answers, normalized_question: str):
        for answer in saved_answers:
            candidate = self._normalize_text(answer.question_text)
            if candidate == normalized_question:
                return answer
        return None

    def _find_best_saved_match(self, saved_answers, normalized_question: str):
        best_score = 0.0
        best_answer = None

        for answer in saved_answers:
            candidate = self._normalize_text(answer.question_text)
            score = self._similarity_score(normalized_question, candidate)

            if score > best_score:
                best_score = score
                best_answer = answer

        if best_answer and best_score >= SAVED_ANSWER_FUZZY_MATCH_THRESHOLD:
            return best_answer

        return None

    def _similarity_score(self, left: str, right: str) -> float:
        if not left or not right:
            return 0.0

        if left == right:
            return 1.0

        left_tokens = self._tokenize(left)
        right_tokens = self._tokenize(right)

        if not left_tokens or not right_tokens:
            return 0.0

        intersection = left_tokens & right_tokens
        union = left_tokens | right_tokens
        jaccard = len(intersection) / max(len(union), 1)

        left_in_right = 1.0 if left in right else 0.0
        right_in_left = 1.0 if right in left else 0.0
        containment = max(left_in_right, right_in_left)

        prefix_bonus = PREFIX_SIMILARITY_BONUS if self._starts_similarly(left, right) else 0.0

        return max(
            jaccard + prefix_bonus,
            containment * CONTAINMENT_SCORE_MULTIPLIER,
            jaccard,
        )

    def _starts_similarly(self, left: str, right: str) -> bool:
        left_tokens = list(self._tokenize(left))
        right_tokens = list(self._tokenize(right))

        if len(left_tokens) < MIN_PREFIX_TOKEN_COUNT or len(right_tokens) < MIN_PREFIX_TOKEN_COUNT:
            return False

        return (
            len(set(left_tokens[:PREFIX_TOKEN_WINDOW]) & set(right_tokens[:PREFIX_TOKEN_WINDOW]))
            >= MIN_SHARED_PREFIX_TOKENS
        )

    def _tokenize(self, text: str) -> set[str]:
        raw_tokens = re.findall(TOKEN_PATTERN, text.lower())
        return {token for token in raw_tokens if token not in STOP_WORDS}

    def _normalize_text(self, text: str | None) -> str:
        if not text:
            return ""

        normalized = text.lower().strip()
        normalized = normalized.replace(
            NORMALIZE_APOSTROPHE_SOURCE,
            NORMALIZE_APOSTROPHE_TARGET,
        )
        normalized = re.sub(NON_ALPHANUMERIC_PATTERN, " ", normalized)
        normalized = re.sub(WHITESPACE_PATTERN, " ", normalized).strip()
        return normalized