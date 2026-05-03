"""
Automation fill domain service.

Executes safe high-confidence field entry without submitting the form.
"""

from __future__ import annotations

import logging
import random
import uuid
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from src.domain.automation.planning.constants import (
    FIELD_ROLE_COVER_LETTER_UPLOAD,
    FIELD_ROLE_IGNORE,
    FIELD_ROLE_LOCATION,
    FIELD_ROLE_RESUME_UPLOAD,
    FIELD_ROLE_SUBMIT,
    PLATFORM_LEVER,
    PLATFORM_GREENHOUSE,
    PLATFORM_ASHBY,
)
from src.domain.automation.planning.service import AutomationPlanningService
from src.domain.automation.planning.models import AutomationFillPlanRequest
from src.domain.automation.fill.handlers.radio_groups import fill_radio_group
from src.domain.automation.fill.handlers.greenhouse_combobox import fill_greenhouse_combobox
from src.domain.automation.fill.handlers.select_like import fill_select_like
from src.domain.automation.fill.handlers.text_fields import (
    fill_autocomplete_location_field,
    fill_text_field,
)
from src.domain.automation.fill.handlers.uploads import (
    skip_cover_letter_upload,
    upload_resume,
)
from src.domain.automation.fill.helpers import is_backing_input_label
from src.integrations.automation.helpers import normalize_application_url, prepare_application_page
from src.integrations.automation.browser import create_stealth_context
from src.domain.automation.fill.models import (
    AutomationFillFieldResult,
    AutomationFillRequest,
    AutomationFillResult,
    AutomationUnresolvedField,
)
from src.domain.automation.planning.helpers import (
    should_include_unresolved_field,
    build_unresolved_reason,
)

logger = logging.getLogger(__name__)


