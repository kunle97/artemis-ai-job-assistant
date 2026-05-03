"""
Application pipeline service.

Determines whether an application is cleared to advance past the
'filled' state into the submission stage. Also orchestrates the
end-to-end inspect → plan → fill pipeline and advances
Application.status through each step.
"""

import logging

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
)
from src.domain.automation.planning.models import AutomationFillPlanRequest
from src.domain.automation.schemas import ApplicationPageIntakeRequest


logger = logging.getLogger(__name__)


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

            inspection_result = self.automation_service.inspect_application_page(
                ApplicationPageIntakeRequest(application_url=job.apply_url)
            )

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

            plan = self.planning_service.build_fill_plan(
                user_id=user_id,
                payload=AutomationFillPlanRequest(
                    application_url=job.apply_url,
                    inspected_fields=inspected_fields,
                    page_title=page_title,
                    job_context=job_context,
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

            fill_result = self.fill_service.fill_from_plan(
                user_id=user_id,
                application_url=job.apply_url,
                plan=plan,
                application_id=application_id,
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
                failure_reason=str(exc),
            )
            raise

        logger.info(
            f"[PipelineService] run_pipeline complete application_id={application_id} "
            f"status={application.status}"
        )
        return application
