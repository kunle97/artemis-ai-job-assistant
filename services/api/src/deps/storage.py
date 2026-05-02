"""
Storage FastAPI dependency.

Provides the active StorageService instance via dependency injection.
Routes receive it through Depends(get_storage) — never instantiate it directly.
"""

from src.integrations.storage.base import StorageService
from src.integrations.storage.factory import get_storage_service


def get_storage() -> StorageService:
    """FastAPI dependency that returns the configured storage backend."""
    return get_storage_service()
