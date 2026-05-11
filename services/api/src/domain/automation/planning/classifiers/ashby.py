"""
Ashby field classifier.

Handles Ashby-specific field naming and labels.
"""

from src.domain.automation.planning.base_classifier import BaseAutomationFieldClassifier
from src.domain.automation.planning.constants import (
    FIELD_ROLE_COMPLIANCE,
    FIELD_ROLE_CONSENT,
    FIELD_ROLE_COUNTRY,
    FIELD_ROLE_COVER_LETTER_UPLOAD,
    FIELD_ROLE_DEMOGRAPHIC,
    FIELD_ROLE_DESIRED_START_DATE,
    FIELD_ROLE_EMAIL,
    FIELD_ROLE_FIRST_NAME,
    FIELD_ROLE_FULL_NAME,
    FIELD_ROLE_GITHUB,
    FIELD_ROLE_IGNORE,
    FIELD_ROLE_JOB_SEARCH_STATUS,
    FIELD_ROLE_LAST_NAME,
    FIELD_ROLE_LINKEDIN,
    FIELD_ROLE_LOCATION,
    FIELD_ROLE_OPEN_ENDED,
    FIELD_ROLE_PHONE,
    FIELD_ROLE_PORTFOLIO,
    FIELD_ROLE_PREFERRED_OFFICE_LOCATION,
    FIELD_ROLE_REFERRAL_SOURCE,
    FIELD_ROLE_RELOCATION,
    FIELD_ROLE_RESUME_UPLOAD,
    FIELD_ROLE_SALARY_EXPECTATION,
    FIELD_ROLE_SUBMIT,
    FIELD_ROLE_UNKNOWN,
    FIELD_ROLE_AREA_OF_EXPERTISE,
    FIELD_ROLE_WORK_AUTHORIZATION,
    IGNORE_BUTTON_LABELS,
    SUBMIT_BUTTON_LABELS,
)


class AshbyAutomationFieldClassifier(BaseAutomationFieldClassifier):
    def classify(self, *, field_type, label, name, placeholder):
        text = " ".join(filter(None, [label, name, placeholder])).lower().strip()

        if field_type == "button":
            if text in IGNORE_BUTTON_LABELS or not text:
                return FIELD_ROLE_IGNORE
            if text in SUBMIT_BUTTON_LABELS:
                return FIELD_ROLE_SUBMIT
            return FIELD_ROLE_IGNORE

        if "preferred pronouns" in text:
            return FIELD_ROLE_DEMOGRAPHIC

        if "gender" in text or "ethnicity" in text or "disability" in text or "race" in text or "veteran" in text or "hispanic" in text or "latino" in text:
            return FIELD_ROLE_DEMOGRAPHIC

        if "consent" in text:
            return FIELD_ROLE_CONSENT

        if "privacy" in text or "confidentiality" in text:
            return FIELD_ROLE_COMPLIANCE

        if "visa" in text or "sponsorship" in text or "authorized to work" in text:
            return FIELD_ROLE_WORK_AUTHORIZATION

        if text == "name" or "_systemfield_name" in text or "full name" in text:
            return FIELD_ROLE_FULL_NAME

        if "first name" in text:
            return FIELD_ROLE_FIRST_NAME

        if "last name" in text:
            return FIELD_ROLE_LAST_NAME

        if text == "email" or "_systemfield_email" in text or "email" in text:
            return FIELD_ROLE_EMAIL

        if "phone" in text:
            return FIELD_ROLE_PHONE

        if "linkedin" in text and "portfolio" in text and "website" in text:
            return FIELD_ROLE_LINKEDIN

        if "linkedin" in text:
            return FIELD_ROLE_LINKEDIN

        if "github" in text:
            return FIELD_ROLE_GITHUB

        if "portfolio" in text or "personal website" in text or "website" in text:
            return FIELD_ROLE_PORTFOLIO

        if "country" in text:
            return FIELD_ROLE_COUNTRY

        if "where do you plan on working from" in text:
            return FIELD_ROLE_LOCATION

        if "location" in text or "city" in text:
            return FIELD_ROLE_LOCATION

        if "salary" in text or "compensation" in text:
            return FIELD_ROLE_SALARY_EXPECTATION

        if "desired start date" in text or "available start date" in text or "when can you start" in text or "start date" in text:
            return FIELD_ROLE_DESIRED_START_DATE

        if "job search status" in text:
            return FIELD_ROLE_JOB_SEARCH_STATUS

        if "area of expertise" in text:
            return FIELD_ROLE_AREA_OF_EXPERTISE

        if "how did you hear about" in text:
            return FIELD_ROLE_REFERRAL_SOURCE

        if field_type == "file":
            if "cover" in text:
                return FIELD_ROLE_COVER_LETTER_UPLOAD
            return FIELD_ROLE_RESUME_UPLOAD

        if field_type == "textarea":
            return FIELD_ROLE_OPEN_ENDED

        if field_type == "select_like":
            if "country" in text:
                return FIELD_ROLE_COUNTRY
            if "location" in text or "city" in text:
                return FIELD_ROLE_LOCATION

        if field_type == "select":
            if "country" in text:
                return FIELD_ROLE_COUNTRY
            if "location" in text or "city" in text:
                return FIELD_ROLE_LOCATION
            if "how did you hear about" in text:
                return FIELD_ROLE_REFERRAL_SOURCE

        if field_type == "checkbox_group":
            # Detect location-preference checkbox groups via the group label.
            # When the label is null/empty the planning service will inspect options.
            if "location" in text or "where" in text or "office" in text or "city" in text or "prefer" in text:
                return FIELD_ROLE_PREFERRED_OFFICE_LOCATION
            return FIELD_ROLE_UNKNOWN

        if field_type == "checkbox":
            if "consent" in text or "agree" in text or "acknowledge" in text:
                return FIELD_ROLE_CONSENT
            if "privacy" in text:
                return FIELD_ROLE_COMPLIANCE
            return FIELD_ROLE_UNKNOWN

        if field_type == "radio_group":
            if "gender" in text or "ethnicity" in text or "race" in text or "veteran" in text or "disability" in text:
                return FIELD_ROLE_DEMOGRAPHIC
            if "visa" in text or "sponsorship" in text or "authorized to work" in text:
                return FIELD_ROLE_WORK_AUTHORIZATION
            if "relocat" in text:
                return FIELD_ROLE_RELOCATION
            if "consent" in text:
                return FIELD_ROLE_CONSENT

        return FIELD_ROLE_UNKNOWN