"""
Unit tests for the scheduled worker job feed task.
"""

from pathlib import Path
import sys
from uuid import uuid4
from unittest.mock import MagicMock, patch

from celery.exceptions import Retry
import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.worker.tasks import scan_job_feed_for_all_users
from services.worker.tasks import run_application_pipeline_async


@patch("services.worker.tasks.JobFeedService.scan_for_user")
@patch("services.worker.tasks.JobPreferencesRepository")
@patch("services.worker.tasks.SessionLocal")
def test_scan_job_feed_for_all_users_scans_each_enabled_user(
    mock_session_local,
    mock_preferences_repository,
    mock_scan_for_user,
):
    session = MagicMock()
    mock_session_local.return_value = session
    user_ids = [uuid4(), uuid4()]
    mock_preferences_repository.return_value.list_user_ids_with_enabled_sources.return_value = user_ids
    mock_scan_for_user.side_effect = [2, 3]

    result = scan_job_feed_for_all_users()

    assert result == {"scanned_users": 2, "failed_users": 0, "new_jobs_found": 5}
    assert mock_scan_for_user.call_count == 2
    session.close.assert_called_once()


@patch("services.worker.tasks.JobFeedService.scan_for_user")
@patch("services.worker.tasks.JobPreferencesRepository")
@patch("services.worker.tasks.SessionLocal")
def test_scan_job_feed_for_all_users_continues_after_failure(
    mock_session_local,
    mock_preferences_repository,
    mock_scan_for_user,
):
    session = MagicMock()
    mock_session_local.return_value = session
    user_ids = [uuid4(), uuid4(), uuid4()]
    mock_preferences_repository.return_value.list_user_ids_with_enabled_sources.return_value = user_ids
    mock_scan_for_user.side_effect = [2, RuntimeError("boom"), 1]

    result = scan_job_feed_for_all_users()

    assert result == {"scanned_users": 2, "failed_users": 1, "new_jobs_found": 3}
    assert mock_scan_for_user.call_count == 3
    session.close.assert_called_once()


@patch("services.worker.tasks.build_pipeline_service")
@patch("services.worker.tasks.AutomationConcurrencyLimiter")
@patch("services.worker.tasks.SessionLocal")
def test_run_application_pipeline_async_returns_final_status(
    mock_session_local,
    mock_concurrency_limiter,
    mock_build_pipeline_service,
):
    session = MagicMock()
    mock_session_local.return_value = session

    fake_application = MagicMock()
    fake_application.status = "filled"

    limiter = MagicMock()
    limiter.acquire.return_value = (True, None)
    mock_concurrency_limiter.return_value = limiter

    pipeline_service = MagicMock()
    pipeline_service.run_pipeline.return_value = fake_application
    mock_build_pipeline_service.return_value = pipeline_service

    result = run_application_pipeline_async(
        user_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
        application_id="123e4567-e89b-12d3-a456-426614174000",
    )

    assert result == {
        "application_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "filled",
    }
    pipeline_service.run_pipeline.assert_called_once()
    limiter.acquire.assert_called_once()
    limiter.release.assert_called_once()
    session.close.assert_called_once()


@patch("services.worker.tasks.build_pipeline_service")
@patch("services.worker.tasks.AutomationConcurrencyLimiter")
@patch("services.worker.tasks.SessionLocal")
def test_run_application_pipeline_async_closes_session_on_failure(
    mock_session_local,
    mock_concurrency_limiter,
    mock_build_pipeline_service,
):
    session = MagicMock()
    mock_session_local.return_value = session

    pipeline_service = MagicMock()
    pipeline_service.run_pipeline.side_effect = RuntimeError("pipeline boom")
    mock_build_pipeline_service.return_value = pipeline_service

    limiter = MagicMock()
    limiter.acquire.return_value = (True, None)
    mock_concurrency_limiter.return_value = limiter

    try:
        run_application_pipeline_async(
            user_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
            application_id="123e4567-e89b-12d3-a456-426614174000",
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected RuntimeError")

    limiter.release.assert_called_once()
    session.close.assert_called_once()


@patch("services.worker.tasks.AutomationConcurrencyLimiter")
@patch("services.worker.tasks.SessionLocal")
@patch.object(run_application_pipeline_async, "retry")
def test_run_application_pipeline_async_requeues_when_limit_reached(
    mock_retry,
    mock_session_local,
    mock_concurrency_limiter,
):
    session = MagicMock()
    mock_session_local.return_value = session

    limiter = MagicMock()
    limiter.acquire.return_value = (False, "user limit reached")
    mock_concurrency_limiter.return_value = limiter
    mock_retry.side_effect = Retry()

    with pytest.raises(Retry):
        run_application_pipeline_async(
            user_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
            application_id="123e4567-e89b-12d3-a456-426614174000",
        )

    mock_retry.assert_called_once()
    limiter.release.assert_not_called()
    session.close.assert_called_once()