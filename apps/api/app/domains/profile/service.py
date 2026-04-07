"""
Profile domain service.

Contains business logic for candidate profiles and coordinates profile-related operations.
"""

from app.domains.profile.repository import CandidateProfileRepository
from app.domains.profile.schemas import CandidateProfileCreate


class CandidateProfileService:
    def __init__(self, repository: CandidateProfileRepository):
        self.repository = repository

    def get_profile_by_user_id(self, user_id):
        return self.repository.get_by_user_id(user_id)

    def create_profile(self, payload: CandidateProfileCreate):
        existing_profile = self.repository.get_by_user_id(payload.user_id)
        if existing_profile:
            raise ValueError("This user already has a candidate profile.")

        return self.repository.create(**payload.model_dump())

    def upsert_profile_from_resume(self, user_id, normalized_data: dict):
        """
        Create or update a candidate profile from parsed resume data.

        Rules:
        - do not overwrite existing populated fields with empty values
        - merge skills without duplicates
        - map detected URLs into likely profile fields
        """
        existing_profile = self.repository.get_by_user_id(user_id)
        mapped_data = self._map_resume_data_to_profile_fields(normalized_data)

        if not existing_profile:
            return self.repository.create(
                user_id=user_id,
                phone=mapped_data["phone"],
                location=mapped_data["location"],
                linkedin_url=mapped_data["linkedin_url"],
                github_url=mapped_data["github_url"],
                portfolio_url=mapped_data["portfolio_url"],
                years_experience=mapped_data["years_experience"],
                work_authorization=None,
                requires_sponsorship=False,
                current_title=mapped_data["current_title"],
                summary=mapped_data["summary"],
                skills=mapped_data["skills"],
                industries=[],
                target_titles=[],
                remote_preference=None,
                salary_min=None,
                salary_target=None,
                default_answers={},
            )

        update_data = {
            "phone": self._prefer_existing(existing_profile.phone, mapped_data["phone"]),
            "linkedin_url": self._prefer_existing(
                existing_profile.linkedin_url,
                mapped_data["linkedin_url"],
            ),
            "github_url": self._prefer_existing(
                existing_profile.github_url,
                mapped_data["github_url"],
            ),
            "portfolio_url": self._prefer_existing(
                existing_profile.portfolio_url,
                mapped_data["portfolio_url"],
            ),
            "years_experience": self._prefer_existing(
                existing_profile.years_experience,
                mapped_data["years_experience"],
            ),
            "current_title": self._prefer_existing(
                existing_profile.current_title,
                mapped_data["current_title"],
            ),
            "summary": self._prefer_existing(
                existing_profile.summary,
                mapped_data["summary"],
            ),
            "skills": self._merge_lists(
                existing_profile.skills or [],
                mapped_data["skills"],
            ),
        }

        return self.repository.update(existing_profile, **update_data)

    def _map_resume_data_to_profile_fields(self, normalized_data: dict) -> dict:
        """
        Map normalized resume data into candidate profile fields.
        """
        years_experience = normalized_data.get("years_experience")
        if years_experience is not None:
            years_experience = int(years_experience)

        return {
            "phone": normalized_data.get("phone"),
            "location": None,
            "linkedin_url": normalized_data.get("linkedin_url"),
            "github_url": normalized_data.get("github_url"),
            "portfolio_url": normalized_data.get("portfolio_url"),
            "years_experience": years_experience,
            "current_title": normalized_data.get("headline_title")
            or normalized_data.get("current_job_title"),
            "summary": normalized_data.get("summary"),
            "skills": normalized_data.get("skills", []),
        }

    def _prefer_existing(self, existing_value, incoming_value):
        """
        Keep the existing value when it is already populated;
        otherwise use the incoming value.
        """
        if existing_value is not None and existing_value != "":
            return existing_value
        return incoming_value

    def _merge_lists(self, existing: list, incoming: list) -> list:
        merged = []
        for value in existing + incoming:
            if value not in merged:
                merged.append(value)
        return merged