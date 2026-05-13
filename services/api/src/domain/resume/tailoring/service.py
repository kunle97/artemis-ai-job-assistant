"""
Resume tailoring service.

Generates explainable per-application resume tailoring recommendations
using resume/profile/job context. Returns deterministic fallback output
when LLM is unavailable or generation fails.
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
import re

from src.domain.resume.tailoring.models import TailoringContext
from src.domain.resume.tailoring.schemas import TailoredResumeResult, TailoringRecommendation

logger = logging.getLogger(__name__)

_STOPWORDS = {
    "the", "and", "for", "that", "with", "from", "your", "this", "have", "will", "you", "are",
    "our", "job", "role", "team", "work", "years", "experience", "required", "preferred",
}

_SYSTEM_PROMPT = (
    "You are a senior resume coach. Return strict JSON only. "
    "Given a resume context and job context, produce actionable rewrite suggestions."
)


class ResumeTailoringService:
    """Business logic for per-application resume tailoring."""

    def __init__(self, *, repository, llm_client=None):
        self.repository = repository
        self.llm_client = llm_client

    def tailor_resume(
        self,
        *,
        user_id,
        application_id,
        resume_id=None,
        job_description_override: str | None = None,
    ) -> TailoredResumeResult:
        logger.info(
            "[ResumeTailoringService] tailor_resume start user_id=%s application_id=%s resume_id=%s",
            user_id,
            application_id,
            resume_id,
        )

        application = self.repository.get_application(application_id)
        if application is None:
            raise ValueError("Application not found.")
        if application.user_id != user_id:
            raise PermissionError("Forbidden")

        selected_resume = None
        if resume_id is not None:
            selected_resume = self.repository.get_resume_by_user(user_id, resume_id)
            if selected_resume is None:
                raise ValueError("Resume not found.")
        elif application.resume_id is not None:
            selected_resume = self.repository.get_resume_by_user(user_id, application.resume_id)

        if selected_resume is None:
            selected_resume = self.repository.get_primary_resume_for_user(user_id)

        if selected_resume is None:
            selected_resume = self.repository.get_latest_resume_for_user(user_id)

        if selected_resume is None:
            return TailoredResumeResult(
                application_id=application_id,
                generated_at=datetime.now(UTC),
                is_fallback=True,
                message="No resume available to tailor. Upload or select a resume first.",
                suggestions=[],
            )

        job = self.repository.get_job(application.job_id)
        if job is None:
            raise ValueError("Job not found.")

        jd_text = (job.description or "").strip()
        if not jd_text and (job_description_override or "").strip():
            jd_text = (job_description_override or "").strip()

        if not jd_text:
            return TailoredResumeResult(
                application_id=application_id,
                resume_id=selected_resume.id,
                generated_at=datetime.now(UTC),
                is_fallback=True,
                message="Job description is missing. Add job context to generate tailoring suggestions.",
                suggestions=[],
            )

        profile = self.repository.get_profile_for_user(user_id)
        context = self._build_context(
            selected_resume=selected_resume,
            profile=profile,
            job=job,
            job_description=jd_text,
        )

        if self.llm_client is None:
            return TailoredResumeResult(
                application_id=application_id,
                resume_id=selected_resume.id,
                generated_at=datetime.now(UTC),
                is_fallback=True,
                message="LLM provider unavailable. Configure GROQ_API_KEY to enable tailoring suggestions.",
                suggestions=[],
            )

        suggestions = self._generate_with_llm(context)
        if not suggestions:
            return TailoredResumeResult(
                application_id=application_id,
                resume_id=selected_resume.id,
                generated_at=datetime.now(UTC),
                is_fallback=True,
                message="Tailoring generation unavailable right now. Please try again.",
                suggestions=[],
            )

        logger.info(
            "[ResumeTailoringService] tailor_resume complete user_id=%s application_id=%s suggestions=%d",
            user_id,
            application_id,
            len(suggestions),
        )

        return TailoredResumeResult(
            application_id=application_id,
            resume_id=selected_resume.id,
            generated_at=datetime.now(UTC),
            is_fallback=False,
            message="Suggestions generated. Your stored resume is unchanged.",
            suggestions=suggestions,
        )

    def _build_context(self, *, selected_resume, profile, job, job_description: str | None = None) -> TailoringContext:
        parsed = (selected_resume.parsed_json or {}).get("normalized_data") or {}
        resume_text = (selected_resume.extracted_text or "").strip()

        skills = []
        skills.extend(parsed.get("skills") or [])
        if profile and profile.skills:
            skills.extend(profile.skills)
        skills = list(dict.fromkeys([s.strip() for s in skills if isinstance(s, str) and s.strip()]))

        profile_parts = []
        if profile and profile.current_company:
            profile_parts.append(f"Current company: {profile.current_company}")
        if profile and profile.work_arrangement:
            profile_parts.append(f"Preferred work arrangement: {profile.work_arrangement}")
        if parsed.get("headline_title"):
            profile_parts.append(f"Headline: {parsed['headline_title']}")
        if parsed.get("current_job_title"):
            profile_parts.append(f"Current role: {parsed['current_job_title']}")

        return TailoringContext(
            resume_text=resume_text,
            profile_summary=" | ".join(profile_parts),
            job_description=(job_description or job.description or "").strip(),
            job_title=(job.title or "").strip(),
            company_name=(job.company_name or "").strip(),
            skills=skills,
        )

    def _generate_with_llm(self, context: TailoringContext) -> list[TailoringRecommendation]:
        top_keywords = self._extract_keywords(context.job_description)

        user_prompt = (
            "Return JSON object with key 'suggestions' as an array. Each suggestion must include: "
            "section, current_text, proposed_text, reason, matched_keywords, missing_keywords.\n"
            f"Job title: {context.job_title}\n"
            f"Company: {context.company_name}\n"
            f"Top JD keywords: {', '.join(top_keywords)}\n"
            f"Profile summary: {context.profile_summary or 'N/A'}\n"
            f"Resume skills: {', '.join(context.skills) if context.skills else 'N/A'}\n"
            f"Resume text excerpt: {(context.resume_text or '')[:4000]}\n"
            f"Job description excerpt: {context.job_description[:4000]}\n"
            "Generate 3-6 concise, high-impact suggestions."
        )

        raw = self.llm_client.complete(system=_SYSTEM_PROMPT, user=user_prompt, max_tokens=900)
        if not raw:
            logger.warning("[ResumeTailoringService] LLM returned empty response")
            return []

        parsed = self._parse_llm_json(raw)
        if not parsed:
            logger.warning("[ResumeTailoringService] Failed to parse LLM response")
            return []

        result: list[TailoringRecommendation] = []
        for item in parsed.get("suggestions", []):
            try:
                result.append(
                    TailoringRecommendation(
                        section=str(item.get("section") or "general"),
                        current_text=str(item.get("current_text") or ""),
                        proposed_text=str(item.get("proposed_text") or ""),
                        reason=str(item.get("reason") or ""),
                        matched_keywords=[str(v) for v in (item.get("matched_keywords") or []) if str(v).strip()],
                        missing_keywords=[str(v) for v in (item.get("missing_keywords") or []) if str(v).strip()],
                    )
                )
            except Exception:
                continue

        return [s for s in result if s.proposed_text.strip() and s.reason.strip()]

    def _parse_llm_json(self, raw: str) -> dict | None:
        candidate = raw.strip()
        if candidate.startswith("```"):
            candidate = re.sub(r"^```(?:json)?", "", candidate).strip()
            candidate = re.sub(r"```$", "", candidate).strip()

        try:
            return json.loads(candidate)
        except Exception:
            pass

        match = re.search(r"\{[\s\S]*\}", candidate)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except Exception:
            return None

    def _extract_keywords(self, jd_text: str) -> list[str]:
        tokens = re.findall(r"[a-zA-Z][a-zA-Z+.#-]{2,}", jd_text.lower())
        filtered = [t for t in tokens if t not in _STOPWORDS]
        freq: dict[str, int] = {}
        for token in filtered:
            freq[token] = freq.get(token, 0) + 1
        return [k for k, _ in sorted(freq.items(), key=lambda item: item[1], reverse=True)[:12]]
