"""
Application pipeline service.

Determines whether an application is cleared to advance past the
'filled' state into the submission stage. Also orchestrates the
end-to-end inspect → plan → fill pipeline and advances
Application.status through each step.
"""

import logging
import re
from time import sleep
from typing import Callable, TypeVar

from src.core.config import settings
from src.domain.applications.constants import (
    APPLICATION_STATUS_AWAITING_SUBMISSION,
    APPLICATION_STATUS_FAILED,
    APPLICATION_STATUS_FILLED,
    APPLICATION_STATUS_FILLING,
    APPLICATION_STATUS_INSPECTED,
    APPLICATION_STATUS_INSPECTING,
    APPLICATION_STATUS_PLANNED,
    APPLICATION_STATUS_PLANNING,
    APPLICATION_STATUS_QUEUED,
    APPLICATION_STATUS_SUBMITTED,
)
from src.domain.automation.planning.models import AutomationFillPlanRequest
from src.domain.automation.schemas import ApplicationPageIntakeRequest


logger = logging.getLogger(__name__)
_T = TypeVar("_T")


class ApplicationPipelineService:
    """
    Governs pipeline transitions and orchestrates the full automation
    pipeline for job applications.

    Gate logic: an application that has been filled by automation must
    pass a manual review gate before it can be submitted.  The gate
    opens when either:

    * ``manual_review_required`` is ``False`` — the user has opted into
      automatic submission via their profile preferences; or
    * ``is_authorized_to_submit`` is ``True`` — the user explicitly called
      the ``POST /applications/{id}/authorize`` endpoint.
    """

    def __init__(
        self,
        application_repo,
        job_repo,
        automation_service,
        planning_service,
        fill_service,
    ):
        self.application_repo = application_repo
        self.job_repo = job_repo
        self.automation_service = automation_service
        self.planning_service = planning_service
        self.fill_service = fill_service

    def _classify_failure(self, exc: Exception) -> tuple[str, bool]:
        """Classify failures into retryable transient or terminal permanent buckets."""
        message = str(exc).lower()

        if "captcha" in message:
            return "captcha_detected", False

        if "already applied" in message:
            return "already_applied_signal", False

        if re.search(r"\b404\b", message):
            return "http_404", False

        if (
            re.search(r"\b5\d\d\b", message)
            and ("http" in message or "status" in message or "ats" in message)
        ):
            return "http_5xx", True

        if "timeout" in message or "timed out" in message:
            return "playwright_timeout", True

        if "dom not found" in message or ("selector" in message and "not found" in message):
            return "dom_not_found", True

        return "unclassified_error", False

    def _format_failure_reason(self, exc: Exception) -> str:
        """Return a classified failure_reason string suitable for persistence."""
        category, retryable = self._classify_failure(exc)
        class_name = "transient" if retryable else "permanent"
        return f"{category} ({class_name}): {type(exc).__name__}: {exc}"

    def _execute_with_retries(self, operation_name: str, operation: Callable[[], _T]) -> _T:
        """Execute an operation with exponential backoff for transient failures."""
        max_retries = max(0, settings.max_pipeline_retries)
        attempt = 0

        while True:
            try:
                return operation()
            except Exception as exc:
                category, retryable = self._classify_failure(exc)
                if retryable and attempt < max_retries:
                    delay_seconds = 2 ** attempt
                    logger.warning(
                        "[PipelineService] %s transient failure (%s) attempt=%d/%d delay=%ss error=%s",
                        operation_name,
                        category,
                        attempt + 1,
                        max_retries + 1,
                        delay_seconds,
                        exc,
                    )
                    sleep(delay_seconds)
                    attempt += 1
                    continue

                if retryable:
                    logger.error(
                        "[PipelineService] %s retries exhausted after %d attempts category=%s error=%s",
                        operation_name,
                        max_retries + 1,
                        category,
                        exc,
                    )
                raise

    def _inspection_has_already_applied(self, inspection_result) -> bool:
        """Return True when inspection signals the candidate already applied."""
        value = None
        if isinstance(inspection_result, dict):
            value = inspection_result.get("already_applied")
        else:
            value = getattr(inspection_result, "already_applied", None)

        return value is True

    def can_advance_past_filled(self, application) -> bool:
        """Return True if the application is cleared for submission."""
        if application.status != APPLICATION_STATUS_FILLED:
            logger.debug(
                f"[PipelineService] Application {application.id} is not in "
                f"'filled' state (current: {application.status}); "
                "advancement check is not applicable."
            )
            return False

        if not application.manual_review_required:
            logger.info(
                f"[PipelineService] Application {application.id} cleared "
                "for submission: manual review not required (auto-submit mode)."
            )
            return True

        if application.is_authorized_to_submit:
            logger.info(
                f"[PipelineService] Application {application.id} cleared "
                "for submission: user explicitly authorized."
            )
            return True

        logger.info(
            f"[PipelineService] Application {application.id} is halted at "
            "'filled': manual review required and not yet authorized."
        )
        return False

    def run_pipeline(self, user_id, application_id):
        """Coordinate the full inspect → plan → fill pipeline for an application.

        Status transitions:
            queued → inspecting → inspected → planning → planned
            → filling → filled → awaiting_submission | failed
        """
        logger.info(f"[PipelineService] run_pipeline start application_id={application_id}")

        application = self.application_repo.get_by_id(application_id)
        if not application:
            raise ValueError("Application not found.")

        if str(application.user_id) != str(user_id):
            raise PermissionError("You are not allowed to run this application's pipeline.")

        job = self.job_repo.get_by_id(application.job_id)
        if not job:
            raise ValueError("Job not found for this application.")

        try:
            application = self.application_repo.update_fields(
                application_id, status=APPLICATION_STATUS_QUEUED
            )

            # INSPECT
            logger.info(f"[PipelineService] Inspecting application_id={application_id}")
            application = self.application_repo.update_fields(
                application_id, status=APPLICATION_STATUS_INSPECTING
            )

            inspection_result = self._execute_with_retries(
                "inspect_application_page",
                lambda: self.automation_service.inspect_application_page(
                    ApplicationPageIntakeRequest(application_url=job.apply_url)
                ),
            )

            if self._inspection_has_already_applied(inspection_result):
                application = self.application_repo.update_fields(
                    application_id,
                    status=APPLICATION_STATUS_SUBMITTED,
                )
                logger.info(
                    "[PipelineService] ATS already-applied signal detected during inspection; "
                    "marking application_id=%s as submitted",
                    application_id,
                )
                return application

            # inspection_result is a plain dict from ApplicationPageInspector
            if isinstance(inspection_result, dict):
                raw_fields = inspection_result.get("fields", [])
                page_title = inspection_result.get("title")
                job_context = inspection_result.get("job_context")
            else:
                raw_fields = inspection_result.fields
                page_title = inspection_result.title
                job_context = inspection_result.job_context

            inspected_fields = [
                f.model_dump() if hasattr(f, "model_dump") else (f if isinstance(f, dict) else dict(f))
                for f in raw_fields
            ]

            application = self.application_repo.update_fields(
                application_id, status=APPLICATION_STATUS_INSPECTED
            )
            logger.info(
                f"[PipelineService] Inspection complete: {len(inspected_fields)} fields "
                f"application_id={application_id}"
            )

            # PLAN
            logger.info(f"[PipelineService] Planning application_id={application_id}")
            application = self.application_repo.update_fields(
                application_id, status=APPLICATION_STATUS_PLANNING
            )

            plan = self._execute_with_retries(
                "build_fill_plan",
                lambda: self.planning_service.build_fill_plan(
                    user_id=user_id,
                    payload=AutomationFillPlanRequest(
                        application_url=job.apply_url,
                        inspected_fields=inspected_fields,
                        page_title=page_title,
                        job_context=job_context,
                    ),
                ),
            )

            application = self.application_repo.update_fields(
                application_id, status=APPLICATION_STATUS_PLANNED
            )
            logger.info(
                f"[PipelineService] Planning complete: {len(plan.fields)} fields planned "
                f"application_id={application_id}"
            )

            # FILL
            logger.info(f"[PipelineService] Filling application_id={application_id}")
            application = self.application_repo.update_fields(
                application_id, status=APPLICATION_STATUS_FILLING
            )

            fill_result = self._execute_with_retries(
                "fill_from_plan",
                lambda: self.fill_service.fill_from_plan(
                    user_id=user_id,
                    application_url=job.apply_url,
                    plan=plan,
                    application_id=application_id,
                ),
            )

            application = self.application_repo.update_fields(
                application_id, status=APPLICATION_STATUS_FILLED
            )
            logger.info(
                f"[PipelineService] Fill complete: filled={fill_result.filled_count}, "
                f"skipped={fill_result.skipped_count} application_id={application_id}"
            )

            # GATE CHECK — advance to awaiting_submission if cleared
            application = self.application_repo.get_by_id(application_id)
            if self.can_advance_past_filled(application):
                application = self.application_repo.update_fields(
                    application_id, status=APPLICATION_STATUS_AWAITING_SUBMISSION
                )
                logger.info(
                    f"[PipelineService] Application {application_id} advanced to awaiting_submission."
                )

        except Exception as exc:
            logger.error(
                f"[PipelineService] Pipeline failed application_id={application_id}: {exc}"
            )
            self.application_repo.update_fields(
                application_id,
                status=APPLICATION_STATUS_FAILED,
                failure_reason=self._format_failure_reason(exc),
            )
            raise

        logger.info(
            f"[PipelineService] run_pipeline complete application_id={application_id} "
            f"status={application.status}"
        )
        return application

    # ------------------------------------------------------------------
    # Submission layer
    # ------------------------------------------------------------------

    def _validate_submission_guardrails(self, application) -> None:
        """Raise ValueError listing every unmet guardrail condition.

        All four conditions must be satisfied before a form is submitted:
          (a) fill pipeline has completed (status is filled or awaiting_submission)
          (b) readiness check has passed (profile + resume present)
          (c) Application reached the 'filled' state
          (d) explicit user authorization is set
        """
        errors: list[str] = []

        # (a) + (c) The fill pipeline must have completed
        if application.status not in (
            APPLICATION_STATUS_FILLED,
            APPLICATION_STATUS_AWAITING_SUBMISSION,
        ):
            errors.append(
                f"fill pipeline has not completed (current status: '{application.status}'); "
                "run POST /applications/{id}/run first"
            )

        # (b) Readiness check
        if not application.is_ready_for_automation:
            errors.append(
                "application is not ready for automation — ensure a profile and resume are attached"
            )

        # (d) Explicit user authorization
        if application.manual_review_required and not application.is_authorized_to_submit:
            errors.append(
                "user authorization is required before submission — "
                "call POST /applications/{id}/authorize first"
            )

        if errors:
            raise ValueError(
                "Submission blocked by safety guardrails: " + "; ".join(errors)
            )

    def submit_application(self, user_id, application_id):
        """Submit the application form after validating all safety guardrails.

        Guardrails (all four must pass):
          (a) fill pipeline completed (status == filled or awaiting_submission)
          (b) readiness check passed (is_ready_for_automation == True)
          (c) application reached 'filled' state
          (d) explicit authorization flag set (is_authorized_to_submit == True
              or manual_review_required == False)

        On success the Application.status advances to 'submitted'.
        On failure it is set to 'failed'.
        """
        logger.info(
            f"[PipelineService] submit_application start application_id={application_id}"
        )

        application = self.application_repo.get_by_id(application_id)
        if not application:
            raise ValueError("Application not found.")

        if str(application.user_id) != str(user_id):
            raise PermissionError("You are not allowed to submit this application.")

        self._validate_submission_guardrails(application)

        job = self.job_repo.get_by_id(application.job_id)
        if not job:
            raise ValueError("Job not found for this application.")

        try:
            # Re-inspect and re-plan so the browser session is fresh
            inspection_result = self._execute_with_retries(
                "inspect_application_page",
                lambda: self.automation_service.inspect_application_page(
                    ApplicationPageIntakeRequest(application_url=job.apply_url)
                ),
            )

            if self._inspection_has_already_applied(inspection_result):
                application = self.application_repo.update_fields(
                    application_id,
                    status=APPLICATION_STATUS_SUBMITTED,
                )
                logger.info(
                    "[PipelineService] ATS already-applied signal detected before submit; "
                    "marking application_id=%s as submitted",
                    application_id,
                )
                return application

            if isinstance(inspection_result, dict):
                raw_fields = inspection_result.get("fields", [])
                page_title = inspection_result.get("title")
                job_context = inspection_result.get("job_context")
            else:
                raw_fields = inspection_result.fields
                page_title = inspection_result.title
                job_context = inspection_result.job_context

            inspected_fields = [
                f.model_dump() if hasattr(f, "model_dump") else (f if isinstance(f, dict) else dict(f))
                for f in raw_fields
            ]

            plan = self._execute_with_retries(
                "build_fill_plan",
                lambda: self.planning_service.build_fill_plan(
                    user_id=user_id,
                    payload=AutomationFillPlanRequest(
                        application_url=job.apply_url,
                        inspected_fields=inspected_fields,
                        page_title=page_title,
                        job_context=job_context,
                    ),
                ),
            )

            fill_result = self._execute_with_retries(
                "fill_and_submit_from_plan",
                lambda: self.fill_service.fill_and_submit_from_plan(
                    user_id=user_id,
                    application_url=job.apply_url,
                    plan=plan,
                    application_id=application_id,
                ),
            )

            if not fill_result.submission_confirmed:
                raise ValueError(
                    "Submit button was clicked but no confirmation message was detected on the page. "
                    "The application may not have been submitted successfully."
                )

            application = self.application_repo.update_fields(
                application_id, status=APPLICATION_STATUS_SUBMITTED
            )
            logger.info(
                f"[PipelineService] submit_application complete application_id={application_id}"
            )

        except Exception as exc:
            logger.error(
                f"[PipelineService] submit_application failed application_id={application_id}: {exc}"
            )
            self.application_repo.update_fields(
                application_id,
                status=APPLICATION_STATUS_FAILED,
                failure_reason=self._format_failure_reason(exc),
            )
            raise

        return application
