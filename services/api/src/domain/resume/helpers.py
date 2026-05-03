"""
Resume domain helper functions.

Contains reusable validation for uploaded resume files.
"""

from pathlib import Path


def validate_resume_file(upload_file, allowed_extensions: set[str]) -> None:
    """Ensure Artemis only accepts supported resume file types."""
    if not upload_file.filename:
        raise ValueError("Uploaded file must have a file name.")

    extension = Path(upload_file.filename).suffix.lower()
    if extension not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise ValueError(f"Unsupported resume file type. Allowed types: {allowed}")
