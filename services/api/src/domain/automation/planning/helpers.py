"""
Helpers for automation planning.

Includes classifier selection, field value resolution, unresolved field filtering,
and platform detection.
"""

from src.domain.automation.planning.classifiers.ashby import AshbyAutomationFieldClassifier
from src.domain.automation.planning.classifiers.greenhouse import GreenhouseAutomationFieldClassifier
from src.domain.automation.planning.classifiers.generic import GenericAutomationFieldClassifier
from src.domain.automation.planning.classifiers.lever import LeverAutomationFieldClassifier
from src.domain.automation.planning.constants import (
    FIELD_ROLE_COMPLIANCE,
    FIELD_ROLE_CONSENT,
    FIELD_ROLE_COUNTRY,
    FIELD_ROLE_COVER_LETTER_UPLOAD,
    FIELD_ROLE_CURRENT_COMPANY,
    FIELD_ROLE_DEMOGRAPHIC,
    FIELD_ROLE_EMAIL,
    FIELD_ROLE_FIRST_NAME,
    FIELD_ROLE_FULL_NAME,
    FIELD_ROLE_IGNORE,
    FIELD_ROLE_LAST_NAME,
    FIELD_ROLE_LINKEDIN_URL,
    FIELD_ROLE_LOCATION,
    FIELD_ROLE_PHONE,
    FIELD_ROLE_PREFERRED_PROGRAMMING_LANGUAGE,
    FIELD_ROLE_REFERRAL_SOURCE,
    FIELD_ROLE_RESUME_UPLOAD,
    FIELD_ROLE_SALARY_EXPECTATION,
    FIELD_ROLE_STATE_OF_RESIDENCE,
    FIELD_ROLE_SUBMIT,
    FIELD_ROLE_WORK_AUTHORIZATION,
    FIELD_ROLE_ZIP_CODE,
)


def get_classifier_for_url(application_url: str):
    lowered = (application_url or "").lower()

    if "greenhouse" in lowered:
        return GreenhouseAutomationFieldClassifier()

    if "ashbyhq" in lowered or "ashby" in lowered:
        return AshbyAutomationFieldClassifier()

    if "lever.co" in lowered:
        return LeverAutomationFieldClassifier()

    return GenericAutomationFieldClassifier()


def resolve_salary_value(*, profile) -> str | None:
    """Return a salary string from profile.salary_target.

    Handles several stored formats:
    - Already a range:  "120000-150000" or "120,000 - 150,000"  → returned as-is
    - Plain number:     "120000" or "$120,000"                   → returned as-is
    - None / empty                                               → None
    """
    import re

    raw = getattr(profile, "salary_target", None)
    if not raw:
        return None

    value = str(raw).strip()
    if not value:
        return None

    # Strip leading/trailing whitespace but preserve the value structure
    # — let the field accept whatever the user stored (range or single number)
    # Normalise common formatting so it reads cleanly: remove extra spaces around dashes
    value = re.sub(r"\s*[-–—]\s*", " - ", value)
    return value


def resolve_work_authorization_value(*, inspected_field: dict, profile) -> str | None:
    label = (inspected_field.get("label") or "").strip().lower()

    if "authorized to work" in label or "lawfully in the united states" in label:
        return getattr(profile, "work_authorization", None)

    if "sponsor" in label or "sponsorship" in label or "immigration case" in label:
        return getattr(profile, "visa_sponsorship", None)

    return None


def resolve_compliance_value(*, inspected_field: dict, profile) -> str | None:
    return None


def resolve_consent_value(*, inspected_field: dict, profile) -> str | None:
    return None


def resolve_demographic_value(*, inspected_field: dict, profile) -> str | None:
    label = (inspected_field.get("label") or "").strip().lower()

    if "gender" in label:
        return getattr(profile, "gender", None)

    if "race" in label or "ethnicity" in label:
        return getattr(profile, "race", None)

    if "veteran" in label:
        return getattr(profile, "veteran_status", None)

    if "disability" in label:
        return getattr(profile, "disability_status", None)

    return None


