"""
Resume API routes.

Thin HTTP endpoints for uploading and listing resumes.
Business logic stays in the resume service layer.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_db
from app.domains.resume.repository import ResumeRepository
from app.domains.resume.schemas import ResumeRead
from app.domains.resume.service import ResumeService
from app.domains.resume.parser import ResumeParser
from app.domains.profile.repository import CandidateProfileRepository
from app.integrations.storage.local_storage import LocalStorageService

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeRead)
def upload_resume(
    user_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    repository = ResumeRepository(db)
    profile_repository = CandidateProfileRepository(db)
    storage_service = LocalStorageService()
    parser = ResumeParser()

    service = ResumeService(
        repository=repository,
        storage_service=storage_service,
        parser=parser,
        profile_repository=profile_repository,
    )

    try:
        return service.upload_resume(user_id=user_id, upload_file=file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{user_id}", response_model=list[ResumeRead])
def list_resumes(user_id: UUID, db: Session = Depends(get_db)):
    repository = ResumeRepository(db)
    profile_repository = CandidateProfileRepository(db)
    storage_service = LocalStorageService()
    parser = ResumeParser()

    service = ResumeService(
        repository=repository,
        storage_service=storage_service,
        parser=parser,
        profile_repository=profile_repository,
    )

    return service.list_resumes(user_id=user_id)