"""Tests portable local-path resolution for shared API and worker storage."""

from src.core.config import API_SERVICE_DIR
from src.integrations.storage.helpers import open_stored_file


def test_open_stored_file_remaps_host_upload_path_for_worker(monkeypatch):
    host_path = "/Users/example/project/services/api/uploads/resumes/resume.pdf"
    expected = str(API_SERVICE_DIR / "uploads" / "resumes" / "resume.pdf")

    monkeypatch.setattr("src.integrations.storage.helpers.os.path.exists", lambda path: False)

    resolved, is_temp = open_stored_file(host_path)

    assert resolved == expected
    assert is_temp is False


def test_open_stored_file_preserves_existing_absolute_path(monkeypatch):
    local_path = "/tmp/resume.pdf"
    monkeypatch.setattr("src.integrations.storage.helpers.os.path.exists", lambda path: True)

    resolved, is_temp = open_stored_file(local_path)

    assert resolved == local_path
    assert is_temp is False
