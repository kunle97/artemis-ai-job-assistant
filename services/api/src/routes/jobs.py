"""
Jobs API routes.

Thin HTTP endpoints for searching and listing normalized job records.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from fastapi import Query

from src.deps.auth import get_current_user
from src.domain.applications.repository import ApplicationRepository
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.jobs.feed_service import JobFeedService
from src.domain.jobs.models import Job
from src.domain.jobs.models import JobFeedStatus
from src.domain.jobs.repository import JobPreferencesRepository, JobRepository, JobSourceRepository
from src.domain.jobs.scoring.repository import ApplicationScoreRepository
from src.domain.jobs.scoring.service import score_job_fit_preview
from src.domain.jobs.schemas import (
    FeedJobRead,
    FeedPage,
    FeedScanResponse,
    JobFeedStatusUpdateRequest,
    JobFeedStatusUpdateResponse,
    JobPreferencesSchema,
    JobPreferencesUpsertRequest,
    JobRead,
    JobSearchRequest,
    JobSourceRead,
)
from src.domain.jobs.service import JobService
from src.infrastructure.db.session import get_db
from src.core.config import settings

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _next_url(request: Request, skip: int, limit: int) -> str:
    """Build an absolute next-page URL.

    Uses API_BASE_URL from config when set (needed behind a reverse proxy),
    otherwise falls back to the host reflected in the incoming request.
    """
    base = settings.api_base_url.rstrip("/") if settings.api_base_url else str(request.base_url).rstrip("/")
    path = request.url.path
    params = dict(request.query_params)
    params["skip"] = str(skip)
    params["limit"] = str(limit)
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{base}{path}?{query}"


def _prev_url(request: Request, skip: int, limit: int) -> str | None:
    """Build an absolute previous-page URL when a prior page exists."""
    if skip <= 0:
        return None

    previous_skip = max(skip - limit, 0)
    base = settings.api_base_url.rstrip("/") if settings.api_base_url else str(request.base_url).rstrip("/")
    path = request.url.path
    params = dict(request.query_params)
    params["skip"] = str(previous_skip)
    params["limit"] = str(limit)
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{base}{path}?{query}"


class JobCreateRequest(BaseModel):
    apply_url: str


def _build_job_service(db: Session) -> JobService:
    return JobService(
        repository=JobRepository(db),
        preferences_repository=JobPreferencesRepository(db),
        job_source_repository=JobSourceRepository(db),
    )


def _build_feed_job_reads(db: Session, user_id, jobs: list[Job]) -> list[FeedJobRead]:
    if not jobs:
        return []

    application_repository = ApplicationRepository(db)
    profile_repository = CandidateProfileRepository(db)
    score_repository = ApplicationScoreRepository(db)
    profile = profile_repository.get_by_user_id(user_id)

    applications = application_repository.list_by_user_and_job_ids(
        user_id=user_id,
        job_ids=[job.id for job in jobs],
    )
    applications_by_job_id = {application.job_id: application for application in applications}
    scores_by_application_id = {
        score.application_id: score
        for score in score_repository.list_by_application_ids([application.id for application in applications])
    }

    feed_jobs: list[FeedJobRead] = []
    for job in jobs:
        application = applications_by_job_id.get(job.id)
        score = scores_by_application_id.get(application.id) if application else None
        preview_score = score_job_fit_preview(job, profile) if score is None else None
        payload = JobRead.model_validate(job).model_dump(mode="python")
        payload.update(
            application_id=application.id if application else None,
            fit_score=score.global_score if score else preview_score["global_score"],
            fit_recommendation=score.recommendation if score else preview_score["recommendation"],
        )
        feed_jobs.append(FeedJobRead.model_validate(payload))

    return feed_jobs


@router.get("/sources", response_model=list[JobSourceRead])
def list_job_sources(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return active job source mappings configured in the database."""
    _ = current_user
    repository = JobSourceRepository(db)
    return repository.list_active()


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


@router.post("/search", response_model=FeedPage)
def search_jobs(
    request: Request,
    payload: JobSearchRequest,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search jobs from a supported source, store normalized results, and return a paginated page.
    """
    service = _build_job_service(db)

    try:
        jobs, total = service.search_and_store_jobs(
            payload,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    next_offset = skip + limit
    has_next = next_offset < total
    return FeedPage(
        total=total,
        skip=skip,
        limit=limit,
        has_next=has_next,
        prev_url=_prev_url(request, skip, limit),
        next_url=_next_url(request, next_offset, limit) if has_next else None,
        jobs=_build_feed_job_reads(db=db, user_id=current_user.id, jobs=jobs),
    )


@router.get("", response_model=FeedPage)
def list_jobs(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return paginated stored normalized jobs.
    """
    service = _build_job_service(db)
    jobs, total = service.list_jobs_paginated(skip=skip, limit=limit)
    next_offset = skip + limit
    has_next = next_offset < total
    return FeedPage(
        total=total,
        skip=skip,
        limit=limit,
        has_next=has_next,
        prev_url=_prev_url(request, skip, limit),
        next_url=_next_url(request, next_offset, limit) if has_next else None,
        jobs=_build_feed_job_reads(db=db, user_id=current_user.id, jobs=jobs),
    )


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


@router.post("/feed/scan", response_model=FeedScanResponse)
def scan_job_feed(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Trigger an on-demand job feed scan for the current user.

    Runs JobFeedService against all enabled ATS boards, persists new jobs,
    and returns the count of newly ingested jobs. Call GET /jobs/feed to
    display results.
    """
    service = JobFeedService(user_id=current_user.id, db=db)
    new_jobs = service.scan()
    return FeedScanResponse(new_jobs_found=len(new_jobs))


@router.get("/feed", response_model=FeedPage)
def get_job_feed(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    query: str | None = Query(default=None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return a paginated job feed for the current user.

    Filters are applied at read time against the user's current preferences:
    target_titles, positive_keywords, negative_keywords, remote_only, salary_min.
    """
    service = JobFeedService(user_id=current_user.id, db=db)
    jobs, total = service.get_feed(skip=skip, limit=limit, query=query)
    next_offset = skip + limit
    has_next = next_offset < total
    return FeedPage(
        total=total,
        skip=skip,
        limit=limit,
        has_next=has_next,
        prev_url=_prev_url(request, skip, limit),
        next_url=_next_url(request, next_offset, limit) if has_next else None,
        jobs=_build_feed_job_reads(db=db, user_id=current_user.id, jobs=jobs),
    )


@router.patch("/feed/{job_id}", response_model=JobFeedStatusUpdateResponse)
def update_job_feed_status(
    job_id: UUID,
    payload: JobFeedStatusUpdateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a per-user feed status for a job already linked into the user's feed.
    """
    if payload.status not in {JobFeedStatus.SAVED, JobFeedStatus.DISMISSED}:
        raise HTTPException(
            status_code=400,
            detail="Only saved or dismissed statuses can be set via this endpoint.",
        )

    service = JobFeedService(user_id=current_user.id, db=db)
    link = service.update_feed_status(job_id=job_id, status=payload.status)
    if link is None:
        raise HTTPException(status_code=404, detail="Job feed entry not found.")

    return JobFeedStatusUpdateResponse(job_id=link.job_id, status=link.status)