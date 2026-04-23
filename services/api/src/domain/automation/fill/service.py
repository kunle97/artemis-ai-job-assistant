"""
Automation fill domain service.

Executes safe high-confidence field entry without submitting the form.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from src.domain.automation.planning.constants import (
    FIELD_ROLE_COVER_LETTER_UPLOAD,
    FIELD_ROLE_IGNORE,
    FIELD_ROLE_RESUME_UPLOAD,
    FIELD_ROLE_SUBMIT,
)
from src.domain.automation.planning.service import AutomationPlanningService
from src.domain.automation.planning.models import AutomationFillPlanRequest
from src.domain.automation.fill.handlers.radio_groups import fill_radio_group
from src.domain.automation.fill.handlers.select_like import fill_select_like
from src.domain.automation.fill.handlers.text_fields import fill_text_field
from src.domain.automation.fill.handlers.uploads import (
    skip_cover_letter_upload,
    upload_resume,
)
from src.domain.automation.fill.helpers import is_backing_input_label
from src.domain.automation.fill.models import (
    AutomationFillFieldResult,
    AutomationFillRequest,
    AutomationFillResult,
    AutomationUnresolvedField,
)


class AutomationFillService:
    def __init__(self, planning_service: AutomationPlanningService):
        self.planning_service = planning_service

    def fill_safe_fields(self, user_id, payload: AutomationFillRequest) -> AutomationFillResult:
        plan = self.planning_service.build_fill_plan(
            user_id=user_id,
            payload=AutomationFillPlanRequest(
                application_url=payload.application_url,
                inspected_fields=payload.inspected_fields,
            ),
        )

        fill_results: list[AutomationFillFieldResult] = []
        screenshot_path: str | None = None

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            try:
                page.goto(
                    payload.application_url,
                    wait_until="domcontentloaded",
                    timeout=30000,
                )
                page.wait_for_timeout(1500)

                for planned_field in plan.fields:
                    field_dict = planned_field.model_dump()

                    result = self._fill_planned_field(
                        page=page,
                        field=field_dict,
                        resume_file_path=payload.resume_file_path,
                    )
                    fill_results.append(result)

                screenshot_path = self._save_screenshot(page)

            finally:
                context.close()
                browser.close()

        filled = sum(1 for result in fill_results if result.fill_status == "filled")
        skipped = len(fill_results) - filled
        unresolved_fields = self._build_unresolved_fields(fill_results)

        return AutomationFillResult(
            application_url=payload.application_url,
            fields=fill_results,
            filled_count=filled,
            skipped_count=skipped,
            screenshot_path=screenshot_path,
            unresolved_fields=unresolved_fields,
            notes=plan.notes + ["Safe fill pass completed."],
        )

    def _fill_planned_field(
        self,
        *,
        page: Page,
        field: dict,
        resume_file_path: str | None,
    ) -> AutomationFillFieldResult:
        role = field.get("classified_role")
        value = field.get("resolved_value")
        field_type = field.get("field_type")

        if role in {FIELD_ROLE_IGNORE, FIELD_ROLE_SUBMIT}:
            return self._build_result(
                field=field,
                resolved_value=None,
                fill_status="skipped_ignored",
            )

        if role == FIELD_ROLE_COVER_LETTER_UPLOAD:
            return skip_cover_letter_upload(field)

        if role == FIELD_ROLE_RESUME_UPLOAD:
            return upload_resume(page, field, resume_file_path)

        if field.get("needs_review"):
            return self._build_result(
                field=field,
                resolved_value=value,
                fill_status="skipped_review",
            )

        if not value:
            return self._build_result(
                field=field,
                resolved_value=None,
                fill_status="skipped_no_value",
            )

        if self._is_backing_input(field):
            return self._build_result(
                field=field,
                resolved_value=value,
                fill_status="skipped_backing_input",
            )

        try:
            if field_type == "select_like":
                return fill_select_like(page, field, value)

            if field_type == "radio_group":
                return fill_radio_group(page, field, value)

            if field_type in {"input", "textarea"}:
                return fill_text_field(page, field, value)

            return self._build_result(
                field=field,
                resolved_value=value,
                fill_status="skipped_unknown_type",
            )
        except Exception:
            return self._build_result(
                field=field,
                resolved_value=value,
                fill_status="error",
            )

    def _is_backing_input(self, field: dict) -> bool:
        field_type = field.get("field_type")
        label = field.get("label")

        if field_type != "input":
            return False

        return is_backing_input_label(label)

    def _build_result(
        self,
        *,
        field: dict,
        resolved_value: str | None,
        fill_status: str,
    ) -> AutomationFillFieldResult:
        return AutomationFillFieldResult(
            label=field.get("label"),
            name=field.get("name"),
            classified_role=field.get("classified_role", "unknown"),
            resolved_value=resolved_value,
            fill_status=fill_status,
        )

    def _build_unresolved_fields(
        self,
        fill_results: list[AutomationFillFieldResult],
    ) -> list[AutomationUnresolvedField]:
        unresolved_statuses = {
            "skipped_option_not_applied",
            "skipped_option_not_found",
            "skipped_review",
            "skipped_no_value",
            "skipped_not_found",
            "skipped_unknown_type",
            "error",
        }

        unresolved_fields: list[AutomationUnresolvedField] = []

        for result in fill_results:
            if result.fill_status not in unresolved_statuses:
                continue

            unresolved_fields.append(
                AutomationUnresolvedField(
                    label=result.label,
                    name=result.name,
                    classified_role=result.classified_role,
                    resolved_value=result.resolved_value,
                    fill_status=result.fill_status,
                    reason=self._get_unresolved_reason(result),
                )
            )

        return unresolved_fields

    def _get_unresolved_reason(self, result: AutomationFillFieldResult) -> str:
        mapping = {
            "skipped_option_not_applied": "Resolved a value, but Artemis could not reliably apply it in the UI.",
            "skipped_option_not_found": "Resolved a value, but no matching selectable option was found on the page.",
            "skipped_review": "This field requires user review before filling.",
            "skipped_no_value": "No value is currently stored for this field.",
            "skipped_not_found": "The target field could not be located on the page.",
            "skipped_unknown_type": "This field type is not yet supported by the fill engine.",
            "error": "An unexpected automation error occurred while trying to fill this field.",
        }
        return mapping.get(result.fill_status, "This field still needs manual attention.")

    def _save_screenshot(self, page: Page) -> str | None:
        try:
            screenshot_dir = Path("uploads/automation")
            screenshot_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{uuid.uuid4()}-filled.png"
            path = screenshot_dir / filename

            page.screenshot(path=str(path), full_page=True)
            return str(path)
        except Exception:
            return None