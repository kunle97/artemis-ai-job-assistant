"""
Job scoring service.

Scores a job application across multiple dimensions based on career-ops
evaluation logic (Blocks A–D): role fit, seniority match, and location match.
Uses the Groq LLM client when available; falls back to heuristic scoring.
"""

from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)

# Recommendation thresholds (aligned with career-ops _shared.md)
_RECOMMEND_IMMEDIATELY = "apply_immediately"
_RECOMMEND_WORTH = "worth_applying"
_RECOMMEND_SPECIFIC_REASON = "apply_if_specific_reason"
_RECOMMEND_AGAINST = "recommend_against"

_SENIORITY_KEYWORDS = {
    "staff": 5,
    "principal": 5,
    "lead": 4,
    "senior": 4,
    "sr.": 4,
    "mid": 3,
    "junior": 2,
    "jr.": 2,
    "entry": 1,
    "associate": 2,
}

_REMOTE_SCORE_MAP = {
    "remote": 5.0,
    "hybrid": 3.5,
    "onsite": 2.0,
    "on-site": 2.0,
    "in-office": 2.0,
}


def _recommendation_from_score(global_score: float) -> str:
    if global_score >= 4.5:
        return _RECOMMEND_IMMEDIATELY
    if global_score >= 4.0:
        return _RECOMMEND_WORTH
    if global_score >= 3.5:
        return _RECOMMEND_SPECIFIC_REASON
    return _RECOMMEND_AGAINST


def _weighted_global(role_fit: float, seniority_match: float, location_match: float) -> float:
    # Weights: role_fit 50%, seniority_match 30%, location_match 20%
    return round(role_fit * 0.5 + seniority_match * 0.3 + location_match * 0.2, 2)


def _heuristic_role_fit(job_description: str, profile_skills: list[str]) -> float:
    """Score role fit by keyword overlap between JD and profile skills."""
    if not job_description or not profile_skills:
        # Missing job description should not be treated as a hard mismatch.
        return 3.8 if profile_skills else 3.2

    jd_lower = job_description.lower()
    matched = sum(1 for skill in profile_skills if skill.lower() in jd_lower)
    ratio = min(matched / max(len(profile_skills), 1), 1.0)
    return round(1.0 + ratio * 4.0, 2)


def _heuristic_seniority_match(job_title: str, profile_experience: list | None) -> float:
    """Estimate seniority match from job title keywords and years of experience."""
    jd_seniority = 3  # default: mid-level
    title_lower = (job_title or "").lower()
    for keyword, level in _SENIORITY_KEYWORDS.items():
        if keyword in title_lower:
            jd_seniority = level
            break

    years = 0
    if profile_experience:
        years = len(profile_experience)

    if years >= 8:
        candidate_seniority = 5
    elif years >= 5:
        candidate_seniority = 4
    elif years >= 3:
        candidate_seniority = 3
    elif years >= 1:
        candidate_seniority = 2
    else:
        candidate_seniority = 1

    diff = abs(jd_seniority - candidate_seniority)
    return round(max(5.0 - diff * 1.5, 1.0), 2)


def _heuristic_location_match(
    workplace_type: str | None,
    work_arrangement: list | dict | None,
) -> float:
    """Score location match by comparing job's workplace type to candidate preferences."""
    if not workplace_type:
        # Unknown workplace type is neutral-positive when the user has preferences.
        return 3.8 if work_arrangement else 3.4

    job_type = workplace_type.lower()
    base_score = _REMOTE_SCORE_MAP.get(job_type, 3.0)

    if not work_arrangement:
        return base_score

    preferred = work_arrangement if isinstance(work_arrangement, list) else list(work_arrangement)
    preferred_lower = [str(p).lower() for p in preferred]

    if any(job_type in p or p in job_type for p in preferred_lower):
        return min(base_score + 0.5, 5.0)
    return max(base_score - 1.0, 1.0)


def _heuristic_skills_gap_summary(
    job_description: str,
    profile_skills: list[str],
) -> str:
    """Produce a simple gap summary from unmatched JD technology keywords."""
    if not job_description or not profile_skills:
        return "Insufficient data to produce a gap summary."

    skills_lower = {s.lower() for s in profile_skills}

    # Extract capitalized technical-looking words as potential requirements
    candidates = re.findall(r"\b[A-Z][a-zA-Z0-9+#.]+\b", job_description)
    unmatched = [c for c in candidates if c.lower() not in skills_lower]
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_gaps = []
    for c in unmatched:
        if c.lower() not in seen:
            seen.add(c.lower())
            unique_gaps.append(c)

    top_gaps = unique_gaps[:5]
    if not top_gaps:
        return "No significant skills gaps detected based on profile data."
    return f"Potential gaps (from JD keywords not found in profile): {', '.join(top_gaps)}."


