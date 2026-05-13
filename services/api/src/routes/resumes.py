"""
Resume API routes.

Thin HTTP endpoints for uploading and listing resumes for the authenticated user.
Business logic stays in the resume service layer.
"""

from uuid import UUID
import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
import requests
from sqlalchemy.orm import Session

from src.deps.auth import get_current_user
from src.deps.storage import get_storage
from src.domain.applications.repository import ApplicationRepository
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.resume.parser import ResumeParser
from src.domain.resume.repository import ResumeRepository
from src.domain.resume.schemas import ResumeRead, ResumeUploadResponse
from src.domain.resume.service import ResumeService
from src.infrastructure.db.session import get_db
from src.integrations.storage.base import StorageService

router = APIRouter(prefix="/resumes", tags=["resumes"])


def _build_resume_service(db: Session, storage_service: StorageService) -> ResumeService:
    """
    Build the resume service and its dependencies.
    """
    repository = ResumeRepository(db)
    profile_repository = CandidateProfileRepository(db)
    application_repository = ApplicationRepository(db)
    parser = ResumeParser()

    return ResumeService(
        repository=repository,
        storage_service=storage_service,
        parser=parser,
        profile_repository=profile_repository,
        application_repository=application_repository,
    )


# Suggested resume format note surfaced in the upload response.
_FORMAT_HINT = (
    "For best autofill results, use a clean single-column resume with clearly labelled "
    "sections (Experience, Education, Skills) and your LinkedIn/GitHub URLs visible in "
    "the header."
)


@router.post("/upload", response_model=ResumeUploadResponse)
def upload_resume(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage),
):
    """
    Upload a resume for the authenticated user.
    Returns the saved resume and any profile fields that could not be auto-populated.
    """
    service = _build_resume_service(db, storage_service)

    try:
        resume, missing_fields = service.upload_resume(
            user_id=current_user.id,
            upload_file=file,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    message = _FORMAT_HINT if missing_fields else "Profile updated from resume."
    return ResumeUploadResponse(
        **ResumeRead.model_validate(resume).model_dump(),
        missing_profile_fields=missing_fields,
        message=message,
    )


@router.get("", response_model=list[ResumeRead])
def list_resumes(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage),
):
    """
    Return resumes for the authenticated user.
    """
    service = _build_resume_service(db, storage_service)
    return service.list_resumes(current_user.id)


@router.delete("/{resume_id}")
def delete_resume(
    resume_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage),
):
    """
    Delete a resume for the authenticated user.
    """
    service = _build_resume_service(db, storage_service)
    deleted = service.delete_resume(current_user.id, resume_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resume not found.")

    return {"message": "Resume deleted."}


@router.patch("/{resume_id}/primary", response_model=ResumeRead)
def set_primary_resume(
    resume_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage),
):
    """
    Mark a resume as the authenticated user's default resume.
    """
    service = _build_resume_service(db, storage_service)
    resume = service.set_primary_resume(current_user.id, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    return resume


@router.get("/{resume_id}/download")
def download_resume(
    resume_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage),
):
    """
    Download a resume for the authenticated user.

    For local storage, returns a file response.
    For remote storage (e.g. S3), redirects to a pre-signed URL.
    """
    service = _build_resume_service(db, storage_service)
    resume, read_path = service.get_resume_download(current_user.id, resume_id)
    if not resume or not read_path:
        raise HTTPException(status_code=404, detail="Resume not found.")

    if isinstance(read_path, str) and read_path.startswith("http"):
        upstream = requests.get(read_path, stream=True, timeout=30)
        if upstream.status_code >= 400:
            raise HTTPException(status_code=404, detail="Resume file not found.")

        media_type = upstream.headers.get("content-type") or resume.mime_type or "application/octet-stream"

        def iter_content():
            try:
                for chunk in upstream.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        yield chunk
            finally:
                upstream.close()

        return StreamingResponse(
            iter_content(),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{resume.file_name}"',
            },
        )

    if not os.path.exists(read_path):
        raise HTTPException(status_code=404, detail="Resume file not found.")

    return FileResponse(
        path=read_path,
        media_type=resume.mime_type or "application/octet-stream",
        filename=resume.file_name,
    )