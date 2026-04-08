"""
Question text normalizer.

Normalizes question text so similar wording is easier to match.
"""

from __future__ import annotations

import re


class QuestionTextNormalizer:
    """
    Normalize question text for deterministic matching.
    """

    def normalize(self, text: str | None) -> str:
        if not text:
            return ""

        normalized = text.strip().lower()
        normalized = normalized.replace("’", "'")
        normalized = re.sub(r"[*?!.:,;()\[\]{}\"]", "", normalized)
        normalized = re.sub(r"\s+", " ", normalized)

        return normalized