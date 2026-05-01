"""
Greenhouse field classifier.
"""

from __future__ import annotations

from src.domain.automation.planning.classifiers.generic import (
    GenericAutomationFieldClassifier,
)
from src.domain.automation.planning.constants import (
    FIELD_ROLE_COMPLIANCE,
    FIELD_ROLE_CONSENT,
    FIELD_ROLE_COUNTRY,
    FIELD_ROLE_COVER_LETTER_UPLOAD,
    FIELD_ROLE_DEMOGRAPHIC,
    FIELD_ROLE_IGNORE,
    FIELD_ROLE_PREFERRED_PROGRAMMING_LANGUAGE,
    FIELD_ROLE_REFERRAL_SOURCE,
    FIELD_ROLE_RESUME_UPLOAD,
    FIELD_ROLE_STATE_OF_RESIDENCE,
    FIELD_ROLE_WORK_AUTHORIZATION,
    FIELD_ROLE_ZIP_CODE,
)


class GreenhouseAutomationFieldClassifier(GenericAutomationFieldClassifier):
    """
    Greenhouse-aware classifier.

    Keeps Greenhouse-specific overrides on top of generic behavior.
    """

    def classify(self, *, field_type, label, name, placeholder):
        text = " ".join(
            part for part in [label, name, placeholder] if part
        ).strip().lower()

        if field_type == "button" and text in {
            "attach",
            "upload",
            "upload file",
            "dropbox",
            "google drive",
            "enter manually",
            "toggle flyout",
        }:
            return FIELD_ROLE_IGNORE

        if "country" in text and "city, country" not in text:
            return FIELD_ROLE_COUNTRY

        if field_type == "file":
            if any(token in text for token in ["cover letter", "cover-letter"]):
                return FIELD_ROLE_COVER_LETTER_UPLOAD

            if any(token in text for token in ["resume", "cv", "resume/cv"]):
                return FIELD_ROLE_RESUME_UPLOAD

            return "unknown"

        if any(
            phrase in text
            for phrase in [
                "prepared or submitted in whole or in part by an ai",
                "language model",
                "automated agent",
                "ai system",
                "acknowledge",
                "confirm",
            ]
        ):
            return FIELD_ROLE_COMPLIANCE

        if any(
            phrase in text
            for phrase in [
                "i consent",
                "i do not consent",
                "receive communications via sms",
                "receive communications via text",
                "record and transcribe interviews",
                "prefer not to be recorded",
                "notetaker",
            ]
        ):
            return FIELD_ROLE_CONSENT

        if any(
            keyword in text
            for keyword in [
                "gender",
                "ethnicity",
                "sexual orientation",
                "transgender",
                "disability",
                "physical disability",
                "nationality",
                "race",
                "veteran status",
                "pronoun",
                "hispanic",
                "latino",
            ]
        ):
            return FIELD_ROLE_DEMOGRAPHIC

        if any(
            phrase in text
            for phrase in [
                "authorized to work",
                "lawfully in the united states",
                "require calendly to commence",
                "sponsor an immigration case",
                "employment-based visa",
                "sponsorship",
            ]
        ):
            return FIELD_ROLE_WORK_AUTHORIZATION

        if any(
            phrase in text
            for phrase in [
                "state where you will reside",
                "state where you will reside and work",
                "select the state where you will reside",
                "permanent residency",
            ]
        ):
            return FIELD_ROLE_STATE_OF_RESIDENCE

        if "zip code" in text or "postal code" in text:
            return FIELD_ROLE_ZIP_CODE

        if "preferred programming language" in text:
            return FIELD_ROLE_PREFERRED_PROGRAMMING_LANGUAGE

        if "how did you hear about this job" in text:
            return FIELD_ROLE_REFERRAL_SOURCE

        return super().classify(
            field_type=field_type,
            label=label,
            name=name,
            placeholder=placeholder,
        )