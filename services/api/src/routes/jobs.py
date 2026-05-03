"""
Jobs API routes.

Thin HTTP endpoints for searching and listing normalized job records.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.deps.auth import get_current_user
from src.domain.jobs.models import Job
from src.domain.jobs.repository import JobPreferencesRepository, JobRepository
from src.domain.jobs.schemas import (
    JobPreferencesSchema,
    JobPreferencesUpsertRequest,
    JobRead,
    JobSearchRequest,
)
from src.domain.jobs.service import JobService
from src.infrastructure.db.session import get_db

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobCreateRequest(BaseModel):
    apply_url: str


def _build_job_service(db: Session) -> JobService:
    return JobService(
        repository=JobRepository(db),
        preferences_repository=JobPreferencesRepository(db),
    )


@router.post("", response_model=JobRead)
def create_job(
    payload: JobCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a minimal job record for testing/pipeline purposes.
    Extracts company name from URL when possible.
    """
    # Check if job with this URL already exists
    existing = db.query(Job).filter(Job.apply_url == payload.apply_url).first()
    if existing:
        return JobRead.model_validate(existing)

    # Extract source and company from URL
    apply_url = payload.apply_url
    if "greenhouse" in apply_url:
        source = "greenhouse"
        company_name = "Greenhouse Company"
    elif "lever.co" in apply_url:
        source = "lever"
        company_name = "Lever Company"
    elif "ashby" in apply_url:
        source = "ashby"
        company_name = "Ashby Company"
    else:
        source = "manual"
        company_name = "Test Company"

    # Extract job ID from URL
    source_job_id = apply_url.split("/")[-1].split("?")[0] or "test-job"

    # Create job
    job = Job(
        source=source,
        source_job_id=source_job_id,
        title="Test Position",
        company_name=company_name,
        apply_url=apply_url,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return JobRead.model_validate(job)


@router.post("/search", response_model=list[JobRead])
def search_jobs(
    payload: JobSearchRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search jobs from a supported source and store normalized results.
    """
    service = _build_job_service(db)

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
    service = _build_job_service(db)
    return service.list_jobs()


@router.get("/preferences", response_model=JobPreferencesSchema)
def get_job_preferences(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_job_service(db)
    return service.get_preferences_for_user(current_user.id)


@router.put("/preferences", response_model=JobPreferencesSchema)
def upsert_job_preferences(
    payload: JobPreferencesUpsertRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_job_service(db)
    return service.upsert_preferences_for_user(current_user.id, payload)