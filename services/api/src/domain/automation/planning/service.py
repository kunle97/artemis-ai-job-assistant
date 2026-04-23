"""
Automation planning service.

Classifies inspected fields and resolves values from the user's profile.
"""

from __future__ import annotations

from src.domain.automation.planning.helpers import get_classifier_for_url
from src.domain.automation.planning.constants import (
    FIELD_ROLE_IGNORE,
    FIELD_ROLE_SUBMIT,
    FIELD_ROLE_RESUME_UPLOAD,
    FIELD_ROLE_FIRST_NAME,
    FIELD_ROLE_LAST_NAME,
    FIELD_ROLE_FULL_NAME,
    FIELD_ROLE_EMAIL,
    FIELD_ROLE_PHONE,
    FIELD_ROLE_LINKEDIN_URL,
    FIELD_ROLE_LOCATION,
    FIELD_ROLE_COUNTRY,
    FIELD_ROLE_PREFERRED_PROGRAMMING_LANGUAGE,
    FIELD_ROLE_REFERRAL_SOURCE,
    FIELD_ROLE_STATE_OF_RESIDENCE,
    FIELD_ROLE_ZIP_CODE,
    FIELD_ROLE_COVER_LETTER_UPLOAD,
)
from src.domain.automation.planning.models import (
    AutomationFillPlan,
    AutomationFillPlanRequest,
    AutomationPlannedField,
)


class AutomationPlanningService:
    def __init__(
        self,
        user_repo,
        profile_repo,
    ):
        self.user_repo = user_repo
        self.profile_repo = profile_repo

    def build_fill_plan(
        self,
        *,
        user_id,
        payload: AutomationFillPlanRequest,
    ) -> AutomationFillPlan:
        classifier = get_classifier_for_url(payload.application_url)

        user = self.user_repo.get_by_id(user_id)
        profile = self.profile_repo.get_by_user_id(user_id)

        planned_fields: list[AutomationPlannedField] = []

        for inspected_field in payload.inspected_fields:
            field_type = inspected_field.get("field_type")
            label = inspected_field.get("label")
            name = inspected_field.get("name")
            placeholder = inspected_field.get("placeholder")

            classified_role = classifier.classify(
                field_type=field_type,
                label=label,
                name=name,
                placeholder=placeholder,
            )

            resolved_value, needs_review = self._resolve_field_value(
                classified_role=classified_role,
                inspected_field=inspected_field,
                user=user,
                profile=profile,
            )

            planned_fields.append(
                AutomationPlannedField(
                    field_type=field_type,
                    input_subtype=inspected_field.get("input_subtype"),
                    label=label,
                    name=name,
                    placeholder=placeholder,
                    required=bool(inspected_field.get("required", False)),
                    options=inspected_field.get("options", []),
                    classified_role=classified_role,
                    resolved_value=resolved_value,
                    needs_review=needs_review,
                )
            )

        return AutomationFillPlan(
            application_url=payload.application_url,
            fields=planned_fields,
            notes=[
                f"Detected platform: {self._detect_platform_name(payload.application_url)}",
                f"Classifier: {classifier.__class__.__name__}",
                "Basic autofill only.",
            ],
        )

    def _resolve_field_value(
        self,
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

        if classified_role == FIELD_ROLE_COUNTRY:
            return getattr(profile, "country", None), False

        if classified_role == FIELD_ROLE_PREFERRED_PROGRAMMING_LANGUAGE:
            return getattr(profile, "preferred_programming_language", None), False

        if classified_role == FIELD_ROLE_REFERRAL_SOURCE:
            return getattr(profile, "referral_source", None), False

        if classified_role == FIELD_ROLE_STATE_OF_RESIDENCE:
            return getattr(profile, "state_of_residence", None), False

        if classified_role == FIELD_ROLE_ZIP_CODE:
            value = getattr(profile, "zip_code", None)
            return str(value) if value is not None else None, False

        return None, True

    def _detect_platform_name(self, application_url: str) -> str:
        lowered = application_url.lower()
        if "greenhouse" in lowered:
            return "greenhouse"
        if "ashbyhq" in lowered or "ashby" in lowered:
            return "ashby"
        if "lever" in lowered:
            return "lever"
        return "generic"