class AutomationFillService:
    def __init__(self, planning_service: AutomationPlanningService):
        self.planning_service = planning_service

    def fill_safe_fields(self, user_id, payload: AutomationFillRequest) -> AutomationFillResult:
        application_url = normalize_application_url(payload.application_url)
        logger.info(f"[AutomationFill] Starting safe fill for: {application_url}")

        plan = self.planning_service.build_fill_plan(
            user_id=user_id,
            payload=AutomationFillPlanRequest(
                application_url=application_url,
                inspected_fields=payload.inspected_fields,
                page_title=payload.page_title,
                job_context=payload.job_context,
            ),
        )

        fill_results: list[AutomationFillFieldResult] = []
        screenshot_path: str | None = None
        platform = _detect_platform(application_url)
        profile = self.planning_service.profile_repo.get_by_user_id(user_id)
        has_explicit_race_field = any(_is_race_label(getattr(field, "label", None)) for field in plan.fields)
        race_followup_attempted = False

        with sync_playwright() as playwright:
            browser, context, page = create_stealth_context(playwright)

            try:
                page.goto(
                    application_url,
                    wait_until="domcontentloaded",
                    timeout=30000,
                )
                # Random pause — mimics human reading time, reduces bot signal
                page.wait_for_timeout(random.randint(1800, 3200))

                prepare_application_page(page, application_url)
                page.wait_for_timeout(800)

                for planned_field in plan.fields:
                    field_dict = planned_field.model_dump()

                    result = self._fill_planned_field(
                        page=page,
                        field=field_dict,
                        resume_file_path=payload.resume_file_path,
                        platform=platform,
                    )
                    fill_results.append(result)

                    if (
                        platform == PLATFORM_GREENHOUSE
                        and not has_explicit_race_field
                        and not race_followup_attempted
                    ):
                        race_followup_result = self._maybe_fill_greenhouse_race_followup(
                            page=page,
                            filled_field=field_dict,
                            field_result=result,
                            profile=profile,
                        )
                        if race_followup_result is not None:
                            race_followup_attempted = True
                            if race_followup_result.fill_status == "filled":
                                fill_results.append(race_followup_result)

                screenshot_path = self._save_screenshot(page, application_url=application_url)

            finally:
                context.close()
                browser.close()

        filled = sum(1 for result in fill_results if result.fill_status == "filled")
        skipped = len(fill_results) - filled
        unresolved_fields = self._build_unresolved_fields(fill_results)

        logger.info(
            f"[AutomationFill] Safe fill complete: filled={filled}, skipped={skipped}, unresolved={len(unresolved_fields)}"
        )

        return AutomationFillResult(
            application_url=application_url,
            fields=fill_results,
            filled_count=filled,
            skipped_count=skipped,
            screenshot_path=screenshot_path,
            unresolved_fields=unresolved_fields,
            notes=plan.notes + ["Safe fill pass completed."],
        )

    def _maybe_fill_greenhouse_race_followup(
        self,
        *,
        page: Page,
        filled_field: dict,
        field_result: AutomationFillFieldResult,
        profile,
    ) -> AutomationFillFieldResult | None:
        if not profile:
            return None

        race_value = getattr(profile, "race", None)
        if not race_value or not getattr(profile, "autofill_race", False):
            return None

        label = (filled_field.get("label") or "").strip().lower()
        if "hispanic" not in label and "latino" not in label:
            return None

        if field_result.fill_status != "filled":
            return None

        selected = (field_result.resolved_value or "").strip().lower()
        if not selected.startswith("no"):
            return None

        page.wait_for_timeout(250)

        for race_label in [
            "Please identify your race",
            "What is your race?",
            "Race",
            "Race/Ethnicity",
        ]:
            synthetic_field = {
                "label": race_label,
                "name": None,
                "classified_role": "demographic_question",
                "field_type": "select_like",
            }
            result = fill_greenhouse_combobox(page, synthetic_field, race_value)
            if result.fill_status == "filled":
                logger.info(
                    "[AutomationFill] Filled emergent Greenhouse race field "
                    f"after Hispanic/Latino selection with value={race_value!r}"
                )
                return result

        return None

    def _fill_planned_field(
        self,
        *,
        page: Page,
        field: dict,
        resume_file_path: str | None,
        platform: str | None = None,
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
            return upload_resume(page, field, resume_file_path, platform=platform)

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
            if field_type in {"select_like", "select"}:
                if platform == PLATFORM_GREENHOUSE:
                    return fill_greenhouse_combobox(page, field, value)
                return fill_select_like(page, field, value)

            if field_type == "radio_group":
                return fill_radio_group(page, field, value)

            if field_type in {"input", "textarea"}:
                if role == FIELD_ROLE_LOCATION and platform == PLATFORM_LEVER:
                    return fill_autocomplete_location_field(page, field, value)
                return fill_text_field(page, field, value)

            return self._build_result(
                field=field,
                resolved_value=value,
                fill_status="skipped_unknown_type",
            )
        except Exception as exc:
            logger.warning(
                f"[AutomationFill] Error filling field label={field.get('label')} role={role}: {type(exc).__name__}"
            )
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
        unresolved_fields: list[AutomationUnresolvedField] = []

        for result in fill_results:
            result_dict = result.model_dump()

            if not should_include_unresolved_field(result_dict):
                continue

            unresolved_fields.append(
                AutomationUnresolvedField(
                    label=result.label,
                    name=result.name,
                    classified_role=result.classified_role,
                    resolved_value=result.resolved_value,
                    fill_status=result.fill_status,
                    reason=build_unresolved_reason(result_dict),
                )
            )

        return unresolved_fields

    def _save_screenshot(self, page: Page, application_url: str | None = None) -> str | None:
        from src.core.config import settings
        if not settings.save_screenshots:
            return None
        try:
            platform = _detect_platform(application_url or "")
            screenshot_dir = Path("uploads/automation") / platform
            screenshot_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{uuid.uuid4()}-filled.png"
            path = screenshot_dir / filename

            page.screenshot(path=str(path), full_page=True)
            return str(path)
        except Exception as exc:
            logger.warning(f"[AutomationFill] Failed to save screenshot: {type(exc).__name__}")
            return None


def _detect_platform(url: str) -> str:
    """Infer the ATS platform from the application URL."""
    if "lever.co" in url:
        return PLATFORM_LEVER
    if "greenhouse.io" in url or "boards.greenhouse" in url:
        return PLATFORM_GREENHOUSE
    if "ashbyhq.com" in url or "ashby" in url:
        return PLATFORM_ASHBY
    return "generic"


def _is_race_label(label: str | None) -> bool:
    text = (label or "").strip().lower()
    if not text:
        return False
    if "hispanic" in text or "latino" in text:
        return False
    return "race" in text or "ethnicity" in text