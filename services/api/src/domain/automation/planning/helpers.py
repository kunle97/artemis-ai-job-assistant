"""
Helpers for automation planning.

Includes classifier selection, field value resolution, unresolved field filtering,
and platform detection.
"""

import re

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


def _parse_money_amount(raw: str | int | float | None) -> int | None:
    if raw is None:
        return None
    text = str(raw).strip().lower()
    if not text:
        return None

    multiplier = 1000 if text.endswith("k") else 1
    text = text.rstrip("k")
    text = re.sub(r"[^\d.]", "", text)
    if not text:
        return None
    try:
        return int(float(text) * multiplier)
    except ValueError:
        return None


def _extract_money_amounts(text: str | None) -> list[int]:
    if not text:
        return []
    matches = re.findall(r"\$?\s*\d[\d,]*(?:\.\d+)?\s*[kK]?", text)
    values = []
    for match in matches:
        amount = _parse_money_amount(match)
        if amount is not None:
            values.append(amount)
    return values


def _parse_salary_range(raw: str | None) -> tuple[int, int] | None:
    if not raw:
        return None
    amounts = _extract_money_amounts(raw)
    if not amounts:
        return None
    if len(amounts) == 1:
        return amounts[0], amounts[0]
    return min(amounts[0], amounts[1]), max(amounts[0], amounts[1])


def resolve_salary_expectation_value(*, inspected_field: dict, profile) -> str | None:
    label = (inspected_field.get("label") or "").strip().lower()
    profile_salary = resolve_salary_value(profile=profile)

    binary_salary_question = any(
        token in label
        for token in [
            "align with your compensation expectations",
            "compensation expectations",
            "does this align",
        ]
    ) or (
        _is_binary_yes_no_field(inspected_field)
        and any(token in label for token in ["salary", "compensation"])
    )
    if not binary_salary_question:
        return profile_salary

    offered_range = _parse_salary_range(label)
    desired_range = _parse_salary_range(profile_salary)
    min_salary = _parse_money_amount(getattr(profile, "min_salary", None))
    if not offered_range or not desired_range:
        return profile_salary

    _, offered_max = offered_range
    desired_min, _ = desired_range
    floor = min_salary or desired_min
    return "Yes" if offered_max >= floor else "No"


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
    work_auth_value = getattr(profile, "work_authorization", None)
    visa_value = getattr(profile, "visa_sponsorship", None)

    def _coerce_work_auth_to_yes_no(value: str | None) -> str | None:
        normalized = _normalize_binary_text(value)
        if not normalized:
            return None

        if any(
            token in normalized
            for token in [
                "us citizen",
                "u s citizen",
                "citizen",
                "green card",
                "permanent resident",
                "authorized",
                "work authorized",
            ]
        ):
            return "Yes"

        if any(
            token in normalized
            for token in [
                "not authorized",
                "no authorization",
                "cannot work",
                "ineligible",
            ]
        ):
            return "No"

        return _coerce_yes_no_answer(value)

    if any(
        token in label
        for token in [
            "authorized to work",
            "lawfully in the united states",
            "legally authorized",
            "leagally authorized",
            "legal authorization",
        ]
    ):
        if _is_binary_yes_no_field(inspected_field):
            coerced = _coerce_work_auth_to_yes_no(work_auth_value)
            if coerced:
                return coerced
        return work_auth_value

    if any(
        token in label
        for token in ["sponsor", "sponsorship", "immigration case", "visa status"]
    ):
        if _is_binary_yes_no_field(inspected_field):
            coerced = _coerce_yes_no_answer(visa_value)
            if coerced:
                return coerced
        return visa_value

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


def _normalize_work_arrangement_values(raw_value) -> tuple[list[str], str | None]:
    if raw_value is None:
        return [], None

    if isinstance(raw_value, (list, tuple, set)):
        raw_items = [str(item).strip() for item in raw_value if str(item).strip()]
        display = ", ".join(raw_items) or None
    else:
        display = str(raw_value).strip() or None
        raw_items = re.split(r"[,/|]", display or "")
        raw_items = [item.strip() for item in raw_items if item.strip()]

    normalized: list[str] = []
    for item in raw_items:
        lowered = item.lower()
        if "hybrid" in lowered:
            normalized.append("hybrid")
        elif any(token in lowered for token in ["on-site", "onsite", "in office", "in-office"]):
            normalized.append("onsite")
        elif "remote" in lowered:
            normalized.append("remote")
        else:
            normalized.append(lowered)

    return normalized, display


def _question_requires_office_presence(label: str) -> bool:
    lowered = (label or "").lower()
    return any(
        token in lowered
        for token in [
            "hybrid culture",
            "commutable distance",
            "in person collaboration",
            "in-person collaboration",
            "work out of our",
            "office monday",
            "days per week in manhattan",
            "days a week in the office",
            "our ny office",
            "our new york office",
        ]
    )


