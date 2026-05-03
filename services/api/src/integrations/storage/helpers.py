"""
Storage helpers.

Pure utility functions for reading files back regardless of where they are stored.
"""

import os
import shutil
import tempfile

import boto3
import requests

from src.core.config import settings


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

        s3 = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

        original_filename = os.path.basename(key)
        tmp_dir = tempfile.mkdtemp()
        local_path = os.path.join(tmp_dir, original_filename)
        s3.download_file(bucket, key, local_path)
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

    return read_path, False
