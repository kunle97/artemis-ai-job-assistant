"""
Unit tests for ApplicationPipelineService.run_pipeline.

Verifies that the orchestrator advances Application.status through
each stage and handles error/gate scenarios correctly.
"""

import uuid
from unittest.mock import MagicMock, call, patch

import pytest

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
from src.domain.applications.pipeline_service import ApplicationPipelineService
from src.domain.automation.planning.models import AutomationFillPlan


@pytest.fixture(autouse=True)
def disable_run_snapshots():
    with patch("src.domain.applications.pipeline_service._should_use_run_snapshots", return_value=False):
        yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_application(
    *,
    user_id=None,
    job_id=None,
    status="saved",
    manual_review_required=True,
    is_authorized_to_submit=False,
    automation_snapshot_path=None,
):
    app = MagicMock()
    app.id = uuid.uuid4()
    app.user_id = user_id or uuid.uuid4()
    app.job_id = job_id or uuid.uuid4()
    app.status = status
    app.manual_review_required = manual_review_required
    app.is_authorized_to_submit = is_authorized_to_submit
    app.automation_snapshot_path = automation_snapshot_path
    return app


def _make_job(apply_url="https://jobs.lever.co/acme/123/apply"):
    job = MagicMock()
    job.id = uuid.uuid4()
    job.apply_url = apply_url
    return job


def _make_inspection_result(fields=None):
    result = MagicMock()
    result.title = "Software Engineer at Acme"
    result.job_context = None
    result.fields = fields or []
    return result


def _make_plan(fields=None):
    return AutomationFillPlan(
        application_url="https://jobs.lever.co/acme/123/apply",
        fields=fields or [],
        notes=["Plan built."],
    )


def _make_fill_result(filled_count=3, skipped_count=1):
    result = MagicMock()
    result.filled_count = filled_count
    result.skipped_count = skipped_count
    return result


def _build_service(app, job, inspection, plan, fill_result):
    user_id = app.user_id

    app_repo = MagicMock()
    app_repo.get_by_id.return_value = app
    app_repo.update_fields.return_value = app

    job_repo = MagicMock()
    job_repo.get_by_id.return_value = job

    automation_svc = MagicMock()
    automation_svc.inspect_application_page.return_value = inspection

    planning_svc = MagicMock()
    planning_svc.build_fill_plan.return_value = plan

    fill_svc = MagicMock()
    fill_svc.fill_from_plan.return_value = fill_result

    service = ApplicationPipelineService(
        application_repo=app_repo,
        job_repo=job_repo,
        automation_service=automation_svc,
        planning_service=planning_svc,
        fill_service=fill_svc,
    )
    return service, app_repo, automation_svc, planning_svc, fill_svc


# ---------------------------------------------------------------------------
# Tests — successful full pipeline run
# ---------------------------------------------------------------------------

def test_run_pipeline_advances_through_all_stages():
    app = _make_application()
    job = _make_job()
    inspection = _make_inspection_result()
    plan = _make_plan()
    fill_result = _make_fill_result()

    service, app_repo, automation_svc, planning_svc, fill_svc = _build_service(
        app, job, inspection, plan, fill_result
    )

    service.run_pipeline(app.user_id, app.id)

    # Verify key stages were set
    statuses_set = {
        kw["status"]
        for _, kw in [c for c in app_repo.update_fields.call_args_list]
        if "status" in kw
    }
    assert APPLICATION_STATUS_QUEUED in statuses_set
    assert APPLICATION_STATUS_INSPECTING in statuses_set
    assert APPLICATION_STATUS_INSPECTED in statuses_set
    assert APPLICATION_STATUS_PLANNING in statuses_set
    assert APPLICATION_STATUS_PLANNED in statuses_set
    assert APPLICATION_STATUS_FILLING in statuses_set
    assert APPLICATION_STATUS_FILLED in statuses_set


def test_run_pipeline_calls_inspect_with_job_url():
    app = _make_application()
    job = _make_job(apply_url="https://jobs.lever.co/acme/abc/apply")
    inspection = _make_inspection_result()
    plan = _make_plan()
    fill_result = _make_fill_result()

    service, _, automation_svc, _, _ = _build_service(app, job, inspection, plan, fill_result)
    service.run_pipeline(app.user_id, app.id)

    automation_svc.inspect_application_page.assert_called_once()
    call_arg = automation_svc.inspect_application_page.call_args[0][0]
    assert call_arg.application_url == "https://jobs.lever.co/acme/abc/apply"