def _question_mentions_nyc_area(label: str) -> bool:
    lowered = (label or "").lower()
    return any(
        token in lowered
        for token in ["new york", "ny office", "manhattan", "manhatten", "nyc"]
    )


def _profile_matches_nyc_area(profile) -> bool | None:
    city = (getattr(profile, "city", None) or "").strip().lower()
    state = (getattr(profile, "state", None) or "").strip().lower()
    relocation_cities = getattr(profile, "preferred_relocation_cities", None) or []
    normalized_relocation = " ".join(str(city_name).strip().lower() for city_name in relocation_cities)

    nyc_cities = {
        "new york",
        "manhattan",
        "brooklyn",
        "queens",
        "bronx",
        "staten island",
        "jersey city",
        "hoboken",
        "newark",
    }
    if city in nyc_cities:
        return True
    if city and state in {"ny", "new york", "nj", "new jersey"} and city in nyc_cities:
        return True
    if any(token in normalized_relocation for token in nyc_cities):
        return True
    if city or state or normalized_relocation:
        return False
    return None


def resolve_work_arrangement_value(*, inspected_field: dict, profile) -> str | None:
    normalized_prefs, display = _normalize_work_arrangement_values(
        getattr(profile, "work_arrangement", None)
    )
    label = (inspected_field.get("label") or "").strip()
    requires_office_presence = _question_requires_office_presence(label)
    is_binary = _is_binary_yes_no_field(inspected_field)

    if not normalized_prefs and not display and not requires_office_presence:
        return None

    if not requires_office_presence and not is_binary:
        return display

    if not requires_office_presence:
        return display

    if _question_mentions_nyc_area(label):
        location_match = _profile_matches_nyc_area(profile)
        if location_match is True:
            return "Yes"
        if location_match is False:
            return "No"

    if any(pref in {"hybrid", "onsite"} for pref in normalized_prefs):
        if _question_mentions_nyc_area(label):
            return None
        return "Yes"

    if "remote" in normalized_prefs:
        return "No"

    return None


def _build_open_ended_request(*, user_id, question_text, user, profile, page_title=None, job_context=None):
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
    current_company = getattr(profile, "current_company", None)
    work_arrangement = getattr(profile, "work_arrangement", None)
    salary_target = resolve_salary_value(profile=profile)

    work_arrangement_text = None
    if isinstance(work_arrangement, list):
        cleaned = [str(item).strip() for item in work_arrangement if str(item).strip()]
        work_arrangement_text = ", ".join(cleaned) if cleaned else None
    elif work_arrangement:
        work_arrangement_text = str(work_arrangement)

    return OpenEndedAnswerRequest(
        user_id=user_id,
        question_text=question_text,
        first_name=first_name,
        last_name=last_name,
        skills_summary=skills_summary,
        experience_summary=experience_summary,
        current_location=current_location,
        preferred_relocation_cities=preferred_relocation_cities or None,
        current_company=current_company,
        work_arrangement=work_arrangement_text,
        salary_target=salary_target,
        page_title=page_title,
        job_context=job_context,
    )


def _looks_like_open_ended_question(inspected_field: dict) -> bool:
    field_type = (inspected_field.get("field_type") or "").strip().lower()
    if field_type != "textarea":
        return False

    question_text = (
        inspected_field.get("label")
        or inspected_field.get("placeholder")
        or inspected_field.get("name")
        or ""
    )
    normalized = _normalize_binary_text(question_text)
    if not normalized:
        return False

    return any(
        token in normalized
        for token in [
            "why are you interested",
            "why do you want",
            "why this company",
            "why this role",
            "why us",
            "tell us about",
            "what excites you",
            "project or accomplishment",
        ]
    )


def _normalize_binary_text(text: str | None) -> str:
    if not text:
        return ""
    normalized = text.strip().lower()
    normalized = normalized.replace("’", "'")
    normalized = normalized.replace("don't", "do not")
    normalized = normalized.replace("dont", "do not")
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = " ".join(normalized.split())
    return normalized


def _iter_option_texts(options: list | None) -> list[str]:
    if not options:
        return []

    texts: list[str] = []
    for option in options:
        if isinstance(option, dict):
            label = option.get("label")
            value = option.get("value")
            if label:
                texts.append(str(label))
            elif value:
                texts.append(str(value))
        elif option is not None:
            texts.append(str(option))
    return texts


