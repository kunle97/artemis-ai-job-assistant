"""
Candidate profile repository.
"""

from __future__ import annotations

from src.domain.profile.models import CandidateProfile


class CandidateProfileRepository:
    def __init__(self, db):
        self.db = db

    def get_by_user_id(self, user_id):
        return (
            self.db.query(CandidateProfile)
            .filter(CandidateProfile.user_id == user_id)
            .first()
        )

    def get_or_create_by_user_id(self, user_id):
        profile = self.get_by_user_id(user_id)
        if profile:
            return profile

        profile = CandidateProfile(user_id=user_id)
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def upsert_by_user_id(self, user_id, payload):
        profile = self.get_or_create_by_user_id(user_id)

        if payload.phone is not None:
            profile.phone = payload.phone
        if payload.linkedin_url is not None:
            profile.linkedin_url = payload.linkedin_url
        if payload.github_url is not None:
            profile.github_url = payload.github_url
        if payload.portfolio_url is not None:
            profile.portfolio_url = payload.portfolio_url

        if payload.city is not None:
            profile.city = payload.city
        if payload.state is not None:
            profile.state = payload.state
        if payload.country is not None:
            profile.country = payload.country
        if payload.zip_code is not None:
            profile.zip_code = payload.zip_code

        if payload.salary_target is not None:
            profile.salary_target = payload.salary_target

        if payload.gender is not None:
            profile.gender = payload.gender
        if payload.race is not None:
            profile.race = payload.race
        if payload.veteran_status is not None:
            profile.veteran_status = payload.veteran_status
        if payload.disability_status is not None:
            profile.disability_status = payload.disability_status
        if payload.pronouns is not None:
            profile.pronouns = payload.pronouns

        if payload.autofill_gender is not None:
            profile.autofill_gender = payload.autofill_gender
        if payload.autofill_race is not None:
            profile.autofill_race = payload.autofill_race
        if payload.autofill_veteran_status is not None:
            profile.autofill_veteran_status = payload.autofill_veteran_status
        if payload.autofill_disability_status is not None:
            profile.autofill_disability_status = payload.autofill_disability_status
        if payload.autofill_pronouns is not None:
            profile.autofill_pronouns = payload.autofill_pronouns

        if payload.preferred_relocation_cities is not None:
            profile.preferred_relocation_cities = payload.preferred_relocation_cities
        if payload.work_arrangement is not None:
            profile.work_arrangement = payload.work_arrangement

        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def upsert_from_parsed_data(self, user_id, parsed: dict):
        """
        Create or update a profile using fields parsed from a resume.
        Only fills blank fields — never overwrites existing data.
        """
        profile = self.get_or_create_by_user_id(user_id)

        def _fill(current, incoming):
            if current is None or current == "" or current == []:
                return incoming
            return current

        # Phone: always use the resume value when present (the resume is authoritative).
        if parsed.get("phone"):
            profile.phone = parsed["phone"]
        profile.linkedin_url = _fill(profile.linkedin_url, parsed.get("linkedin_url"))
        profile.github_url = _fill(profile.github_url, parsed.get("github_url"))
        profile.portfolio_url = _fill(profile.portfolio_url, parsed.get("portfolio_url"))
        profile.current_company = _fill(profile.current_company, parsed.get("current_company"))

        incoming_exp = parsed.get("experience_sections") or []
        if incoming_exp and not (profile.experience_sections or []):
            profile.experience_sections = incoming_exp

        incoming_skills = parsed.get("skills") or []
        existing_skills = profile.skills or []
        merged = existing_skills + [s for s in incoming_skills if s not in existing_skills]
        profile.skills = merged or None

        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile