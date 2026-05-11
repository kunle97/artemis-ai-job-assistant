"""Automation snapshot storage.

Stores HTML snapshots in a backend-agnostic way and materializes them as
local file URLs for inspect/fill runs.
"""

from __future__ import annotations

import logging
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from uuid import uuid4

import boto3

from src.core.config import AUTOMATION_UPLOADS_DIR, settings


logger = logging.getLogger(__name__)


class AutomationSnapshotStore:
    """Persist and materialize automation snapshots across storage backends."""

    def save_html(self, html: str) -> str:
        """Persist a snapshot and return its stable stored path."""
        if settings.storage_backend == "s3":
            return self._save_html_to_s3(html)
        return self._save_html_locally(html)

    @contextmanager
    def materialize_runtime_url(self, stored_path: str) -> Iterator[str]:
        """Yield a local file:// URL for inspect/fill, downloading if necessary."""
        if stored_path.startswith("s3://"):
            temp_path = self._download_s3_snapshot(stored_path)
            try:
                yield temp_path.as_uri()
            finally:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    logger.warning(
                        "[AutomationSnapshotStore] Failed to remove temp snapshot %s",
                        temp_path,
                    )
            return

        local_path = Path(stored_path).expanduser().resolve()
        yield local_path.as_uri()

    def delete(self, stored_path: str) -> None:
        """Delete a persisted snapshot."""
        if not stored_path:
            return

        if stored_path.startswith("s3://"):
            self._delete_s3_snapshot(stored_path)
            return

        snapshot_path = Path(stored_path).expanduser().resolve()
        snapshot_path.unlink(missing_ok=True)

    def _save_html_locally(self, html: str) -> str:
        snapshot_dir = AUTOMATION_UPLOADS_DIR / "snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = snapshot_dir / f"{uuid4()}.html"
        snapshot_path.write_text(html, encoding="utf-8")
        return str(snapshot_path.resolve())

    def _save_html_to_s3(self, html: str) -> str:
        if not settings.s3_bucket_name:
            raise ValueError("S3 snapshot storage requires S3_BUCKET_NAME to be configured.")

        key = f"{settings.automation_snapshot_s3_key_prefix.rstrip('/')}/{uuid4()}.html"
        client = self._build_s3_client()
        client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=key,
            Body=html.encode("utf-8"),
            ContentType="text/html; charset=utf-8",
        )
        return f"s3://{settings.s3_bucket_name}/{key}"

    def _download_s3_snapshot(self, stored_path: str) -> Path:
        bucket, key = self._parse_s3_uri(stored_path)
        client = self._build_s3_client()

        fd, temp_name = tempfile.mkstemp(suffix=".html", prefix="automation-snapshot-")
        os.close(fd)
        temp_path = Path(temp_name)
        client.download_file(bucket, key, str(temp_path))
        logger.info(
            "[AutomationSnapshotStore] Downloaded snapshot from S3 stored_path=%s temp_path=%s",
            stored_path,
            temp_path,
        )
        return temp_path

    def _delete_s3_snapshot(self, stored_path: str) -> None:
        bucket, key = self._parse_s3_uri(stored_path)
        client = self._build_s3_client()
        client.delete_object(Bucket=bucket, Key=key)

    def _build_s3_client(self):
        return boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            aws_session_token=settings.aws_session_token,
        )

    def _parse_s3_uri(self, stored_path: str) -> tuple[str, str]:
        without_scheme = stored_path[len("s3://"):]
        bucket, _, key = without_scheme.partition("/")
        if not bucket or not key:
            raise ValueError(f"Invalid S3 snapshot URI: {stored_path}")
        return bucket, key