def test_run_pipeline_calls_fill_from_plan_with_plan():
    app = _make_application()
    job = _make_job()
    inspection = _make_inspection_result()
    plan = _make_plan()
    fill_result = _make_fill_result()

    service, _, _, _, fill_svc = _build_service(app, job, inspection, plan, fill_result)
    service.run_pipeline(app.user_id, app.id)

    fill_svc.fill_from_plan.assert_called_once()
    kwargs = fill_svc.fill_from_plan.call_args.kwargs
    assert kwargs["plan"] is plan
    assert kwargs["application_id"] == app.id


def test_run_pipeline_marks_submitted_when_already_applied_detected_on_inspection():
    app = _make_application()
    job = _make_job()
    inspection = {
        "title": "Software Engineer",
        "job_context": None,
        "fields": [],
        "already_applied": True,
    }

    app_repo = MagicMock()
    app_repo.get_by_id.return_value = app
    app_repo.update_fields.return_value = app

    job_repo = MagicMock()
    job_repo.get_by_id.return_value = job

    automation_svc = MagicMock()
    automation_svc.inspect_application_page.return_value = inspection

    planning_svc = MagicMock()
    fill_svc = MagicMock()

    service = ApplicationPipelineService(
        application_repo=app_repo,
        job_repo=job_repo,
        automation_service=automation_svc,
        planning_service=planning_svc,
        fill_service=fill_svc,
    )

    service.run_pipeline(app.user_id, app.id)

    statuses_set = {
        kw["status"]
        for _, kw in [c for c in app_repo.update_fields.call_args_list]
        if "status" in kw
    }
    assert APPLICATION_STATUS_SUBMITTED in statuses_set
    planning_svc.build_fill_plan.assert_not_called()
    fill_svc.fill_from_plan.assert_not_called()


def test_submit_application_deletes_snapshot_after_confirmed_submission():
    app = _make_application(
        status=APPLICATION_STATUS_AWAITING_SUBMISSION,
        manual_review_required=False,
        automation_snapshot_path="/tmp/automation-snapshot.html",
    )
    app.is_ready_for_automation = True
    job = _make_job()
    inspection = _make_inspection_result()
    plan = _make_plan()
    fill_result = MagicMock()
    fill_result.submission_confirmed = True

    service, app_repo, automation_svc, planning_svc, fill_svc = _build_service(
        app, job, inspection, plan, fill_result
    )
    service.snapshot_store = MagicMock()

    service.submit_application(app.user_id, app.id)

    service.snapshot_store.delete.assert_called_once_with("/tmp/automation-snapshot.html")
    assert any(
        call.kwargs.get("automation_snapshot_path") is None
        for call in app_repo.update_fields.call_args_list
    )


# ---------------------------------------------------------------------------
# Tests — gate check after fill
# ---------------------------------------------------------------------------

def test_run_pipeline_advances_to_awaiting_submission_when_auto_submit():
    app = _make_application(manual_review_required=False, is_authorized_to_submit=False)
    app.status = APPLICATION_STATUS_FILLED

    job = _make_job()
    inspection = _make_inspection_result()
    plan = _make_plan()
    fill_result = _make_fill_result()

    service, app_repo, _, _, _ = _build_service(app, job, inspection, plan, fill_result)

    # After setting filled, get_by_id returns the filled app for the gate check
    filled_app = _make_application(
        user_id=app.user_id,
        job_id=app.job_id,
        status=APPLICATION_STATUS_FILLED,
        manual_review_required=False,
    )
    app_repo.get_by_id.return_value = filled_app
    app_repo.update_fields.return_value = filled_app

    service.run_pipeline(app.user_id, app.id)

    statuses_set = {
        kw["status"]
        for _, kw in [c for c in app_repo.update_fields.call_args_list]
        if "status" in kw
    }
    assert APPLICATION_STATUS_AWAITING_SUBMISSION in statuses_set


def test_run_pipeline_halts_at_filled_when_manual_review_required():
    app = _make_application(manual_review_required=True, is_authorized_to_submit=False)

    job = _make_job()
    inspection = _make_inspection_result()
    plan = _make_plan()
    fill_result = _make_fill_result()

    service, app_repo, _, _, _ = _build_service(app, job, inspection, plan, fill_result)

    filled_app = _make_application(
        user_id=app.user_id,
        job_id=app.job_id,
        status=APPLICATION_STATUS_FILLED,
        manual_review_required=True,
        is_authorized_to_submit=False,
    )
    app_repo.get_by_id.return_value = filled_app
    app_repo.update_fields.return_value = filled_app

    service.run_pipeline(app.user_id, app.id)

    statuses_set = {
        kw["status"]
        for _, kw in [c for c in app_repo.update_fields.call_args_list]
        if "status" in kw
    }
    assert APPLICATION_STATUS_AWAITING_SUBMISSION not in statuses_set


