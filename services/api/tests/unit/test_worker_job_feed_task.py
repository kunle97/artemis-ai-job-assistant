"""
Unit tests for the scheduled worker job feed task.
"""

from pathlib import Path
import sys
from uuid import uuid4
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.worker.tasks import scan_job_feed_for_all_users


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