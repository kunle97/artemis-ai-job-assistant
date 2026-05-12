"""
Resume domain service.

Coordinates resume upload, local file storage, parsing, persistence,
and candidate profile synchronization.
"""

import logging

from src.domain.resume.helpers import validate_resume_file
from src.domain.applications.repository import ApplicationRepository

logger = logging.getLogger(__name__)
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
        application_repository: ApplicationRepository,
    ):
        self.repository = repository
        self.storage_service = storage_service
        self.parser = parser
        self.profile_service = CandidateProfileService(profile_repository)
        self.application_repository = application_repository

    def upload_resume(self, user_id, upload_file):
        """
        Save an uploaded resume, extract text, persist metadata,
        and sync parsed data into the candidate profile.
        """
        logger.info("[ResumeService] upload_resume start user_id=%s filename=%s", user_id, upload_file.filename)
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

        extracted_len = len(parsed_result.get("extracted_text") or "")
        logger.info("[ResumeService] parse complete extracted_chars=%d", extracted_len)

        existing_primary = self.repository.get_primary_by_user_id(user_id)

        resume = self.repository.create(
            user_id=user_id,
            file_name=upload_file.filename,
            file_path=stored_path,
            mime_type=upload_file.content_type,
            extracted_text=parsed_result.get("extracted_text"),
            parsed_json=parsed_result.get("parsed_json"),
            variant_type="master",
            is_primary=existing_primary is None,
        )

        missing_fields: list[str] = []
        normalized_data = (parsed_result.get("parsed_json") or {}).get("normalized_data")
        if normalized_data:
            result = self.profile_service.upsert_profile_from_resume(
                user_id=user_id,
                normalized_data=normalized_data,
            )
            missing_fields = result.get("missing_fields", [])
            logger.info(
                "[ResumeService] profile sync complete missing_fields=%d",
                len(missing_fields),
            )
        else:
            logger.warning("[ResumeService] no normalized_data in parsed result — profile not synced")

        logger.info(
            "[ResumeService] upload_resume complete resume_id=%s user_id=%s",
            resume.id,
            user_id,
        )
        return resume, missing_fields

    def list_resumes(self, user_id):
        """
        Return all resumes for a user, newest first.
        """
        logger.info("[ResumeService] list_resumes user_id=%s", user_id)
        return self.repository.get_by_user_id(user_id)

    def set_primary_resume(self, user_id, resume_id):
        """
        Mark one resume as the default primary resume for a user.
        """
        logger.info("[ResumeService] set_primary_resume start user_id=%s resume_id=%s", user_id, resume_id)
        resume = self.repository.get_by_id_and_user_id(resume_id, user_id)
        if not resume:
            logger.warning("[ResumeService] set_primary_resume not found user_id=%s resume_id=%s", user_id, resume_id)
            return None

        updated = self.repository.set_primary(resume)
        logger.info("[ResumeService] set_primary_resume complete user_id=%s resume_id=%s", user_id, resume_id)
        return updated

    def delete_resume(self, user_id, resume_id):
        """
        Delete a resume owned by a user from storage and persistence.
        """
        logger.info("[ResumeService] delete_resume start user_id=%s resume_id=%s", user_id, resume_id)
        resume = self.repository.get_by_id_and_user_id(resume_id, user_id)
        if not resume:
            logger.warning("[ResumeService] delete_resume not found user_id=%s resume_id=%s", user_id, resume_id)
            return False

        updated_rows = self.application_repository.clear_resume_references(user_id, resume_id)
        if updated_rows:
            logger.info(
                "[ResumeService] cleared application resume references count=%d user_id=%s resume_id=%s",
                updated_rows,
                user_id,
                resume_id,
            )

        self.storage_service.delete(resume.file_path)
        self.repository.delete(resume)
        logger.info("[ResumeService] delete_resume complete user_id=%s resume_id=%s", user_id, resume_id)
        return True