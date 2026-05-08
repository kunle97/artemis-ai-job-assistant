"""
Automation fill domain service.

Executes safe high-confidence field entry without submitting the form.
"""

from __future__ import annotations

import logging
import random
import uuid
from pathlib import Path

from contextlib import ExitStack

from playwright.sync_api import Browser, Page, sync_playwright

from src.core.config import AUTOMATION_UPLOADS_DIR
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
from src.domain.automation.fill.constants import (
    INTER_FIELD_DELAY_MAX_MS,
    INTER_FIELD_DELAY_MIN_MS,
)
from src.domain.automation.fill.helpers import is_backing_input_label
from src.integrations.automation.helpers import (
    _has_detectable_form,
    normalize_application_url,
    prepare_application_page,
)
from src.integrations.automation.browser import create_fresh_context, create_stealth_context, human_delay, simulate_mouse_movement
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
    def __init__(
        self,
        planning_service: AutomationPlanningService,
        application_repository=None,
        resume_repository=None,
    ):
        self.planning_service = planning_service
        self.application_repository = application_repository
        self.resume_repository = resume_repository

    def fill_safe_fields(self, user_id, payload: AutomationFillRequest) -> AutomationFillResult:
        application_url = normalize_application_url(payload.application_url)
        logger.info(f"[AutomationFill] Starting safe fill for: {application_url}")
        resume_file_path = self._resolve_resume_file_path(user_id=user_id, payload=payload)

        plan = self.planning_service.build_fill_plan(
            user_id=user_id,
            payload=AutomationFillPlanRequest(
                application_url=application_url,
                inspected_fields=payload.inspected_fields,
                page_title=payload.page_title,
                job_context=payload.job_context,
            ),
        )

        profile = self.planning_service.profile_repo.get_by_user_id(user_id)
        return self._execute_fill(
            application_url=application_url,
            plan=plan,
            resume_file_path=resume_file_path,
            profile=profile,
        )

    def fill_from_plan(
        self,
        user_id,
        application_url: str,
        plan,
        application_id=None,
        resume_file_path: str | None = None,
        browser: Browser | None = None,
    ) -> AutomationFillResult:
        """Execute the fill phase using a pre-built plan.

        Used by the pipeline orchestrator to avoid double-planning.
        """
        application_url = normalize_application_url(application_url)

        if resume_file_path is None and application_id is not None:
            dummy_payload = AutomationFillRequest(
                application_url=application_url,
                application_id=application_id,
            )
            resume_file_path = self._resolve_resume_file_path(
                user_id=user_id,
                payload=dummy_payload,
            )

        profile = self.planning_service.profile_repo.get_by_user_id(user_id)
        return self._execute_fill(
            application_url=application_url,
            plan=plan,
            resume_file_path=resume_file_path,
            profile=profile,
            browser=browser,
        )

    def fill_and_submit_from_plan(
        self,
        user_id,
        application_url: str,
        plan,
        application_id=None,
        resume_file_path: str | None = None,
        browser: Browser | None = None,
    ) -> AutomationFillResult:
        """Fill the form from a pre-built plan and click the submit button.

        Used by the submission layer after all safety guardrails have passed.
        """
        application_url = normalize_application_url(application_url)

        if resume_file_path is None and application_id is not None:
            dummy_payload = AutomationFillRequest(
                application_url=application_url,
                application_id=application_id,
            )
            resume_file_path = self._resolve_resume_file_path(
                user_id=user_id,
                payload=dummy_payload,
            )

        profile = self.planning_service.profile_repo.get_by_user_id(user_id)
        return self._execute_fill(
            application_url=application_url,
            plan=plan,
            resume_file_path=resume_file_path,
            profile=profile,
            should_submit=True,
            browser=browser,
        )

    def _execute_fill(
        self,
        application_url: str,
        plan,
        resume_file_path: str | None,
        profile,
        should_submit: bool = False,
        browser: Browser | None = None,
    ) -> AutomationFillResult:
        """Run Playwright to fill the form using a pre-built plan.

        When *browser* is supplied the caller's browser process is reused and
        only a fresh context is created per fill operation.  When it is
        ``None`` a full Playwright stack is launched and torn down here.
        """
        fill_results: list[AutomationFillFieldResult] = []
        screenshot_path: str | None = None
        submission_confirmed: bool = False
        platform = _detect_platform(application_url)
        has_explicit_race_field = any(_is_race_label(getattr(field, "label", None)) for field in plan.fields)
        race_followup_attempted = False

        with ExitStack() as stack:
            if browser is not None:
                context, page = create_fresh_context(browser)
                stack.callback(context.close)
            else:
                _playwright = stack.enter_context(sync_playwright())
                _browser, context, page = create_stealth_context(_playwright)
                stack.callback(context.close)
                stack.callback(_browser.close)

            page.goto(application_url, wait_until="domcontentloaded", timeout=30000)
            # Random pause — mimics human reading time, reduces bot signal
            page.wait_for_timeout(random.randint(1800, 3200))

            prepare_application_page(page, application_url)
            page.wait_for_timeout(800)

            # Simulate human presence before touching any fields
            simulate_mouse_movement(page)

            for planned_field in plan.fields:
                field_dict = planned_field.model_dump()

                result = self._fill_planned_field(
                    page=page,
                    field=field_dict,
                    resume_file_path=resume_file_path,
                    platform=platform,
                )
                fill_results.append(result)

                # Keep a short random pause between fields to avoid bot-like
                # machine-speed transitions while preserving throughput.
                human_delay(INTER_FIELD_DELAY_MIN_MS, INTER_FIELD_DELAY_MAX_MS)

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

            if should_submit:
                submitted = self._click_submit_button(page, plan)
                if submitted:
                    logger.info("[AutomationFill] Submit button clicked successfully.")
                    submission_confirmed = self._verify_submission_confirmation(
                        page,
                        application_url=application_url,
                    )
                else:
                    logger.warning("[AutomationFill] Could not locate submit button on page.")

            screenshot_path = self._save_screenshot(page, application_url=application_url)

        filled = sum(1 for result in fill_results if result.fill_status == "filled")
        skipped = len(fill_results) - filled
        unresolved_fields = self._build_unresolved_fields(fill_results)

        completion_note = "Fill + submit pass completed." if should_submit else "Safe fill pass completed."
        logger.info(
            f"[AutomationFill] {'Fill+submit' if should_submit else 'Safe fill'} complete: "
            f"filled={filled}, skipped={skipped}, unresolved={len(unresolved_fields)}"
        )

        return AutomationFillResult(
            application_url=application_url,
            fields=fill_results,
            filled_count=filled,
            skipped_count=skipped,
            screenshot_path=screenshot_path,
            unresolved_fields=unresolved_fields,
            notes=plan.notes + [completion_note],
            submission_confirmed=submission_confirmed,
        )

    def _resolve_resume_file_path(self, *, user_id, payload: AutomationFillRequest) -> str | None:
        if not payload.application_id:
            return payload.resume_file_path

        if not self.application_repository or not self.resume_repository:
            raise ValueError("Application resume resolution is not configured.")

        application = self.application_repository.get_by_id(payload.application_id)
        if not application:
            raise ValueError("Application not found.")

        if str(application.user_id) != str(user_id):
            raise ValueError("Application does not belong to the current user.")

        if not application.resume_id:
            return None

        resume = self.resume_repository.get_by_id_and_user_id(application.resume_id, user_id)
        if not resume:
            raise ValueError("Application resume not found.")

        return resume.file_path

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

    def _click_submit_button(self, page: Page, plan) -> bool:
        """Locate and click the submit button on the application form.

        Attempts in order:
          1. ``button[type='submit']`` or ``input[type='submit']``
          2. Button whose text matches the submit field label from the plan
          3. Buttons matching common submit-button labels
        Returns True if a button was successfully clicked.
        """
        from src.domain.automation.planning.constants import FIELD_ROLE_SUBMIT

        submit_field = next(
            (f for f in plan.fields if getattr(f, "classified_role", None) == FIELD_ROLE_SUBMIT),
            None,
        )

        # Strategy 1: type="submit" element
        try:
            locator = page.locator("button[type='submit'], input[type='submit']")
            if locator.count() > 0:
                human_delay(400, 900)  # pause before clicking submit — bot detectors watch for instant submits
                locator.first.click()
                page.wait_for_timeout(2000)
                return True
        except Exception as exc:
            logger.debug(f"[AutomationFill] type=submit click failed: {exc}")

        # Strategy 2: button matching plan label
        if submit_field and submit_field.label:
            try:
                page.get_by_role("button", name=submit_field.label, exact=False).first.click()
                page.wait_for_timeout(2000)
                return True
            except Exception as exc:
                logger.debug(f"[AutomationFill] Plan-label submit click failed: {exc}")

        # Strategy 3: common submit labels
        for label in ("Submit Application", "Submit Your Application", "Submit", "Apply Now", "Apply"):
            try:
                btn = page.get_by_role("button", name=label, exact=False)
                if btn.count() > 0:
                    btn.first.click()
                    page.wait_for_timeout(2000)
                    return True
            except Exception as exc:
                logger.debug(f"[AutomationFill] Label '{label}' submit click failed: {exc}")

        return False

    _SUBMISSION_CONFIRMATION_PHRASES = (
        "thank you for applying",
        "thank you for your application",
        "thanks for applying",
        "thanks for your application",
        "your application has been submitted",
        "your application was submitted",
        "application submitted",
        "application received",
        "application complete",
        "your application is complete",
        "application sent",
        "successfully submitted",
        "successfully applied",
        "we've received your application",
        "we received your application",
        "we have received your application",
        "we got your application",
        "you have applied",
        "you've applied",
        "application was submitted",
    )

    _SUBMISSION_CONFIRMATION_URL_MARKERS = (
        "submitted",
        "confirmation",
        "complete",
        "success",
        "thank",
        "thanks",
        "applied",
    )

    def _verify_submission_confirmation(self, page: Page, *, application_url: str | None = None) -> bool:
        """Wait briefly for post-submit navigation then scan page text for confirmation.

        Returns True if a confirmation phrase is found, False otherwise.
        """
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            # Timeout is acceptable — the page may not fully idle; still check content
            pass

        page.wait_for_timeout(1500)

        current_url = page.url or ""

        try:
            title = (page.title() or "").lower()
        except Exception as exc:
            logger.debug(f"[AutomationFill] Could not read page title for confirmation check: {exc}")
            title = ""

        try:
            content = page.inner_text("body").lower()
        except Exception as exc:
            logger.debug(f"[AutomationFill] Could not read page body for confirmation check: {exc}")
            return False

        combined_text = " ".join(part for part in (title, content) if part)

        for phrase in self._SUBMISSION_CONFIRMATION_PHRASES:
            if phrase in combined_text:
                logger.info(f"[AutomationFill] Submission confirmation detected: '{phrase}'")
                return True

        if application_url:
            normalized_original = normalize_application_url(application_url)
            if current_url and current_url.rstrip("/") != normalized_original.rstrip("/"):
                if any(marker in current_url.lower() for marker in self._SUBMISSION_CONFIRMATION_URL_MARKERS):
                    logger.info(
                        "[AutomationFill] Submission confirmation inferred from post-submit URL change: %s",
                        current_url,
                    )
                    return True

                if any(marker in title for marker in self._SUBMISSION_CONFIRMATION_URL_MARKERS):
                    logger.info(
                        "[AutomationFill] Submission confirmation inferred from post-submit title change: %s",
                        title,
                    )
                    return True

        try:
            if not _has_detectable_form(page):
                submit_buttons = page.locator("button[type='submit'], input[type='submit']")
                if submit_buttons.count() == 0 and any(
                    marker in combined_text for marker in ("thank", "thanks", "received", "submitted", "complete")
                ):
                    logger.info(
                        "[AutomationFill] Submission confirmation inferred from form disappearance and success text."
                    )
                    return True
        except Exception as exc:
            logger.debug(f"[AutomationFill] Fallback confirmation heuristic failed: {exc}")

        logger.warning(
            "[AutomationFill] No submission confirmation signal found after submit. "
            "url=%s title=%s body_preview=%s",
            current_url,
            title[:120],
            content[:240],
        )
        return False

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
            screenshot_dir = AUTOMATION_UPLOADS_DIR / platform
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