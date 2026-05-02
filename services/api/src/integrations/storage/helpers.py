"""
Storage helpers.

Pure utility functions for reading files back regardless of where they are stored.
"""

import os
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

        suffix = os.path.splitext(key)[1]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.close()
        s3.download_file(bucket, key, tmp.name)
        return tmp.name, True

    if read_path.startswith("http"):
        resp = requests.get(read_path, timeout=30)
        resp.raise_for_status()

        suffix = os.path.splitext(read_path.split("?")[0])[1]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(resp.content)
        tmp.flush()
        tmp.close()
        return tmp.name, True

    return read_path, False
