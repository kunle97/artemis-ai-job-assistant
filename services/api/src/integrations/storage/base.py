"""
Storage service protocol.

Defines the shared interface that all storage backends (local, S3, etc.) must satisfy.
Routes and domain services depend on this protocol, not on any specific backend.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class StorageService(Protocol):
    def save_upload(self, upload_file) -> str:
        """Save an uploaded file and return its storage path or URI."""
        ...

    def get_read_path(self, stored_path: str) -> str:
        """
        Return a path or URL suitable for reading the file back.

        For local storage this is the original path unchanged.
        For S3 this returns a short-lived pre-signed HTTPS URL.
        """
        ...
