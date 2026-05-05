"""
Storage helpers.

Pure utility functions for reading files back regardless of where they are stored.
"""

import os
import shutil
import tempfile
from urllib.parse import unquote

import boto3
import requests
from botocore.exceptions import ClientError

from src.core.config import API_SERVICE_DIR, settings


def open_stored_file(read_path: str) -> tuple[str, bool]:
    """
    Return a local filesystem path for reading a stored file.

    Handles three cases:
    - ``s3://bucket/key`` — downloads via boto3 to a temp file; caller must delete.
    - ``https://...``     — downloads via HTTP (e.g. pre-signed URL) to a temp file; caller must delete.
    - Local path          — returned unchanged; no cleanup needed.

    Returns ``(local_path, is_temp)``.
    """
    if read_path.startswith("s3://"):
        # Parse s3://bucket/key
        without_scheme = read_path[len("s3://"):]
        bucket, _, key = without_scheme.partition("/")
        key = unquote(key)

        if not bucket or not key:
            raise ValueError(f"Invalid S3 URI for resume read: {read_path}")

        s3 = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            aws_session_token=settings.aws_session_token,
        )

        original_filename = os.path.basename(key)
        tmp_dir = tempfile.mkdtemp()
        local_path = os.path.join(tmp_dir, original_filename)
        try:
            s3.download_file(bucket, key, local_path)
        except ClientError as exc:
            # Surface actionable context instead of a generic HeadObject failure.
            raise ValueError(
                "Failed to download resume from S3 "
                f"(bucket={bucket}, key={key}, region={settings.aws_region}). "
                "Check AWS credentials/session token, bucket, key, and region. "
                f"Original error: {exc}"
            ) from exc
        return local_path, True

    if read_path.startswith("http"):
        resp = requests.get(read_path, timeout=30)
        resp.raise_for_status()

        original_filename = os.path.basename(read_path.split("?")[0])
        tmp_dir = tempfile.mkdtemp()
        local_path = os.path.join(tmp_dir, original_filename or "resume.pdf")
        with open(local_path, "wb") as f:
            f.write(resp.content)
        return local_path, True

    local_path = read_path
    if not os.path.isabs(local_path) and local_path.startswith("uploads/"):
        local_path = str(API_SERVICE_DIR / local_path)

    return local_path, False
