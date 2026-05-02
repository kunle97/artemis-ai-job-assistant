"""
Storage service factory.

Selects the correct storage backend at runtime based on STORAGE_BACKEND config.
Import and call get_storage_service() wherever a StorageService instance is needed.
"""

from src.core.config import settings
from src.integrations.storage.base import StorageService


def get_storage_service() -> StorageService:
    """
    Return the active storage backend based on settings.storage_backend.

    - "s3"    → S3StorageService  (staging / production)
    - default → LocalStorageService (development)
    """
    if settings.storage_backend == "s3":
        from src.integrations.storage.s3_storage import S3StorageService
        return S3StorageService()

    from src.integrations.storage.local_storage import LocalStorageService
    return LocalStorageService()
