"""
Lever field classifier.
"""

from __future__ import annotations

from src.domain.automation.planning.classifiers.generic import (
    GenericAutomationFieldClassifier,
)
from src.domain.automation.planning.constants import (
    FIELD_ROLE_CONSENT,
    FIELD_ROLE_CURRENT_COMPANY,
    FIELD_ROLE_DEMOGRAPHIC,
    FIELD_ROLE_EMAIL,
    FIELD_ROLE_FULL_NAME,
    FIELD_ROLE_GITHUB_URL,
    FIELD_ROLE_IGNORE,
    FIELD_ROLE_LINKEDIN_URL,
    FIELD_ROLE_LOCATION,
    FIELD_ROLE_OPEN_ENDED,
    FIELD_ROLE_PHONE,
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

        # --- Core identity fields ---
        if field_name == "resume" or "resume/cv" in text:
            return FIELD_ROLE_RESUME_UPLOAD

        if field_name == "name":
            return FIELD_ROLE_FULL_NAME

        if field_name == "email":
            return FIELD_ROLE_EMAIL

        if field_name == "phone":
            return FIELD_ROLE_PHONE

        # --- Location / company ---
        if field_name == "org" or "current company" in text or "current employer" in text:
            return FIELD_ROLE_CURRENT_COMPANY

        if field_name == "location":
            return FIELD_ROLE_LOCATION

        # --- URL fields (Lever uses bracket notation) ---
        if field_name in {"urls[linkedin]", "urls[linkedin url]"}:
            return FIELD_ROLE_LINKEDIN_URL

        if field_name in {"urls[github]", "urls[github url]"}:
            return FIELD_ROLE_GITHUB_URL

        if field_name in {"urls[portfolio]", "urls[portfolio url]", "urls[website]"}:
            return FIELD_ROLE_PORTFOLIO_URL

        # --- Pronouns ---
        if field_name == "pronouns" or "pronoun" in text:
            return FIELD_ROLE_DEMOGRAPHIC

        # --- Referral ---
        if "how did you hear about us" in text or "how did you hear about this" in text:
            return FIELD_ROLE_REFERRAL_SOURCE

        # --- Salary ---
        if (
            "expected compensation range" in text
            or "salary expectation" in text
            or "salary range" in text
            or "desired compensation" in text
        ):
            return FIELD_ROLE_SALARY_EXPECTATION

        # --- Work authorization / sponsorship ---
        if "require sponsorship" in text or "sponsorship to work in the united states" in text:
            return FIELD_ROLE_WORK_AUTHORIZATION

        # --- EEOC / demographic fields ---
        # Lever uses name="eeo[gender]", "eeo[race]", "eeo[veteran]", "eeo[disability]"
        if field_name.startswith("eeo[") or any(
            keyword in text
            for keyword in [
                "gender",
                "race",
                "ethnicity",
                "veteran",
                "disability",
                "protected veteran",
                "individual with a disability",
                "hispanic",
                "latino",
            ]
        ):
            return FIELD_ROLE_DEMOGRAPHIC

        # --- Consent checkboxes ---
        if "i agree" in text or "i consent" in text or "i certify" in text:
            return FIELD_ROLE_CONSENT

        if text in {"loading...", "submit application"}:
            return FIELD_ROLE_IGNORE

        return super().classify(
            field_type=field_type,
            label=label,
            name=name,
            placeholder=placeholder,
        )