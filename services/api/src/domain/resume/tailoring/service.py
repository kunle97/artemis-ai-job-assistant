"""
Resume tailoring service.

Generates explainable per-application resume tailoring recommendations
using resume/profile/job context. Returns deterministic fallback output
when LLM is unavailable or generation fails.
"""

from __future__ import annotations

from datetime import UTC, datetime
import io
import json
import logging
from pathlib import Path
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

    def __init__(self, *, repository, llm_client=None, storage_service=None):
        self.repository = repository
        self.llm_client = llm_client
        self.storage_service = storage_service

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

    def create_tailored_resume(
        self,
        *,
        user_id,
        application_id,
        resume_id=None,
        job_description_override: str | None = None,
    ):
        if self.storage_service is None:
            raise ValueError("Storage service unavailable.")

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
            raise ValueError("No resume available to tailor.")

        result = self.tailor_resume(
            user_id=user_id,
            application_id=application_id,
            resume_id=selected_resume.id,
            job_description_override=job_description_override,
        )
        if result.is_fallback or not result.suggestions:
            raise ValueError(result.message or "Unable to create tailored resume from current context.")

        source_text = (selected_resume.extracted_text or "").strip()
        tailored_text = self._build_tailored_resume_text(source_text, result.suggestions)

        source_name = Path(selected_resume.file_name or "resume").stem
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M")
        file_name = f"{source_name}-tailored-{timestamp}.txt"
        upload_file = _InMemoryUploadFile(
            filename=file_name,
            content=tailored_text.encode("utf-8"),
            content_type="text/plain",
        )
        stored_path = self.storage_service.save_upload(upload_file)

        created = self.repository.create_resume(
            user_id=user_id,
            file_name=file_name,
            file_path=stored_path,
            mime_type="text/plain",
            extracted_text=tailored_text,
            parsed_json={
                "status": "generated",
                "generated_from_resume_id": str(selected_resume.id),
                "application_id": str(application_id),
                "tailoring": {
                    "generated_at": result.generated_at.isoformat(),
                    "suggestions": [item.model_dump() for item in result.suggestions],
                },
            },
            variant_type="tailored",
            is_primary=False,
        )
        self.repository.update_application_resume(application_id, created.id)
        return created

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

        # Some models return a top-level JSON array instead of
        # {"suggestions": [...]}. Normalize both formats.
        if isinstance(parsed, list):
            suggestion_items = parsed
        elif isinstance(parsed, dict):
            suggestion_items = parsed.get("suggestions", [])
        else:
            suggestion_items = []

        result: list[TailoringRecommendation] = []
        for item in suggestion_items:
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

    def _parse_llm_json(self, raw: str) -> dict | list | None:
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

    def _build_tailored_resume_text(
        self,
        source_text: str,
        suggestions: list[TailoringRecommendation],
    ) -> str:
        tailored_text = source_text
        if not tailored_text:
            tailored_text = ""

        for suggestion in suggestions:
            current = (suggestion.current_text or "").strip()
            proposed = (suggestion.proposed_text or "").strip()
            if current and proposed and current in tailored_text:
                tailored_text = tailored_text.replace(current, proposed, 1)

        if not tailored_text.strip():
            tailored_text = "\n\n".join(
                [
                    "Tailored Resume Draft",
                    *[
                        f"[{item.section}]\n{item.proposed_text.strip()}"
                        for item in suggestions
                        if item.proposed_text.strip()
                    ],
                ]
            )

        suggestions_block = "\n\n".join(
            [
                f"Section: {item.section}\nReason: {item.reason}\nProposed:\n{item.proposed_text.strip()}"
                for item in suggestions
                if item.proposed_text.strip()
            ]
        )

        return (
            f"{tailored_text.strip()}\n\n"
            "---\n"
            "Tailoring Notes\n"
            f"{suggestions_block}\n"
        )


class _InMemoryUploadFile:
    def __init__(self, *, filename: str, content: bytes, content_type: str):
        self.filename = filename
        self.file = io.BytesIO(content)
        self.content_type = content_type