def resolve_field_value(
    *,
    classified_role: str,
    inspected_field: dict,
    user,
    profile,
) -> tuple[str | None, bool]:
    if classified_role in {FIELD_ROLE_IGNORE, FIELD_ROLE_SUBMIT, FIELD_ROLE_COVER_LETTER_UPLOAD}:
        return None, False

    if classified_role == FIELD_ROLE_RESUME_UPLOAD:
        return inspected_field.get("resolved_value"), False

    if classified_role == FIELD_ROLE_FIRST_NAME:
        return getattr(profile, "first_name", None) or getattr(user, "first_name", None), False

    if classified_role == FIELD_ROLE_LAST_NAME:
        return getattr(profile, "last_name", None) or getattr(user, "last_name", None), False

    if classified_role == FIELD_ROLE_FULL_NAME:
        full_name = getattr(profile, "full_name", None)
        if full_name:
            return full_name, False

        first = getattr(profile, "first_name", None) or getattr(user, "first_name", None) or ""
        last = getattr(profile, "last_name", None) or getattr(user, "last_name", None) or ""
        combined = f"{first} {last}".strip()
        return combined or None, False

    if classified_role == FIELD_ROLE_EMAIL:
        return getattr(profile, "email", None) or getattr(user, "email", None), False

    if classified_role == FIELD_ROLE_PHONE:
        return getattr(profile, "phone", None), False

    if classified_role == FIELD_ROLE_LINKEDIN_URL:
        return getattr(profile, "linkedin_url", None), False

    if classified_role == FIELD_ROLE_LOCATION:
        return getattr(profile, "location", None), False

    if classified_role == FIELD_ROLE_CURRENT_COMPANY:
        value = getattr(profile, "current_company", None)
        return value, value is None

    if classified_role == FIELD_ROLE_COUNTRY:
        value = getattr(profile, "country", None)
        return value, value is None

    if classified_role == FIELD_ROLE_PREFERRED_PROGRAMMING_LANGUAGE:
        skills = getattr(profile, "skills", None) or []

        if isinstance(skills, list) and skills:
            first = skills[0]
            # skills may be plain strings or dicts with a "name" key
            if isinstance(first, dict):
                value = first.get("name") or first.get("label") or first.get("skill")
            else:
                value = str(first) if first else None
            return value, value is None

        return None, True

    if classified_role == FIELD_ROLE_SALARY_EXPECTATION:
        value = resolve_salary_value(profile=profile)
        return value, value is None

    if classified_role == FIELD_ROLE_REFERRAL_SOURCE:
        return None, True

    if classified_role == FIELD_ROLE_STATE_OF_RESIDENCE:
        value = getattr(profile, "state", None)
        return value, value is None

    if classified_role == FIELD_ROLE_ZIP_CODE:
        value = getattr(profile, "zip_code", None)
        return str(value) if value is not None else None, value is None

    if classified_role == FIELD_ROLE_WORK_AUTHORIZATION:
        value = resolve_work_authorization_value(
            inspected_field=inspected_field,
            profile=profile,
        )
        return value, value is None

    if classified_role == FIELD_ROLE_COMPLIANCE:
        value = resolve_compliance_value(
            inspected_field=inspected_field,
            profile=profile,
        )
        return value, value is None

    if classified_role == FIELD_ROLE_CONSENT:
        value = resolve_consent_value(
            inspected_field=inspected_field,
            profile=profile,
        )
        return value, value is None

    if classified_role == FIELD_ROLE_DEMOGRAPHIC:
        value = resolve_demographic_value(
            inspected_field=inspected_field,
            profile=profile,
        )
        return value, value is None

    return None, True


def detect_platform_name(application_url: str) -> str:
    lowered = application_url.lower()

    if "greenhouse" in lowered:
        return "greenhouse"
    if "ashbyhq" in lowered or "ashby" in lowered:
        return "ashby"
    if "lever" in lowered:
        return "lever"

    return "generic"


_NOISY_ROLES = {
    "ignore",
    "submit_action",
    "open_ended_question",
}

_NOISY_LABELS = {
    "",
    "select...",
    "toggle flyout",
    "attach",
    "dropbox",
    "google drive",
    "enter manually",
    "locate me",
    "other website",
    "other",
    "additional information",
    "pronouns",
}


def should_include_unresolved_field(field: dict) -> bool:
    label = (field.get("label") or "").strip().lower()
    role = field.get("classified_role")
    status = field.get("fill_status")

    if status not in {
        "skipped_review",
        "skipped_no_value",
        "skipped_option_not_applied",
        "skipped_option_not_found",
        "skipped_not_found",
        "skipped_unknown_type",
        "error",
    }:
        return False

    if role in _NOISY_ROLES:
        return False

    # Unknown fields with no classifiable role are UI noise — not actionable
    if role == "unknown" and status == "skipped_review":
        return False

    if label in _NOISY_LABELS:
        return False

    return True


def build_unresolved_reason(field: dict) -> str:
    status = field.get("fill_status")

    if status == "skipped_no_value":
        return "No value is currently stored for this field."

    if status == "skipped_option_not_applied":
        return "Resolved a value, but Artemis could not reliably apply it in the UI."

    if status == "skipped_option_not_found":
        return "Resolved a value, but no matching selectable option was found on the page."

    if status == "skipped_not_found":
        return "The target field could not be located on the page."

    if status == "skipped_unknown_type":
        return "This field type is not yet supported by the fill engine."

    if status == "error":
        return "An unexpected automation error occurred while trying to fill this field."

    return "This field requires user review before filling."
