"""
Local storage integration.

Handles saving uploaded files to the local filesystem during development.
Later this can be replaced with S3 or another object store.
"""

import os
import shutil
import uuid
from pathlib import Path

from src.core.config import API_SERVICE_DIR, RESUME_UPLOADS_DIR


class LocalStorageService:
    def __init__(self, base_upload_dir: str | None = None):
        upload_dir = Path(base_upload_dir) if base_upload_dir else RESUME_UPLOADS_DIR
        if not upload_dir.is_absolute():
            upload_dir = API_SERVICE_DIR / upload_dir

        self.base_upload_dir = str(upload_dir)
        os.makedirs(self.base_upload_dir, exist_ok=True)

    def save_upload(self, upload_file):
        file_ext = ""
        if upload_file.filename and "." in upload_file.filename:
            file_ext = "." + upload_file.filename.split(".")[-1]

        stored_name = str(uuid.uuid4()) + file_ext
        stored_path = os.path.join(self.base_upload_dir, stored_name)

        with open(stored_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)

        return stored_path

    def get_read_path(self, stored_path: str) -> str:
        """Return the stored path unchanged — local files are read directly."""
        return stored_path

    def delete(self, stored_path: str) -> None:
        """Delete a locally stored file if present."""
        if os.path.exists(stored_path):
            os.remove(stored_path)