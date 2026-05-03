"""
Resume domain service.

Coordinates resume upload, local file storage, parsing, persistence,
and candidate profile synchronization.
"""

from src.domain.resume.helpers import validate_resume_file
from src.domain.resume.repository import ResumeRepository
from src.integrations.storage.base import StorageService
from src.integrations.storage.helpers import open_stored_file
from src.domain.resume.parser import ResumeParser
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.profile.service import CandidateProfileService


class ResumeService:
    """
    Handles resume upload workflows.
    """

    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

    def __init__(
        self,
        repository: ResumeRepository,
        storage_service: StorageService,
        parser: ResumeParser,
        profile_repository: CandidateProfileRepository,
    ):
        self.repository = repository
        self.storage_service = storage_service
        self.parser = parser
        self.profile_service = CandidateProfileService(profile_repository)

    def upload_resume(self, user_id, upload_file):
        """
        Save an uploaded resume, extract text, persist metadata,
        and sync parsed data into the candidate profile.
        """
        validate_resume_file(upload_file, self.ALLOWED_EXTENSIONS)

        stored_path = self.storage_service.save_upload(upload_file)
        read_path = self.storage_service.get_read_path(stored_path)
        local_path, is_temp = open_stored_file(read_path)
        try:
            parsed_result = self.parser.parse(local_path)
        finally:
            if is_temp:
                import os
                os.unlink(local_path)

        resume = self.repository.create(
            user_id=user_id,
            file_name=upload_file.filename,
            file_path=stored_path,
            mime_type=upload_file.content_type,
            extracted_text=parsed_result.get("extracted_text"),
            parsed_json=parsed_result.get("parsed_json"),
            variant_type="master",
            is_primary=False,
        )

        missing_fields: list[str] = []
        normalized_data = (parsed_result.get("parsed_json") or {}).get("normalized_data")
        if normalized_data:
            result = self.profile_service.upsert_profile_from_resume(
                user_id=user_id,
                normalized_data=normalized_data,
            )
            missing_fields = result.get("missing_fields", [])

        return resume, missing_fields

    def list_resumes(self, user_id):
        """
        Return all resumes for a user, newest first.
        """
        return self.repository.get_by_user_id(user_id)