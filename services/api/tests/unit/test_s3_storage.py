"""
Unit tests for S3StorageService.

Uses moto to mock AWS S3 calls so no real credentials or bucket are needed.
"""

import io
import os

import boto3
import pytest
from moto import mock_aws

from src.core.config import settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_upload_file(content: bytes, filename: str, content_type: str = "application/pdf"):
    """Return a lightweight object that matches the UploadFile interface used by S3StorageService."""

    class _FakeUploadFile:
        def __init__(self):
            self.filename = filename
            self.content_type = content_type
            self.file = io.BytesIO(content)

    return _FakeUploadFile()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _s3_env(monkeypatch):
    """Patch settings so S3StorageService uses the moto mock bucket."""
    monkeypatch.setattr(settings, "storage_backend", "s3")
    monkeypatch.setattr(settings, "aws_access_key_id", "testing")
    monkeypatch.setattr(settings, "aws_secret_access_key", "testing")
    monkeypatch.setattr(settings, "aws_region", "us-east-1")
    monkeypatch.setattr(settings, "s3_bucket_name", "test-artemis-resumes")
    monkeypatch.setattr(settings, "s3_key_prefix", "resumes")


def _create_bucket(region: str = "us-east-1") -> None:
    client = boto3.client("s3", region_name=region,
                          aws_access_key_id="testing",
                          aws_secret_access_key="testing")
    if region == "us-east-1":
        client.create_bucket(Bucket="test-artemis-resumes")
    else:
        client.create_bucket(
            Bucket="test-artemis-resumes",
            CreateBucketConfiguration={"LocationConstraint": region},
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@mock_aws
def test_save_upload_returns_s3_uri():
    """save_upload() uploads the file and returns an s3://bucket/key URI."""
    _create_bucket()

    # Import here so monkeypatched settings are already active
    from src.integrations.storage.s3_storage import S3StorageService

    service = S3StorageService()
    upload = _fake_upload_file(b"%PDF-fake-content", "resume.pdf")
    stored_path = service.save_upload(upload)

    assert stored_path.startswith("s3://test-artemis-resumes/resumes/")
    assert stored_path.endswith(".pdf")


@mock_aws
def test_save_upload_stores_correct_bytes():
    """The bytes written to S3 match the original file content."""
    _create_bucket()

    from src.integrations.storage.s3_storage import S3StorageService

    content = b"%PDF-1.4 hello world"
    service = S3StorageService()
    upload = _fake_upload_file(content, "my_resume.pdf")
    stored_path = service.save_upload(upload)

    # Derive key from stored_path
    key = stored_path.removeprefix("s3://test-artemis-resumes/")

    s3 = boto3.client("s3", region_name="us-east-1",
                      aws_access_key_id="testing",
                      aws_secret_access_key="testing")
    obj = s3.get_object(Bucket="test-artemis-resumes", Key=key)
    assert obj["Body"].read() == content


@mock_aws
def test_get_read_path_returns_presigned_url():
    """get_read_path() returns an HTTPS pre-signed URL for the stored object."""
    _create_bucket()

    from src.integrations.storage.s3_storage import S3StorageService

    service = S3StorageService()
    upload = _fake_upload_file(b"resume text", "cv.pdf")
    stored_path = service.save_upload(upload)

    read_path = service.get_read_path(stored_path)

    assert read_path.startswith("https://")
    assert "test-artemis-resumes" in read_path


@mock_aws
def test_save_upload_uses_key_prefix():
    """Objects are stored under the configured s3_key_prefix."""
    _create_bucket()

    from src.integrations.storage.s3_storage import S3StorageService

    service = S3StorageService()
    upload = _fake_upload_file(b"data", "test.pdf")
    stored_path = service.save_upload(upload)

    assert "/resumes/" in stored_path


@mock_aws
def test_save_upload_docx_extension():
    """File extension is preserved in the S3 key for DOCX files."""
    _create_bucket()

    from src.integrations.storage.s3_storage import S3StorageService

    service = S3StorageService()
    upload = _fake_upload_file(b"docx-bytes", "resume.docx",
                               content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    stored_path = service.save_upload(upload)

    assert stored_path.endswith(".docx")
