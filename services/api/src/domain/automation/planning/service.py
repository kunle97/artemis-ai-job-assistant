"""
Automation planning service.

Classifies inspected fields and resolves values from the user's profile.
"""

from __future__ import annotations

from src.domain.automation.planning.helpers import (
    detect_platform_name,
    get_classifier_for_url,
    resolve_field_value,
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

            resolved_value, needs_review = resolve_field_value(
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
                f"Detected platform: {detect_platform_name(payload.application_url)}",
                f"Classifier: {classifier.__class__.__name__}",
                "Basic autofill only.",
            ],
        )