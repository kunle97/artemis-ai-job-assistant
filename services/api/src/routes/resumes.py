"""
Resume API routes.

Thin HTTP endpoints for uploading and listing resumes for the authenticated user.
Business logic stays in the resume service layer.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.deps.auth import get_current_user
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.resume.parser import ResumeParser
from src.domain.resume.repository import ResumeRepository
from src.domain.resume.schemas import ResumeRead
from src.domain.resume.service import ResumeService
from src.infrastructure.db.session import get_db
from src.integrations.storage.local_storage import LocalStorageService

router = APIRouter(prefix="/resumes", tags=["resumes"])


def _build_resume_service(db: Session) -> ResumeService:
    """
    Build the resume service and its dependencies.
    """
    repository = ResumeRepository(db)
    profile_repository = CandidateProfileRepository(db)
    storage_service = LocalStorageService()
    parser = ResumeParser()

    return ResumeService(
        repository=repository,
        storage_service=storage_service,
        parser=parser,
        profile_repository=profile_repository,
    )


@router.post("/upload", response_model=ResumeRead)
def upload_resume(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a resume for the authenticated user.
    """
    service = _build_resume_service(db)

    try:
        return service.upload_resume(user_id=current_user.id, upload_file=file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=list[ResumeRead])
def list_resumes(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return resumes for the authenticated user.
    """
    service = _build_resume_service(db)
    return service.list_resumes(current_user.id)