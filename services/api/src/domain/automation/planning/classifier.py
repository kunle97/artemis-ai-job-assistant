"""
Field classifier.

Maps raw inspected form fields into normalized field roles.
"""

from __future__ import annotations

from src.domain.automation.planning.constants import (
    COMPLIANCE_KEYWORDS,
    CONSENT_KEYWORDS,
    DEMOGRAPHIC_KEYWORDS,
    FIELD_ROLE_COMPLIANCE,
    FIELD_ROLE_CONSENT,
    FIELD_ROLE_COUNTRY,
    FIELD_ROLE_COVER_LETTER_UPLOAD,
    FIELD_ROLE_DEMOGRAPHIC,
    FIELD_ROLE_EMAIL,
    FIELD_ROLE_FIRST_NAME,
    FIELD_ROLE_GITHUB,
    FIELD_ROLE_IGNORE,
    FIELD_ROLE_LAST_NAME,
    FIELD_ROLE_LINKEDIN,
    FIELD_ROLE_LOCATION,
    FIELD_ROLE_OPEN_ENDED,
    FIELD_ROLE_PHONE,
    FIELD_ROLE_PORTFOLIO,
    FIELD_ROLE_RESUME_UPLOAD,
    FIELD_ROLE_SALARY_EXPECTATION,
    FIELD_ROLE_SUBMIT,
    FIELD_ROLE_UNKNOWN,
    FIELD_ROLE_WORK_AUTHORIZATION,
    IGNORE_BUTTON_LABELS,
    SUBMIT_BUTTON_LABELS,
    WORK_AUTH_KEYWORDS,
)


class AutomationFieldClassifier:
    """
    Classify inspected fields into normalized field roles.
    """

    def classify(
        self,
        *,
        field_type: str,
        label: str | None,
        name: str | None,
        placeholder: str | None,
    ) -> str:
        text = " ".join(
            part for part in [label, name, placeholder] if part
        ).strip().lower()

        if field_type == "button":
            if text in IGNORE_BUTTON_LABELS or not text:
                return FIELD_ROLE_IGNORE
            if text in SUBMIT_BUTTON_LABELS:
                return FIELD_ROLE_SUBMIT
            return FIELD_ROLE_IGNORE

        if any(keyword in text for keyword in CONSENT_KEYWORDS):
            return FIELD_ROLE_CONSENT

        if any(keyword in text for keyword in COMPLIANCE_KEYWORDS):
            return FIELD_ROLE_COMPLIANCE

        if any(keyword in text for keyword in DEMOGRAPHIC_KEYWORDS):
            return FIELD_ROLE_DEMOGRAPHIC

        if any(keyword in text for keyword in WORK_AUTH_KEYWORDS):
            return FIELD_ROLE_WORK_AUTHORIZATION

        if "first name" in text:
            return FIELD_ROLE_FIRST_NAME
        if "last name" in text:
            return FIELD_ROLE_LAST_NAME
        if "email" in text:
            return FIELD_ROLE_EMAIL
        if "phone" in text or "mobile" in text:
            return FIELD_ROLE_PHONE
        if "linkedin" in text:
            return FIELD_ROLE_LINKEDIN
        if "github" in text:
            return FIELD_ROLE_GITHUB
        if "portfolio" in text or "website" in text:
            return FIELD_ROLE_PORTFOLIO
        if "country" in text:
            return FIELD_ROLE_COUNTRY
        if "location" in text or "city" in text:
            return FIELD_ROLE_LOCATION
        if "salary" in text or "compensation" in text:
            return FIELD_ROLE_SALARY_EXPECTATION

        if field_type == "file":
            if "cover" in text:
                return FIELD_ROLE_COVER_LETTER_UPLOAD
            return FIELD_ROLE_RESUME_UPLOAD

        if field_type == "textarea":
            return FIELD_ROLE_OPEN_ENDED

        return FIELD_ROLE_UNKNOWN