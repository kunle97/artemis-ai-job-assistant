"""
Lever field classifier.
"""

from __future__ import annotations

from src.domain.automation.planning.classifiers.generic import (
    GenericAutomationFieldClassifier,
)
from src.domain.automation.planning.constants import (
    FIELD_ROLE_CURRENT_COMPANY,
    FIELD_ROLE_DEMOGRAPHIC,
    FIELD_ROLE_GITHUB_URL,
    FIELD_ROLE_IGNORE,
    FIELD_ROLE_LINKEDIN_URL,
    FIELD_ROLE_LOCATION,
    FIELD_ROLE_OPEN_ENDED,
    FIELD_ROLE_PORTFOLIO_URL,
    FIELD_ROLE_REFERRAL_SOURCE,
    FIELD_ROLE_RESUME_UPLOAD,
    FIELD_ROLE_SALARY_EXPECTATION,
    FIELD_ROLE_WORK_AUTHORIZATION,
)


class LeverAutomationFieldClassifier(GenericAutomationFieldClassifier):
    def classify(self, *, field_type, label, name, placeholder):
        text = " ".join(part for part in [label, name, placeholder] if part).strip().lower()
        field_name = (name or "").strip().lower()

        # Lever custom card questions (name="cards[uuid][fieldN]") are
        # open-ended and must never be matched by label keyword heuristics.
        if field_name.startswith("cards["):
            return FIELD_ROLE_OPEN_ENDED

        if field_name == "resume" or "resume/cv" in text:
            return FIELD_ROLE_RESUME_UPLOAD

        if field_name == "org" or "current company" in text or "current employer" in text:
            return FIELD_ROLE_CURRENT_COMPANY

        if field_name == "location":
            return FIELD_ROLE_LOCATION

        if field_name == "urls[linkedin]":
            return FIELD_ROLE_LINKEDIN_URL

        if field_name == "urls[github]":
            return FIELD_ROLE_GITHUB_URL

        if field_name == "urls[portfolio]":
            return FIELD_ROLE_PORTFOLIO_URL

        if field_name == "pronouns" or "pronoun" in text:
            return FIELD_ROLE_IGNORE

        if "how did you hear about us" in text:
            return FIELD_ROLE_REFERRAL_SOURCE

        if "expected compensation range" in text or "salary expectation" in text:
            return FIELD_ROLE_SALARY_EXPECTATION

        if "require sponsorship" in text or "sponsorship to work in the united states" in text:
            return FIELD_ROLE_WORK_AUTHORIZATION

        if field_name.startswith("eeo[") or any(
            keyword in text for keyword in ["gender", "race", "veteran status", "veteran status select"]
        ):
            return FIELD_ROLE_DEMOGRAPHIC

        if text in {"loading...", "submit application"}:
            return FIELD_ROLE_IGNORE

        return super().classify(
            field_type=field_type,
            label=label,
            name=name,
            placeholder=placeholder,
        )