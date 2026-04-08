"""
Application answer matching service.

Matches raw application questions to canonical saved answer keys.
"""

from __future__ import annotations

from src.domain.application_answers.matching.constants import QUESTION_ALIASES
from src.domain.application_answers.matching.normalizer import QuestionTextNormalizer


class ApplicationAnswerMatcher:
    """
    Match incoming questions to canonical answer keys.
    """

    def __init__(self):
        self.normalizer = QuestionTextNormalizer()
        self._normalized_alias_map = self._build_alias_map()

    def match_question_to_key(self, question_text: str | None) -> str | None:
        """
        Return the canonical question key for a given question text, if known.
        """
        normalized_question = self.normalizer.normalize(question_text)
        if not normalized_question:
            return None

        return self._normalized_alias_map.get(normalized_question)

    def _build_alias_map(self) -> dict[str, str]:
        alias_map: dict[str, str] = {}

        for question_key, aliases in QUESTION_ALIASES.items():
            alias_map[self.normalizer.normalize(question_key)] = question_key

            for alias in aliases:
                alias_map[self.normalizer.normalize(alias)] = question_key

        return alias_map