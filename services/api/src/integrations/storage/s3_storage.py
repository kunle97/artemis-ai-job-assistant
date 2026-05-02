"""
AWS S3 storage backend.

Uploads resume files to S3 and returns pre-signed URLs for reading them back.
Used when STORAGE_BACKEND=s3 (staging / production environments).
"""

import uuid

import boto3

from src.core.config import settings


class S3StorageService:
    """
    StorageService implementation backed by AWS S3.
    """

    def __init__(self):
        self._client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self._bucket = settings.s3_bucket_name
        self._prefix = settings.s3_key_prefix

    def save_upload(self, upload_file) -> str:
        """
        Upload a file to S3 and return an s3://bucket/key URI.
        """
        ext = ""
        if upload_file.filename and "." in upload_file.filename:
            ext = "." + upload_file.filename.rsplit(".", 1)[-1]

        key = f"{self._prefix}/{uuid.uuid4()}{ext}"

        self._client.upload_fileobj(
            upload_file.file,
            self._bucket,
            key,
            ExtraArgs={"ContentType": upload_file.content_type or "application/octet-stream"},
        )

        return f"s3://{self._bucket}/{key}"

    def get_read_path(self, stored_path: str) -> str:
        """
        Generate a 15-minute pre-signed URL for reading the stored file.
        """
        key = stored_path.removeprefix(f"s3://{self._bucket}/")
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=900,
        )