def _is_binary_yes_no_field(inspected_field: dict) -> bool:
    field_type = (inspected_field.get("field_type") or "").strip().lower()
    if field_type not in {"select", "select_like", "radio_group"}:
        return False

    option_texts = _iter_option_texts(inspected_field.get("options"))
    normalized = [_normalize_binary_text(text) for text in option_texts if text]
    has_yes = any(text in {"yes", "y"} or text.startswith("yes ") for text in normalized)
    has_no = any(text in {"no", "n"} or text.startswith("no ") for text in normalized)
    if has_yes and has_no:
        return True

    # Inspector may not always return option lists for comboboxes.
    # In that case, allow a conservative label-based yes/no fallback trigger.
    question_text = _normalize_binary_text(
        inspected_field.get("label")
        or inspected_field.get("placeholder")
        or inspected_field.get("name")
    )
    if not question_text:
        return False

    yes_no_question_starts = (
        "do you",
        "are you",
        "will you",
        "can you",
        "have you",
        "is your",
        "would you",
    )
    return question_text.startswith(yes_no_question_starts)


def _coerce_yes_no_answer(answer_text: str | None) -> str | None:
    text = _normalize_binary_text(answer_text)
    if not text:
        return None

    tokens = text.split()
    if not tokens:
        return None

    if "yes" in tokens or tokens[0] in {"yes", "y"}:
        return "Yes"
    if "no" in tokens or tokens[0] in {"no", "n"}:
        return "No"
    return None


def _resolve_unknown_yes_no_value(
    *,
    inspected_field: dict,
    user,
    profile,
    open_ended_provider,
    page_title=None,
    job_context=None,
) -> tuple[str | None, bool]:
    salary_value = resolve_salary_expectation_value(
        inspected_field=inspected_field,
        profile=profile,
    )
    salary_yes_no = _coerce_yes_no_answer(salary_value)
    if salary_yes_no:
        return salary_yes_no, False

    work_auth_value = resolve_work_authorization_value(
        inspected_field=inspected_field,
        profile=profile,
    )
    work_auth_yes_no = _coerce_yes_no_answer(work_auth_value)
    if work_auth_yes_no:
        return work_auth_yes_no, False

    work_arrangement_value = resolve_work_arrangement_value(
        inspected_field=inspected_field,
        profile=profile,
    )
    work_arrangement_yes_no = _coerce_yes_no_answer(work_arrangement_value)
    if work_arrangement_yes_no:
        return work_arrangement_yes_no, False

    if open_ended_provider is None:
        return None, True

    if not _is_binary_yes_no_field(inspected_field):
        return None, True

    question_text = (
        inspected_field.get("label")
        or inspected_field.get("placeholder")
        or inspected_field.get("name")
        or ""
    ).strip()
    if not question_text:
        return None, True

    constrained_prompt = (
        f"{question_text}\n"
        "Answer using exactly one word: Yes or No. "
        "Do not include any extra words or punctuation."
    )
    request = _build_open_ended_request(
        user_id=getattr(user, "id", None),
        question_text=constrained_prompt,
        user=user,
        profile=profile,
        page_title=page_title,
        job_context=job_context,
    )
    result = open_ended_provider.get_answer(request)
    coerced = _coerce_yes_no_answer(result.answer_text)
    if coerced:
        return coerced, bool(result.needs_review)

    return None, True


def _resolve_unknown_open_ended_value(
    *,
    inspected_field: dict,
    user,
    profile,
    open_ended_provider,
    page_title=None,
    job_context=None,
) -> tuple[str | None, bool]:
    if open_ended_provider is None or not _looks_like_open_ended_question(inspected_field):
        return None, True

    question_text = (
        inspected_field.get("label")
        or inspected_field.get("placeholder")
        or inspected_field.get("name")
        or ""
    ).strip()
    if not question_text:
        return None, True

    request = _build_open_ended_request(
        user_id=getattr(user, "id", None),
        question_text=question_text,
        user=user,
        profile=profile,
        page_title=page_title,
        job_context=job_context,
    )
    result = open_ended_provider.get_answer(request)
    if result.answer_text:
        return result.answer_text, bool(result.needs_review)
    return None, True


def resolve_field_value(
    *,
    classified_role: str,
    inspected_field: dict,
    user,
    profile,
    open_ended_provider=None,
    page_title=None,
    job_context=None,
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
        value = getattr(profile, "location", None)
        return value, value is None

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
        value = resolve_salary_expectation_value(
            inspected_field=inspected_field,
            profile=profile,
        )
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
        value = resolve_work_arrangement_value(
            inspected_field=inspected_field,
            profile=profile,
        )
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
            page_title=page_title,
            job_context=job_context,
        )
        result = open_ended_provider.get_answer(request)
        if result.answer_text:
            return result.answer_text, result.needs_review
        return None, True

    if classified_role == "unknown":
        value, needs_review = _resolve_unknown_open_ended_value(
            inspected_field=inspected_field,
            user=user,
            profile=profile,
            open_ended_provider=open_ended_provider,
            page_title=page_title,
            job_context=job_context,
        )
        if value:
            return value, needs_review

        value, needs_review = _resolve_unknown_yes_no_value(
            inspected_field=inspected_field,
            user=user,
            profile=profile,
            open_ended_provider=open_ended_provider,
            page_title=page_title,
            job_context=job_context,
        )
        if value:
            return value, needs_review

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
