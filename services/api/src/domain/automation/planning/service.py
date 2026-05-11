"""
Automation planning service.

Classifies inspected fields and resolves values from the user's profile.
"""

from __future__ import annotations

import logging

from src.domain.automation.planning.helpers import (
    detect_platform_name,
    get_classifier_for_url,
    resolve_field_value,
)
from src.domain.automation.planning.constants import FIELD_ROLE_PREFERRED_OFFICE_LOCATION
from src.domain.automation.planning.models import (
    AutomationFillPlan,
    AutomationFillPlanRequest,
    AutomationPlannedField,
)

logger = logging.getLogger(__name__)


class AutomationPlanningService:
    def __init__(
        self,
        user_repo,
        profile_repo,
        answer_resolver=None,
        open_ended_provider=None,
    ):
        self.user_repo = user_repo
        self.profile_repo = profile_repo
        self.answer_resolver = answer_resolver
        self.open_ended_provider = open_ended_provider

    def build_fill_plan(
        self,
        *,
        user_id,
        payload: AutomationFillPlanRequest,
    ) -> AutomationFillPlan:
        logger.info(f"[AutomationPlanning] Building fill plan for: {payload.application_url}")

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

            # For checkbox_group with no label, inspect option values for city/remote keywords
            # to detect a preferred-office-location group even when the heading is absent.
            if field_type == "checkbox_group" and classified_role == "unknown":
                option_labels = " ".join(
                    (opt.get("label") or opt.get("value") or "")
                    for opt in (inspected_field.get("options") or [])
                ).lower()
                location_keywords = (
                    "remote", "office", "hybrid", "on-site", "onsite", "new york", "san francisco",
                    "boston", "los angeles", "chicago", "seattle", "austin", "denver", "cambridge",
                    "manhattan", "brooklyn", "chelsea", "venice", "nyc", "sf ", " la ",
                )
                if any(kw in option_labels for kw in location_keywords):
                    classified_role = FIELD_ROLE_PREFERRED_OFFICE_LOCATION

            resolved_value, needs_review = resolve_field_value(
                classified_role=classified_role,
                inspected_field=inspected_field,
                user=user,
                profile=profile,
                answer_resolver=self.answer_resolver,
                open_ended_provider=self.open_ended_provider,
                page_title=payload.page_title,
                job_context=payload.job_context,
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

        review_count = sum(1 for field in planned_fields if field.needs_review)
        logger.info(
            f"[AutomationPlanning] Fill plan complete: total_fields={len(planned_fields)}, needs_review={review_count}"
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