"""
LLM-backed open-ended answer provider.

Generates answers using OpenAI when no saved or intent-based answer
is found via the resolver. Persists AI-generated answers to the
application_answers table for future zero-cost reuse.
"""

from __future__ import annotations

import logging
import re

from src.domain.application_answers.constants import SOURCE_UNRESOLVED
from src.domain.application_answers.open_ended.models import (
    OpenEndedAnswerRequest,
    OpenEndedAnswerResult,
)
from src.domain.application_answers.open_ended.provider import OpenEndedAnswerProvider
from src.domain.application_answers.resolution import ApplicationAnswerResolver
from src.integrations.groq.client import GroqClient

logger = logging.getLogger(__name__)

SOURCE_AI_GENERATED = "ai_generated"
CATEGORY_AI_GENERATED = "AI Generated"

_SYSTEM_PROMPT = (
    "You are filling out a job application on behalf of a candidate. "
    "Write answers in first person as if you are the candidate. "
    "Be direct and natural — avoid stiff or corporate-sounding phrases. "
    "Never start an answer with the candidate's name (e.g. never write 'I, Jane Doe, ...'). "
    "Keep answers short and to the point — 2 to 4 sentences for simple yes/no questions, "
    "up to a short paragraph for more complex ones. "
    "Do not fabricate credentials, experience, or legal eligibility. "
    "Use only the context provided."
)


def _build_user_prompt(request: OpenEndedAnswerRequest) -> str:
    parts = []
    if request.first_name or request.last_name:
        name = " ".join(filter(None, [request.first_name, request.last_name]))
        parts.append(f"Candidate: {name}")
    if request.current_location:
        parts.append(f"Current location: {request.current_location}")
    if request.preferred_relocation_cities:
        cities = ", ".join(request.preferred_relocation_cities)
        parts.append(f"Open to relocating to: {cities}")
    if request.current_company:
        parts.append(f"Current company: {request.current_company}")
    if request.work_arrangement:
        parts.append(f"Preferred work arrangement: {request.work_arrangement}")
    if request.salary_target:
        parts.append(f"Salary target: {request.salary_target}")
    if request.skills_summary:
        parts.append(f"Key skills: {request.skills_summary}")
    if request.experience_summary:
        parts.append(f"Recent experience: {request.experience_summary}")
    if request.page_title:
        parts.append(f"Job page title: {request.page_title}")
    if request.job_context:
        parts.append(f"Job context: {request.job_context}")
    parts.append(f'Question: "{request.question_text}"')
    parts.append(
        "Write a concise, natural answer in first person. "
        "For simple factual questions (yes/no, location, availability) keep it to 1-2 sentences. "
        "For more open-ended questions use no more than 4-5 sentences. "
        "When the question is about interest in the company or role, explicitly connect the candidate's background to the job context. "
        "Do not use the candidate's name in the answer."
    )
    return "\n".join(parts)


class LLMOpenEndedAnswerProvider(OpenEndedAnswerProvider):
    def __init__(
        self,
        resolver: ApplicationAnswerResolver,
        llm_client: GroqClient,
        answer_repo,
    ):
        self.resolver = resolver
        self.llm_client = llm_client
        self.answer_repo = answer_repo

    def get_answer(self, request: OpenEndedAnswerRequest) -> OpenEndedAnswerResult:
        question_preview = (request.question_text or "")[:80]
        logger.info(
            f"[LLMProvider] Resolving open-ended question — "
            f"user_id={request.user_id} | question='{question_preview}'"
        )

        # Phase 1: resolver cascade first — zero tokens
        resolved = self.resolver.resolve(
            user_id=request.user_id,
            question_text=request.question_text,
        )
        if resolved.resolved_answer:
            logger.info(
                f"[LLMProvider] Resolved from saved/intent — "
                f"source={resolved.source} | needs_review={resolved.needs_review}"
            )
            return OpenEndedAnswerResult(
                answer_text=resolved.resolved_answer,
                source=resolved.source,
                needs_review=resolved.needs_review,
                intent_key=resolved.intent_key,
            )

        # Phase 2: generate with LLM
        logger.info(
            f"[LLMProvider] No saved/intent match — calling LLM. "
            f"user_id={request.user_id} | model={self.llm_client._model}"
        )
        user_prompt = _build_user_prompt(request)
        logger.debug(f"[LLMProvider] User prompt:\n{user_prompt}")

        answer_text = self.llm_client.complete(
            system=_SYSTEM_PROMPT,
            user=user_prompt,
            max_tokens=300,
        )
        if not answer_text:
            logger.warning(
                f"[LLMProvider] LLM returned no answer for question='{question_preview}'"
            )
            return OpenEndedAnswerResult(
                answer_text=None,
                source=SOURCE_UNRESOLVED,
                needs_review=True,
                intent_key=None,
            )

        answer_preview = answer_text[:120].replace("\n", " ")
        logger.info(
            f"[LLMProvider] LLM answer generated — "
            f"length={len(answer_text)} chars | preview='{answer_preview}'"
        )

        # Phase 3: persist for future reuse
        question_key = re.sub(r"[^a-z0-9]+", "_", request.question_text.strip().lower())[:200].strip("_")
        try:
            self.answer_repo.create(
                user_id=request.user_id,
                question_key=question_key,
                question_text=request.question_text,
                answer_text=answer_text,
                category=CATEGORY_AI_GENERATED,
            )
            logger.info("[LLMProvider] Persisted AI-generated answer for future reuse.")
        except Exception as exc:
            logger.warning(f"[LLMProvider] Failed to persist answer: {type(exc).__name__}")

        return OpenEndedAnswerResult(
            answer_text=answer_text,
            source=SOURCE_AI_GENERATED,
            needs_review=False,
            intent_key=None,
        )