# ---------------------------------------------------------------------------
# Tests — error handling
# ---------------------------------------------------------------------------

def test_run_pipeline_sets_failed_status_on_exception():
    app = _make_application()
    job = _make_job()

    app_repo = MagicMock()
    app_repo.get_by_id.return_value = app
    app_repo.update_fields.return_value = app

    job_repo = MagicMock()
    job_repo.get_by_id.return_value = job

    automation_svc = MagicMock()
    automation_svc.inspect_application_page.side_effect = RuntimeError("Playwright crashed")

    planning_svc = MagicMock()
    fill_svc = MagicMock()

    service = ApplicationPipelineService(
        application_repo=app_repo,
        job_repo=job_repo,
        automation_service=automation_svc,
        planning_service=planning_svc,
        fill_service=fill_svc,
    )

    with pytest.raises(RuntimeError):
        service.run_pipeline(app.user_id, app.id)

    failed_calls = [
        c for c in app_repo.update_fields.call_args_list
        if c.kwargs.get("status") == APPLICATION_STATUS_FAILED
    ]
    assert len(failed_calls) == 1
    failure_reason = failed_calls[0].kwargs.get("failure_reason", "")
    assert "unclassified_error (permanent)" in failure_reason
    assert "Playwright crashed" in failure_reason


def test_run_pipeline_retries_on_transient_timeout_then_succeeds():
    app = _make_application()
    job = _make_job()
    inspection = _make_inspection_result()
    plan = _make_plan()
    fill_result = _make_fill_result()

    service, _, automation_svc, _, _ = _build_service(app, job, inspection, plan, fill_result)
    automation_svc.inspect_application_page.side_effect = [
        RuntimeError("Playwright timeout while waiting for selector"),
        inspection,
    ]

    with patch("src.domain.applications.pipeline_service.sleep") as sleep_mock:
        service.run_pipeline(app.user_id, app.id)

    assert automation_svc.inspect_application_page.call_count == 2
    sleep_mock.assert_called_once_with(1)


def test_run_pipeline_does_not_retry_permanent_captcha_failure():
    app = _make_application()
    job = _make_job()

    app_repo = MagicMock()
    app_repo.get_by_id.return_value = app
    app_repo.update_fields.return_value = app

    job_repo = MagicMock()
    job_repo.get_by_id.return_value = job

    automation_svc = MagicMock()
    automation_svc.inspect_application_page.side_effect = RuntimeError(
        "captcha detected on application page"
    )

    service = ApplicationPipelineService(
        application_repo=app_repo,
        job_repo=job_repo,
        automation_service=automation_svc,
        planning_service=MagicMock(),
        fill_service=MagicMock(),
    )

    with pytest.raises(RuntimeError):
        service.run_pipeline(app.user_id, app.id)

    assert automation_svc.inspect_application_page.call_count == 1
    failed_calls = [
        c for c in app_repo.update_fields.call_args_list
        if c.kwargs.get("status") == APPLICATION_STATUS_FAILED
    ]
    assert len(failed_calls) == 1
    assert "captcha_detected (permanent)" in failed_calls[0].kwargs.get("failure_reason", "")


def test_run_pipeline_raises_permission_error_for_wrong_user():
    app = _make_application()
    other_user_id = uuid.uuid4()

    app_repo = MagicMock()
    app_repo.get_by_id.return_value = app

    service = ApplicationPipelineService(
        application_repo=app_repo,
        job_repo=MagicMock(),
        automation_service=MagicMock(),
        planning_service=MagicMock(),
        fill_service=MagicMock(),
    )

    with pytest.raises(PermissionError):
        service.run_pipeline(other_user_id, app.id)


def test_run_pipeline_raises_value_error_for_missing_application():
    app_repo = MagicMock()
    app_repo.get_by_id.return_value = None

    service = ApplicationPipelineService(
        application_repo=app_repo,
        job_repo=MagicMock(),
        automation_service=MagicMock(),
        planning_service=MagicMock(),
        fill_service=MagicMock(),
    )

    with pytest.raises(ValueError, match="Application not found"):
        service.run_pipeline(uuid.uuid4(), uuid.uuid4())
