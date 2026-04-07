"""
Resume domain service.

Coordinates resume upload, local file storage, parsing, and persistence.
"""

from pathlib import Path

from app.domains.resume.repository import ResumeRepository
from app.integrations.storage.local_storage import LocalStorageService
from app.domains.resume.parser import ResumeParser


class ResumeService:
    """
    Handles resume upload workflows.
    """

    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

    def __init__(
        self,
        repository: ResumeRepository,
        storage_service: LocalStorageService,
        parser: ResumeParser,
    ):
        self.repository = repository
        self.storage_service = storage_service
        self.parser = parser

    def upload_resume(self, user_id, upload_file):
        """
        Save an uploaded resume, extract text, and persist metadata.
        """
        self._validate_file(upload_file)

        stored_path = self.storage_service.save_upload(upload_file)
        parsed_result = self.parser.parse(stored_path)

        return self.repository.create(
            user_id=user_id,
            file_name=upload_file.filename,
            file_path=stored_path,
            mime_type=upload_file.content_type,
            extracted_text=parsed_result.get("extracted_text"),
            parsed_json=parsed_result.get("parsed_json"),
            variant_type="master",
            is_primary=False,
        )

    def list_resumes(self, user_id):
        """
        Return all resumes for a user, newest first.
        """
        return self.repository.get_by_user_id(user_id)

    def _validate_file(self, upload_file) -> None:
        """
        Ensure Artemis only accepts supported resume file types.
        """
        if not upload_file.filename:
            raise ValueError("Uploaded file must have a file name.")

        extension = Path(upload_file.filename).suffix.lower()
        if extension not in self.ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(self.ALLOWED_EXTENSIONS))
            raise ValueError(f"Unsupported resume file type. Allowed types: {allowed}")