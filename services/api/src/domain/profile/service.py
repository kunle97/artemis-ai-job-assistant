"""
Profile domain service.

Contains business logic for candidate profiles and coordinates profile-related operations.
"""

import logging

from src.domain.profile.repository import CandidateProfileRepository

logger = logging.getLogger(__name__)


class CandidateProfileService:
    def __init__(self, repository: CandidateProfileRepository):
        self.repository = repository

    def get_profile_by_user_id(self, user_id):
        return self.repository.get_by_user_id(user_id)

    def upsert_profile_from_resume(self, user_id, normalized_data: dict) -> dict:
        """
        Create or update a candidate profile from parsed resume data.
        Only fills blank fields — never overwrites existing data.
        Returns a dict with a 'missing_fields' list.
        """
        logger.info("[ProfileService] Upserting profile from resume for user %s", user_id)

        parsed = {
            "phone": normalized_data.get("phone"),
            "linkedin_url": normalized_data.get("linkedin_url"),
            "github_url": normalized_data.get("github_url"),
            "portfolio_url": normalized_data.get("portfolio_url"),
            "skills": normalized_data.get("skills") or [],
            "current_company": normalized_data.get("current_company"),
            "experience_sections": normalized_data.get("experience_sections") or [],
        }

        profile = self.repository.upsert_from_parsed_data(user_id, parsed)

        missing = self._detect_missing_fields(profile, normalized_data)
        logger.info(
            "[ProfileService] Profile upserted for user %s. Missing fields: %s",
            user_id,
            missing or "none",
        )
        return {"missing_fields": missing}

    def _detect_missing_fields(self, profile, normalized_data: dict) -> list[str]:
        """
        Return the names of profile fields that are still blank after the upsert.
        """
        missing = []

        if not profile.phone:
            missing.append("phone")
        if not profile.linkedin_url:
            missing.append("linkedin_url")
        if not profile.github_url:
            missing.append("github_url")
        if not profile.skills:
            missing.append("skills")
        if not profile.city and not profile.state:
            missing.append("location")
        if not profile.work_authorization:
            missing.append("work_authorization")

        return missing