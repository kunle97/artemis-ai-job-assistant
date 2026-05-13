"""
Open-ended application answer service.

Builds request context from user/profile data and delegates to the configured
open-ended answer provider (resolver-only or LLM-backed).
"""

from __future__ import annotations

import logging

from src.domain.application_answers.open_ended.models import OpenEndedAnswerRequest

logger = logging.getLogger(__name__)


class OpenEndedApplicationAnswerService:
    def __init__(self, *, user_repo, profile_repo, provider):
        self.user_repo = user_repo
        self.profile_repo = profile_repo
        self.provider = provider

    def generate(
        self,
        *,
        user_id,
        question_text: str,
        page_title: str | None = None,
        job_context: str | None = None,
    ):
        logger.info("[OpenEndedAnswerService] generate start user_id=%s", user_id)

        user = self.user_repo.get_by_id(user_id)
        profile = self.profile_repo.get_by_user_id(user_id)
        request = self._build_request(
            user_id=user_id,
            question_text=question_text,
            user=user,
            profile=profile,
            page_title=page_title,
            job_context=job_context,
        )
        result = self.provider.get_answer(request)

        logger.info(
            "[OpenEndedAnswerService] generate result user_id=%s source=%s resolved=%s",
            user_id,
            result.source,
            bool(result.answer_text),
        )
        return result

    def _build_request(
        self,
        *,
        user_id,
        question_text: str,
        user,
        profile,
        page_title: str | None = None,
        job_context: str | None = None,
    ) -> OpenEndedAnswerRequest:
        first_name = getattr(profile, "first_name", None) or getattr(user, "first_name", None)
        last_name = getattr(profile, "last_name", None) or getattr(user, "last_name", None)

        raw_skills = getattr(profile, "skills", None) or []
        skill_names = []
        for skill in raw_skills[:10]:
            if isinstance(skill, dict):
                skill_names.append(skill.get("name") or skill.get("label") or "")
            else:
                skill_names.append(str(skill))
        skills_summary = ", ".join(filter(None, skill_names)) or None

        experience_sections = getattr(profile, "experience_sections", None) or []
        role_lines = []
        for exp in experience_sections[:2]:
            if isinstance(exp, dict):
                title = exp.get("title") or exp.get("role") or ""
                company = exp.get("company") or exp.get("employer") or ""
                line = " at ".join(filter(None, [title, company]))
                if line:
                    role_lines.append(line)
        experience_summary = "; ".join(role_lines) or None

        current_location = None
        city = getattr(profile, "city", None)
        state = getattr(profile, "state", None)
        if city and state:
            current_location = f"{city}, {state}"
        elif city or state:
            current_location = city or state

        preferred_relocation_cities = getattr(profile, "preferred_relocation_cities", None) or []
        relocation_destinations = getattr(profile, "relocation_destinations", None) or []
        if relocation_destinations and not preferred_relocation_cities:
            preferred_relocation_cities = relocation_destinations

        work_arrangement = getattr(profile, "work_arrangement", None)
        if isinstance(work_arrangement, list):
            cleaned = [str(item).strip() for item in work_arrangement if str(item).strip()]
            work_arrangement = ", ".join(cleaned) if cleaned else None
        elif work_arrangement:
            work_arrangement = str(work_arrangement)

        return OpenEndedAnswerRequest(
            user_id=user_id,
            question_text=question_text,
            first_name=first_name,
            last_name=last_name,
            skills_summary=skills_summary,
            experience_summary=experience_summary,
            current_location=current_location,
            preferred_relocation_cities=preferred_relocation_cities or None,
            willing_to_relocate=getattr(profile, "willing_to_relocate", None),
            current_company=getattr(profile, "current_company", None),
            work_arrangement=work_arrangement,
            salary_target=getattr(profile, "salary_target", None),
            desired_start_date=getattr(profile, "desired_start_date", None),
            page_title=page_title,
            job_context=job_context,
        )