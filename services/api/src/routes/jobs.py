"""
Jobs API routes.

Thin HTTP endpoints for searching and listing normalized job records.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.deps.auth import get_current_user
from src.domain.jobs.repository import JobRepository
from src.domain.jobs.schemas import JobRead, JobSearchRequest
from src.domain.jobs.service import JobService
from src.infrastructure.db.session import get_db

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/search", response_model=list[JobRead])
def search_jobs(
    payload: JobSearchRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search jobs from a supported source and store normalized results.
    """
    repository = JobRepository(db)
    service = JobService(repository)

    try:
        return service.search_and_store_jobs(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=list[JobRead])
def list_jobs(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return stored normalized jobs.
    """
    repository = JobRepository(db)
    service = JobService(repository)
    return service.list_jobs()