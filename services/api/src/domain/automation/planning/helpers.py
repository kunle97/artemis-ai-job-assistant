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
    FIELD_ROLE_GITHUB_URL,
    FIELD_ROLE_IGNORE,
    FIELD_ROLE_LAST_NAME,
    FIELD_ROLE_LINKEDIN_URL,
    FIELD_ROLE_LOCATION,
    FIELD_ROLE_OPEN_ENDED,
    FIELD_ROLE_PHONE,
    FIELD_ROLE_PORTFOLIO_URL,
    FIELD_ROLE_PREFERRED_PROGRAMMING_LANGUAGE,
    FIELD_ROLE_REFERRAL_SOURCE,
    FIELD_ROLE_RELOCATION,
    FIELD_ROLE_RESUME_UPLOAD,
    FIELD_ROLE_SALARY_EXPECTATION,
    FIELD_ROLE_STATE_OF_RESIDENCE,
    FIELD_ROLE_SUBMIT,
    FIELD_ROLE_WORK_ARRANGEMENT,
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


def resolve_relocation_value(*, inspected_field: dict, profile) -> str | None:
    """Resolve a relocation question from the candidate profile.

    - If preferred_relocation_cities is a non-empty list → willing to relocate → "Yes"
    - If preferred_relocation_cities is null/empty → not willing → "No"

    Returns "Yes" or "No" so it scores well against typical Yes/No radio options
    and option-matching comboboxes.
    """
    cities = getattr(profile, "preferred_relocation_cities", None)
    if cities:
        return "Yes"
    return "No"


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
    """Resolve a demographic field value from the candidate profile.

    Checks the field ``name`` attribute first (reliable for Lever eeo[*] fields),
    then falls back to label keyword matching. Respects the per-category
    autofill opt-in flags on the profile.
    """
    label = (inspected_field.get("label") or "").strip().lower()
    field_name = (inspected_field.get("name") or "").strip().lower()

    def _is_gender() -> bool:
        return "eeo[gender]" in field_name or "gender" in label

    def _is_race() -> bool:
        return "eeo[race]" in field_name or "race" in label or "ethnicity" in label

    def _is_veteran() -> bool:
        return (
            "eeo[veteran]" in field_name
            or "veteran" in label
            or "protected veteran" in label
        )

    def _is_disability() -> bool:
        return (
            "eeo[disability]" in field_name
            or "disability" in label
            or "individual with a disability" in label
        )

    def _is_pronouns() -> bool:
        return "pronoun" in label or "pronoun" in field_name

    def _is_hispanic_latino() -> bool:
        return "hispanic" in label or "latino" in label

    if _is_gender():
        if not getattr(profile, "autofill_gender", False):
            return None
        return getattr(profile, "gender", None)

    if _is_hispanic_latino():
        # Hispanic/Latino is a prerequisite question on Greenhouse EEOC forms.
        # Derive the Yes/No answer from the stored race value.
        if not getattr(profile, "autofill_race", False):
            return None
        race = getattr(profile, "race", None)
        if not race:
            return None
        race_lower = race.lower()
        if "hispanic" in race_lower or "latino" in race_lower:
            return "Yes"
        return "No"

    if _is_race():
        if not getattr(profile, "autofill_race", False):
            return None
        return getattr(profile, "race", None)

    if _is_veteran():
        if not getattr(profile, "autofill_veteran_status", False):
            return None
        return getattr(profile, "veteran_status", None)

    if _is_disability():
        if not getattr(profile, "autofill_disability_status", False):
            return None
        return getattr(profile, "disability_status", None)

    if _is_pronouns():
        if not getattr(profile, "autofill_pronouns", False):
            return None
        return getattr(profile, "pronouns", None)

    return None


def _build_open_ended_request(*, user_id, question_text, user, profile):
    from src.domain.application_answers.open_ended.models import OpenEndedAnswerRequest

    first_name = getattr(profile, "first_name", None) or getattr(user, "first_name", None)
    last_name = getattr(profile, "last_name", None) or getattr(user, "last_name", None)

    raw_skills = getattr(profile, "skills", None) or []
    skill_names = []
    for s in raw_skills[:10]:
        if isinstance(s, dict):
            skill_names.append(s.get("name") or s.get("label") or "")
        else:
            skill_names.append(str(s))
    skills_summary = ", ".join(filter(None, skill_names)) or None

    experience_sections = getattr(profile, "experience_sections", None) or []
    role_lines = []
    for exp in experience_sections[:2]:
        if isinstance(exp, dict):
            title = exp.get("title") or exp.get("role") or ""
            company = exp.get("company") or exp.get("employer") or ""
            line = " at ".join(filter(None, [title, company]))
            if line:
                role_lines.append(line)
    experience_summary = "; ".join(role_lines) or None

    current_location = None
    city = getattr(profile, "city", None)
    state = getattr(profile, "state", None)
    if city and state:
        current_location = f"{city}, {state}"
    elif city or state:
        current_location = city or state

    preferred_relocation_cities = getattr(profile, "preferred_relocation_cities", None) or []

    return OpenEndedAnswerRequest(
        user_id=user_id,
        question_text=question_text,
        first_name=first_name,
        last_name=last_name,
        skills_summary=skills_summary,
        experience_summary=experience_summary,
        current_location=current_location,
        preferred_relocation_cities=preferred_relocation_cities or None,
    )


def resolve_field_value(
    *,
    classified_role: str,
    inspected_field: dict,
    user,
    profile,
    open_ended_provider=None,
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

    if classified_role == FIELD_ROLE_GITHUB_URL:
        value = getattr(profile, "github_url", None)
        return value, value is None

    if classified_role == FIELD_ROLE_PORTFOLIO_URL:
        value = getattr(profile, "portfolio_url", None) or getattr(profile, "website_url", None)
        return value, value is None

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

    if classified_role == FIELD_ROLE_RELOCATION:
        value = resolve_relocation_value(inspected_field=inspected_field, profile=profile)
        return value, value is None

    if classified_role == FIELD_ROLE_WORK_ARRANGEMENT:
        value = getattr(profile, "work_arrangement", None)
        return value, value is None

    if classified_role == FIELD_ROLE_OPEN_ENDED:
        if open_ended_provider is None:
            return None, True
        question_text = (
            inspected_field.get("label")
            or inspected_field.get("placeholder")
            or ""
        ).strip()
        if not question_text:
            return None, True
        request = _build_open_ended_request(
            user_id=getattr(user, "id", None),
            question_text=question_text,
            user=user,
            profile=profile,
        )
        result = open_ended_provider.get_answer(request)
        if result.answer_text:
            return result.answer_text, result.needs_review
        return None, True

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
