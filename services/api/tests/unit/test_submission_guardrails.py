"""
Unit tests for ApplicationPipelineService submission guardrails.

Verifies that _validate_submission_guardrails raises ValueError for every
unmet condition and that submit_application enforces all four checks.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.domain.applications.constants import (
    APPLICATION_STATUS_AWAITING_SUBMISSION,
    APPLICATION_STATUS_FAILED,
    APPLICATION_STATUS_FILLED,
    APPLICATION_STATUS_SAVED,
    APPLICATION_STATUS_SUBMITTED,
)
from src.domain.applications.pipeline_service import ApplicationPipelineService
from src.domain.automation.planning.models import AutomationFillPlan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_application(
    *,
    status=APPLICATION_STATUS_AWAITING_SUBMISSION,
    is_ready_for_automation=True,
    manual_review_required=False,
    is_authorized_to_submit=False,
    user_id=None,
    job_id=None,
):
    app = MagicMock()
    app.id = uuid.uuid4()
    app.user_id = user_id or uuid.uuid4()
    app.job_id = job_id or uuid.uuid4()
    app.status = status
    app.is_ready_for_automation = is_ready_for_automation
    app.manual_review_required = manual_review_required
    app.is_authorized_to_submit = is_authorized_to_submit
    return app


def _make_job(apply_url="https://jobs.lever.co/acme/123/apply"):
    job = MagicMock()
    job.id = uuid.uuid4()
    job.apply_url = apply_url
    return job


def _make_plan():
    return AutomationFillPlan(
        application_url="https://jobs.lever.co/acme/123/apply",
        fields=[],
        notes=[],
    )


def _build_service(app, job, inspection=None, plan=None):
    app_repo = MagicMock()
    app_repo.get_by_id.return_value = app
    app_repo.update_fields.return_value = app

    job_repo = MagicMock()
    job_repo.get_by_id.return_value = job

    automation_svc = MagicMock()
    inspection_result = inspection or {"fields": [], "title": None, "job_context": None}
    automation_svc.inspect_application_page.return_value = inspection_result

    planning_svc = MagicMock()
    planning_svc.build_fill_plan.return_value = plan or _make_plan()

    fill_svc = MagicMock()
    fill_svc.fill_and_submit_from_plan.return_value = MagicMock()

    service = ApplicationPipelineService(
        application_repo=app_repo,
        job_repo=job_repo,
        automation_service=automation_svc,
        planning_service=planning_svc,
        fill_service=fill_svc,
    )
    return service, app_repo, fill_svc


# ---------------------------------------------------------------------------
# _validate_submission_guardrails
# ---------------------------------------------------------------------------

class TestValidateSubmissionGuardrails:

    def test_passes_when_awaiting_submission_and_auto_submit(self):
        """No error when status=awaiting_submission, ready, and auto-submit."""
        app = _make_application(
            status=APPLICATION_STATUS_AWAITING_SUBMISSION,
            is_ready_for_automation=True,
            manual_review_required=False,
        )
        service, _, _ = _build_service(app, _make_job())
        # Should not raise
        service._validate_submission_guardrails(app)

    def test_passes_when_filled_and_authorized(self):
        """No error when status=filled, ready, manual_review_required=True, is_authorized=True."""
        app = _make_application(
            status=APPLICATION_STATUS_FILLED,
            is_ready_for_automation=True,
            manual_review_required=True,
            is_authorized_to_submit=True,
        )
        service, _, _ = _build_service(app, _make_job())
        service._validate_submission_guardrails(app)

    def test_blocks_when_status_is_not_filled_or_awaiting(self):
        """Rejects applications that have not completed the fill pipeline."""
        app = _make_application(
            status=APPLICATION_STATUS_SAVED,
            is_ready_for_automation=True,
            manual_review_required=False,
        )
        service, _, _ = _build_service(app, _make_job())

        with pytest.raises(ValueError, match="fill pipeline has not completed"):
            service._validate_submission_guardrails(app)

    def test_blocks_when_not_ready_for_automation(self):
        """Rejects applications where readiness check has not passed."""
        app = _make_application(
            status=APPLICATION_STATUS_AWAITING_SUBMISSION,
            is_ready_for_automation=False,
            manual_review_required=False,
        )
        service, _, _ = _build_service(app, _make_job())

        with pytest.raises(ValueError, match="not ready for automation"):
            service._validate_submission_guardrails(app)

    def test_blocks_when_manual_review_required_and_not_authorized(self):
        """Rejects when manual review is required but authorization was not given."""
        app = _make_application(
            status=APPLICATION_STATUS_FILLED,
            is_ready_for_automation=True,
            manual_review_required=True,
            is_authorized_to_submit=False,
        )
        service, _, _ = _build_service(app, _make_job())

        with pytest.raises(ValueError, match="user authorization is required"):
            service._validate_submission_guardrails(app)

    def test_collects_multiple_error_messages(self):
        """When multiple guardrails fail, all messages appear in the error."""
        app = _make_application(
            status=APPLICATION_STATUS_SAVED,
            is_ready_for_automation=False,
            manual_review_required=True,
            is_authorized_to_submit=False,
        )
        service, _, _ = _build_service(app, _make_job())

        with pytest.raises(ValueError) as exc_info:
            service._validate_submission_guardrails(app)

        error_text = str(exc_info.value)
        assert "fill pipeline has not completed" in error_text
        assert "not ready for automation" in error_text
        assert "user authorization is required" in error_text


# ---------------------------------------------------------------------------
# submit_application
# ---------------------------------------------------------------------------

class TestSubmitApplication:

    def test_submit_advances_status_to_submitted(self):
        """Happy path: guardrails pass, fill+submit runs, status set to submitted."""
        app = _make_application(
            status=APPLICATION_STATUS_AWAITING_SUBMISSION,
            is_ready_for_automation=True,
            manual_review_required=False,
        )
        job = _make_job()
        service, app_repo, fill_svc = _build_service(app, job)

        service.submit_application(app.user_id, app.id)

        fill_svc.fill_and_submit_from_plan.assert_called_once()
        update_statuses = {
            call.kwargs["status"]
            for call in app_repo.update_fields.call_args_list
            if "status" in call.kwargs
        }
        assert APPLICATION_STATUS_SUBMITTED in update_statuses

    def test_submit_raises_permission_error_for_wrong_user(self):
        """Returns PermissionError when user does not own the application."""
        app = _make_application(
            status=APPLICATION_STATUS_AWAITING_SUBMISSION,
            is_ready_for_automation=True,
        )
        job = _make_job()
        service, _, _ = _build_service(app, job)

        different_user_id = uuid.uuid4()
        with pytest.raises(PermissionError):
            service.submit_application(different_user_id, app.id)

    def test_submit_raises_value_error_when_guardrails_fail(self):
        """Returns ValueError when safety guardrails are not met."""
        app = _make_application(
            status=APPLICATION_STATUS_SAVED,  # pipeline not run
            is_ready_for_automation=True,
        )
        job = _make_job()
        service, _, fill_svc = _build_service(app, job)

        with pytest.raises(ValueError, match="Submission blocked"):
            service.submit_application(app.user_id, app.id)

        fill_svc.fill_and_submit_from_plan.assert_not_called()

    def test_submit_retries_transient_http_5xx_then_succeeds(self):
        app = _make_application(
            status=APPLICATION_STATUS_AWAITING_SUBMISSION,
            is_ready_for_automation=True,
            manual_review_required=False,
        )
        job = _make_job()
        service, _, _ = _build_service(app, job)

        service.automation_service.inspect_application_page.side_effect = [
            RuntimeError("HTTP 503 from ATS endpoint"),
            {"fields": [], "title": None, "job_context": None},
        ]

        with patch("src.domain.applications.pipeline_service.sleep") as sleep_mock:
            service.submit_application(app.user_id, app.id)

        assert service.automation_service.inspect_application_page.call_count == 2
        sleep_mock.assert_called_once_with(1)

    def test_submit_does_not_retry_permanent_already_applied_signal(self):
        app = _make_application(
            status=APPLICATION_STATUS_AWAITING_SUBMISSION,
            is_ready_for_automation=True,
            manual_review_required=False,
        )
        job = _make_job()
        service, app_repo, fill_svc = _build_service(app, job)

        fill_svc.fill_and_submit_from_plan.side_effect = RuntimeError(
            "already applied signal detected"
        )

        with pytest.raises(RuntimeError):
            service.submit_application(app.user_id, app.id)

        assert fill_svc.fill_and_submit_from_plan.call_count == 1
        failed_calls = [
            c for c in app_repo.update_fields.call_args_list
            if c.kwargs.get("status") == APPLICATION_STATUS_FAILED
        ]
        assert len(failed_calls) == 1
        assert "already_applied_signal (permanent)" in failed_calls[0].kwargs.get(
            "failure_reason", ""
        )
