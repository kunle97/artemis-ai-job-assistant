"""
Jobs API routes.

Thin HTTP endpoints for searching and listing normalized job records.
"""

from datetime import UTC, datetime
from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from fastapi import Query

from src.deps.auth import get_current_user
from src.domain.applications.repository import ApplicationRepository
from src.domain.profile.repository import CandidateProfileRepository
from src.domain.jobs.feed_service import JobFeedService
from src.domain.jobs.discovery_service import JobSourceDiscoveryService, build_hosted_board_url, parse_csv_urls
from src.domain.jobs.models import Job
from src.domain.jobs.models import JobFeedStatus
from src.domain.jobs.repository import JobPreferencesRepository, JobRepository, JobSourceDiscoveryRepository, JobSourceRepository, JobUserFeedRepository
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
    JobSourceDiscoveryPromoteRequest,
    JobSourceDiscoveryPromoteResponse,
    JobSourceDiscoveryRequest,
    JobSourceDiscoveryResponse,
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


def _build_job_source_discovery_service(db: Session) -> JobSourceDiscoveryService:
    return JobSourceDiscoveryService(
        repository=JobSourceDiscoveryRepository(db),
    )


def _build_feed_job_reads(db: Session, user_id, jobs: list[Job]) -> list[FeedJobRead]:
    if not jobs:
        return []

    application_repository = ApplicationRepository(db)
    profile_repository = CandidateProfileRepository(db)
    score_repository = ApplicationScoreRepository(db)
    feed_repository = JobUserFeedRepository(db)
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
    job_ids = [job.id for job in jobs]
    feed_statuses_by_job_id = feed_repository.get_statuses_for_user_and_job_ids(
        user_id=user_id,
        job_ids=job_ids,
    )

    feed_jobs: list[FeedJobRead] = []
    for job in jobs:
        application = applications_by_job_id.get(job.id)
        score = scores_by_application_id.get(application.id) if application else None
        preview_score = (
            score_job_fit_preview(job, profile)
            if score is None
            else {
                "global_score": None,
                "recommendation": None,
                "confidence": "low",
            }
        )

        # Legacy rows can have null timestamps; coerce before strict schema validation.
        payload = {
            "id": job.id,
            "source": job.source,
            "source_job_id": job.source_job_id,
            "title": job.title,
            "company_name": job.company_name,
            "location": job.location,
            "workplace_type": job.workplace_type,
            "description": job.description,
            "apply_url": job.apply_url,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "currency": job.currency,
            "is_active": job.is_active,
            "created_at": job.created_at or datetime.min.replace(tzinfo=UTC),
            "updated_at": job.updated_at or datetime.min.replace(tzinfo=UTC),
        }
        payload.update(
            application_id=application.id if application else None,
            fit_score=score.global_score if score else preview_score["global_score"],
            fit_recommendation=score.recommendation if score else preview_score["recommendation"],
            fit_score_confidence="high" if score else preview_score["confidence"],
            feed_status=feed_statuses_by_job_id.get(job.id),
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


@router.post("/discovery/crawl", response_model=JobSourceDiscoveryResponse)
def crawl_job_sources(
    payload: JobSourceDiscoveryRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Discover ATS source candidates from hosted URLs and career redirects."""
    _ = current_user
    service = _build_job_source_discovery_service(db)
    run_id, candidates, provider_counts = service.discover(
        hosted_urls=payload.hosted_urls,
        career_urls=payload.career_urls,
    )
    return JobSourceDiscoveryResponse(
        run_id=run_id,
        total_candidates=len(candidates),
        provider_counts=provider_counts,
        candidates=candidates,
    )


@router.post("/discovery/promote", response_model=JobSourceDiscoveryPromoteResponse)
def promote_job_source_candidates(
    payload: JobSourceDiscoveryPromoteRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Promote discovery candidates from a run into persistent job source mappings."""
    _ = current_user
    discovery_service = _build_job_source_discovery_service(db)
    source_repository = JobSourceRepository(db)
    promoted_sources, selected_candidates, skipped_count = discovery_service.promote_candidates(
        source_repository=source_repository,
        run_id=payload.run_id,
        candidate_ids=payload.candidate_ids,
        is_active=payload.is_active,
    )
    return JobSourceDiscoveryPromoteResponse(
        run_id=payload.run_id,
        selected_candidates=selected_candidates,
        promoted_count=len(promoted_sources),
        skipped_count=skipped_count,
        promoted_sources=promoted_sources,
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
    preferences_repository = JobPreferencesRepository(db)
    source_repository = JobSourceRepository(db)
    preferences = preferences_repository.get_or_create_by_user_id(current_user.id)
    enabled_sources = set(preferences.enabled_sources or [])

    discovery_hosted_urls: list[str] = []
    if enabled_sources:
        for source_row in source_repository.list_active():
            if source_row.source not in enabled_sources:
                continue
            hosted_url = build_hosted_board_url(source=source_row.source, board_token=source_row.board_token)
            if hosted_url:
                discovery_hosted_urls.append(hosted_url)

    discovery_hosted_urls.extend(parse_csv_urls(settings.job_discovery_seed_hosted_urls))
    discovery_career_urls = parse_csv_urls(settings.job_discovery_seed_career_urls)
    discovery_hosted_urls = list(dict.fromkeys(discovery_hosted_urls))
    discovery_career_urls = list(dict.fromkeys(discovery_career_urls))

    discovery_service = _build_job_source_discovery_service(db)
    discovery_summary = discovery_service.discover_and_promote(
        source_repository=source_repository,
        hosted_urls=discovery_hosted_urls,
        career_urls=discovery_career_urls,
        is_active=True,
    )

    feed_service = JobFeedService(user_id=current_user.id, db=db)
    new_jobs = feed_service.scan()
    return FeedScanResponse(
        new_jobs_found=len(new_jobs),
        discovery_run_id=discovery_summary["run_id"],
        discovery_candidates_found=discovery_summary["candidates_found"],
        discovery_promoted_count=discovery_summary["promoted_count"],
        discovery_skipped_count=discovery_summary["skipped_count"],
    )


@router.get("/feed", response_model=FeedPage)
def get_job_feed(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    query: str | None = Query(default=None),
    sort: Literal["newest", "salary_high", "salary_low", "fit_high"] = Query(default="newest"),
    sources: str | None = Query(default=None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return a paginated job feed for the current user.

    Filters are applied at read time against the user's current preferences:
    target_titles, positive_keywords, negative_keywords, remote_only, salary_min.
    Optional `sources` query param (comma-separated) restricts results to the given ATS platforms.
    """
    source_filter = {s.strip().lower() for s in (sources or "").split(",") if s.strip()}
    service = JobFeedService(user_id=current_user.id, db=db)
    if sort == "fit_high":
        all_jobs, _ = service.get_feed(skip=0, limit=None, query=query, sort="newest", sources=source_filter)
        all_feed_jobs = _build_feed_job_reads(db=db, user_id=current_user.id, jobs=all_jobs)
        all_feed_jobs.sort(
            key=lambda job: (
                job.fit_score if job.fit_score is not None else -1,
                job.created_at or datetime.min,
            ),
            reverse=True,
        )
        total = len(all_feed_jobs)
        page_jobs = all_feed_jobs[skip : skip + limit]
    else:
        jobs, total = service.get_feed(skip=skip, limit=limit, query=query, sort=sort, sources=source_filter)
        page_jobs = _build_feed_job_reads(db=db, user_id=current_user.id, jobs=jobs)

    # Preserve NEW status in this response, then transition delivered NEW jobs to SEEN.
    service.mark_jobs_as_seen([job.id for job in page_jobs])

    next_offset = skip + limit
    has_next = next_offset < total
    return FeedPage(
        total=total,
        skip=skip,
        limit=limit,
        has_next=has_next,
        prev_url=_prev_url(request, skip, limit),
        next_url=_next_url(request, next_offset, limit) if has_next else None,
        jobs=page_jobs,
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


@router.get("/{job_id}", response_model=FeedJobRead)
def get_job_by_id(
    job_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a single job record by ID, enriched with user-specific scoring data."""
    repository = JobRepository(db)
    job = repository.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    feed_jobs = _build_feed_job_reads(
        db=db,
        user_id=current_user.id,
        jobs=[job],
    )
    return feed_jobs[0]