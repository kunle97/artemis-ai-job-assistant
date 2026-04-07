"""
Local storage integration.

Handles saving uploaded files to the local filesystem during development.
Later this can be replaced with S3 or another object store.
"""

import os
import shutil
import uuid


class LocalStorageService:
    def __init__(self, base_upload_dir: str = "uploads/resumes"):
        self.base_upload_dir = base_upload_dir
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