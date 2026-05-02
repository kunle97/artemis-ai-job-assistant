"""
Groq API client.

Thin wrapper around the groq library for chat completions used by
AI-driven answer generation.
"""

from __future__ import annotations

import logging

from groq import Groq

logger = logging.getLogger(__name__)


class GroqClient:
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self._client = Groq(api_key=api_key)
        self._model = model

    def complete(self, *, system: str, user: str, max_tokens: int = 300) -> str | None:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_completion_tokens=max_tokens,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            logger.warning(
                f"[GroqClient] Completion failed: {type(exc).__name__}: {exc}"
            )
            return None