def score_job_fit_preview(job, profile) -> dict:
    """Return a non-persistent heuristic fit score for a job/profile pair."""
    skills = list(profile.skills or []) if profile else []
    experience = list(profile.experience_sections or []) if profile else []
    work_arrangement = getattr(profile, "work_arrangement", None) if profile else None
    has_description = bool((job.description or "").strip())
    has_workplace_type = bool((job.workplace_type or "").strip())

    role_fit = _heuristic_role_fit(job.description or "", skills)
    seniority_match = _heuristic_seniority_match(job.title or "", experience)
    location_match = _heuristic_location_match(job.workplace_type, work_arrangement)
    global_score = _weighted_global(role_fit, seniority_match, location_match)
    skills_gap_summary = _heuristic_skills_gap_summary(job.description or "", skills)
    recommendation = _recommendation_from_score(global_score)
    confidence = "high" if has_description and has_workplace_type else "low"

    # Soften recommendation labels when key job metadata is missing.
    if confidence == "low" and recommendation == _RECOMMEND_AGAINST and global_score >= 3.0:
        recommendation = _RECOMMEND_SPECIFIC_REASON

    return {
        "role_fit": role_fit,
        "seniority_match": seniority_match,
        "location_match": location_match,
        "global_score": global_score,
        "skills_gap_summary": skills_gap_summary,
        "recommendation": recommendation,
        "confidence": confidence,
    }


class JobScoringService:
    def __init__(
        self,
        application_repository,
        job_repository,
        profile_repository,
        resume_repository,
        score_repository,
        llm_client=None,
    ):
        self.application_repository = application_repository
        self.job_repository = job_repository
        self.profile_repository = profile_repository
        self.resume_repository = resume_repository
        self.score_repository = score_repository
        self.llm_client = llm_client

    def score_application(self, application_id, user_id):
        logger.info(f"[JobScoringService] Scoring start application_id={application_id}")

        application = self.application_repository.get_by_id(application_id)
        if not application:
            raise ValueError("Application not found.")
        if str(application.user_id) != str(user_id):
            raise PermissionError("Application does not belong to the current user.")

        job = self.job_repository.get_by_id(application.job_id)
        if not job:
            raise ValueError("Job not found.")

        profile = self.profile_repository.get_by_user_id(user_id)
        resume = None
        if application.resume_id:
            resume = self.resume_repository.get_by_id_and_user_id(application.resume_id, user_id)

        if self.llm_client:
            scores = self._score_with_llm(job, profile, resume)
        else:
            scores = self._score_heuristic(job, profile)

        result = self.score_repository.create_or_update(
            application_id=application_id,
            user_id=user_id,
            **scores,
        )

        logger.info(
            f"[JobScoringService] Scoring complete application_id={application_id} "
            f"global_score={result.global_score} recommendation={result.recommendation}"
        )
        return result

    # ------------------------------------------------------------------
    # LLM-based scoring
    # ------------------------------------------------------------------

    def _score_with_llm(self, job, profile, resume) -> dict:
        skills = list(profile.skills or []) if profile else []
        experience = list(profile.experience_sections or []) if profile else []
        resume_text = (resume.extracted_text or "") if resume else ""

        system_prompt = (
            "You are a career evaluation assistant. Evaluate a job posting against a candidate profile "
            "and return ONLY valid JSON with these fields:\n"
            "  role_fit: float 0-5\n"
            "  seniority_match: float 0-5\n"
            "  location_match: float 0-5\n"
            "  global_score: float 0-5 (weighted: role_fit 50%, seniority_match 30%, location_match 20%)\n"
            "  skills_gap_summary: string (concise, max 2 sentences)\n"
            "  recommendation: one of apply_immediately|worth_applying|apply_if_specific_reason|recommend_against\n"
            "Score interpretation: 4.5+=apply_immediately, 4.0-4.4=worth_applying, "
            "3.5-3.9=apply_if_specific_reason, <3.5=recommend_against. "
            "Return ONLY the JSON object, no explanation."
        )

        user_prompt = (
            f"Job Title: {job.title}\n"
            f"Company: {job.company_name}\n"
            f"Location/Workplace: {job.location or 'unknown'} ({job.workplace_type or 'unknown'})\n"
            f"Job Description (first 1500 chars):\n{(job.description or '')[:1500]}\n\n"
            f"Candidate Skills: {', '.join(skills) if skills else 'not provided'}\n"
            f"Candidate Experience entries: {len(experience)}\n"
            f"Resume excerpt (first 500 chars):\n{resume_text[:500]}\n"
            f"Candidate preferred work arrangement: {getattr(profile, 'work_arrangement', None)}\n"
        )

        raw = self.llm_client.complete(system=system_prompt, user=user_prompt, max_tokens=400)
        if raw:
            scores = self._parse_llm_scores(raw)
            if scores:
                return scores

        logger.warning("[JobScoringService] LLM scoring failed or returned invalid JSON; falling back to heuristics")
        return self._score_heuristic(job, profile)

    def _parse_llm_scores(self, raw: str) -> dict | None:
        try:
            # Strip markdown code fences if present
            cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
            data = json.loads(cleaned)
            return {
                "role_fit": float(data.get("role_fit", 2.5)),
                "seniority_match": float(data.get("seniority_match", 2.5)),
                "location_match": float(data.get("location_match", 2.5)),
                "global_score": float(data.get("global_score", 2.5)),
                "skills_gap_summary": str(data.get("skills_gap_summary", "")),
                "recommendation": str(data.get("recommendation", _RECOMMEND_SPECIFIC_REASON)),
            }
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            logger.warning(f"[JobScoringService] Failed to parse LLM scores: {exc}")
            return None

    # ------------------------------------------------------------------
    # Heuristic scoring (no LLM required)
    # ------------------------------------------------------------------

    def _score_heuristic(self, job, profile) -> dict:
        return score_job_fit_preview(job, profile)
