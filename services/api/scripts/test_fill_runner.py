"""Test pipeline runner - authenticates, creates applications, then runs the pipeline orchestrator.

Usage:
    python scripts/test_fill_runner.py [--clear-screenshots] [--clear-applications] [--storage {local,s3}]

Flags:
    --clear-screenshots   Delete all files in uploads/automation/ before running.
    --clear-applications  Delete all existing applications for the authenticated user before running.
    --storage local       Use the local resume file path from RESUME_PATH (default).
    --storage s3          Fetch the latest S3 resume path from GET /resumes.
    --enable-submit       After a successful fill, auto-authorize when needed,
                          then call POST /applications/{id}/submit. Disabled by default.

Flow:
    1. For each job URL, create or fetch a job record
    2. Create an application for that job
    3. Run POST /applications/{id}/run to trigger the pipeline orchestrator
    4. Track Application.status progression through pipeline stages
    5. Save timestamped JSON results per job

Each run saves a timestamped JSON file per job under:
    scripts/test_results/<RUN_TIMESTAMP>/<slug>.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import threading
import time
from datetime import datetime
from uuid import UUID

import requests
from constants import JOBS, RESUME_PATH
# ─── CONFIG ──────────────────────────────────────────────────────────────────

BASE_URL = "http://localhost:8000"
USERNAME = "adekunledev97@gmail.com"
PASSWORD = "password"
PIPELINE_POLL_TIMEOUT_SECONDS = int(os.getenv("PIPELINE_POLL_TIMEOUT_SECONDS", "900"))

SCREENSHOTS_DIR = os.path.join(
    os.path.dirname(__file__),
    "../uploads/automation",
)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "test_results")
TERMINAL_APPLICATION_STATUSES = {"filled", "awaiting_submission", "submitted", "failed"}


# ─── RESULT EXPORTER ─────────────────────────────────────────────────────────

def _slug(label: str) -> str:
    """Convert a job label to a filesystem-safe slug."""
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def save_result(
    run_dir: str, job: dict, application_id: str, status_progression: list, elapsed: float, error: str | None = None
) -> str:
    """Write the pipeline run result plus metadata to a JSON file.

    Returns the path of the written file.
    """
    os.makedirs(run_dir, exist_ok=True)

    export = {
        "meta": {
            "label": job["label"],
            "application_url": job["application_url"],
            "application_id": application_id,
            "timestamp": datetime.now().isoformat(),
            "elapsed_s": elapsed,
        },
        "error": error,
        "status_progression": status_progression,
        "final_status": status_progression[-1] if status_progression else None,
    }

    filename = f"{_slug(job['label'])}.json"
    path = os.path.join(run_dir, filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(export, fh, indent=2, ensure_ascii=False)

    return path


def _save_pipeline_error(run_dir: str, job: dict, application_id: str, error_msg: str) -> None:
    """Write a minimal error record when the pipeline run fails."""
    os.makedirs(run_dir, exist_ok=True)
    export = {
        "meta": {
            "label": job["label"],
            "application_url": job["application_url"],
            "application_id": application_id,
            "timestamp": datetime.now().isoformat(),
        },
        "error": error_msg,
    }
    filename = f"{_slug(job['label'])}.json"
    path = os.path.join(run_dir, filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(export, fh, indent=2, ensure_ascii=False)




def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def section(title: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def log(msg: str) -> None:
    print(f"[{ts()}] {msg}")


def _loading_indicator(stop_event: threading.Event, label: str) -> None:
    """Render a simple terminal spinner until the stop event is set."""
    frames = ["|", "/", "-", "\\"]
    index = 0
    while not stop_event.is_set():
        print(f"\r[{ts()}] {label} {frames[index % len(frames)]}", end="", flush=True)
        index += 1
        stop_event.wait(0.2)

    print("\r" + " " * 120 + "\r", end="", flush=True)


def _start_loading_indicator(label: str) -> tuple[threading.Event, threading.Thread]:
    """Start the loading indicator thread for a long-running request."""
    stop_event = threading.Event()
    worker = threading.Thread(
        target=_loading_indicator,
        args=(stop_event, label),
        daemon=True,
    )
    worker.start()
    return stop_event, worker


def _stop_loading_indicator(stop_event: threading.Event, worker: threading.Thread) -> None:
    """Stop and clean up the loading indicator thread."""
    stop_event.set()
    worker.join(timeout=1)


def _run_timed(label: str, func):
    """Run a callable with spinner + elapsed timing and return (result, elapsed_seconds)."""
    indicator = _start_loading_indicator(label)
    start = time.time()
    try:
        result = func()
    finally:
        _stop_loading_indicator(*indicator)
    elapsed = round(time.time() - start, 1)
    log(f"✓ {label} complete ({elapsed}s)")
    return result, elapsed


# ─── SCREENSHOT CLEANER ─────────────────────────────────────────────────────

def clear_screenshots() -> None:
    target = os.path.realpath(SCREENSHOTS_DIR)
    if not os.path.isdir(target):
        log(f"⚠️  Screenshots dir not found, skipping: {target}")
        return

    files = glob.glob(os.path.join(target, "**", "*.png"), recursive=True)
    files += glob.glob(os.path.join(target, "**", "*.jpg"), recursive=True)

    if not files:
        log(f"📂 Screenshots dir already empty: {target}")
        return

    for f in files:
        try:
            os.remove(f)
        except Exception as exc:
            log(f"  ⚠️  Could not delete {f}: {exc}")

    log(f"🗑️  Cleared {len(files)} screenshot(s) from {target}")


# ─── AUTH ────────────────────────────────────────────────────────────────────

def authenticate() -> str:
    log(f"Authenticating as {USERNAME} ...")
    resp, _ = _run_timed(
        "Authenticating",
        lambda: requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": USERNAME, "password": PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        ),
    )
    if resp.status_code != 200:
        log(f"❌ Login failed — HTTP {resp.status_code}")
        log(f"   Response: {resp.text}")
        sys.exit(1)

    body = resp.json()
    token = body.get("access_token")
    if not token:
        log(f"❌ No access_token in login response: {body}")
        sys.exit(1)

    log(f"✅ Authenticated — token acquired ({token[:20]}...)")
    return token


def fetch_resume_path(token: str, storage_mode: str) -> str:
    """Fetch the most recent resume path from the API for a storage mode."""
    log(f"Fetching resume from API for storage={storage_mode}...")
    resp, _ = _run_timed(
        "Fetching resumes",
        lambda: requests.get(
            f"{BASE_URL}/resumes",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        ),
    )
    if resp.status_code != 200:
        log(f"❌ GET /resumes failed — HTTP {resp.status_code}: {resp.text}")
        sys.exit(1)

    resumes = resp.json()
    if not resumes:
        log("❌ No resumes found for this user. Upload a resume first.")
        sys.exit(1)

    # Sort by created_at descending so we pick the newest matching resume.
    resumes = sorted(
        resumes,
        key=lambda item: item.get("created_at") or "",
        reverse=True,
    )

    if storage_mode == "s3":
        matching = [r for r in resumes if str(r.get("file_path", "")).startswith("s3://")]
    else:
        matching = [r for r in resumes if not str(r.get("file_path", "")).startswith("s3://")]

    if not matching:
        log(
            "❌ No matching resume path found for requested storage mode. "
            f"storage={storage_mode}."
        )
        log("   Upload a new resume while the API is configured for that backend, then retry.")
        sys.exit(1)

    resume = matching[0]
    path = str(resume.get("file_path") or "")
    if not path:
        log("❌ Selected resume has an empty file_path.")
        sys.exit(1)

    log(f"✅ Using resume: id={resume.get('id')}  path={path}")
    return path


def clear_applications_for_current_user(token: str) -> None:
    """Delete all existing applications for the authenticated user."""
    api_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if api_root not in sys.path:
        sys.path.insert(0, api_root)

    from src.domain.applications.models import Application
    from src.infrastructure.db.session import SessionLocal

    log("Resolving current authenticated user for application cleanup...")
    session_resp, _ = _run_timed(
        "Resolving auth session",
        lambda: requests.get(
            f"{BASE_URL}/auth/session",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        ),
    )
    if session_resp.status_code != 200:
        log(
            "❌ Could not resolve auth session for --clear-applications "
            f"(HTTP {session_resp.status_code}: {session_resp.text})"
        )
        sys.exit(1)

    user_id = session_resp.json().get("id")
    if not user_id:
        log("❌ Session payload did not include user id; cannot clear applications.")
        sys.exit(1)

    log(f"--clear-applications flag set — deleting existing applications for user {user_id}...")
    db = SessionLocal()
    try:
        deleted = (
            db.query(Application)
            .filter(Application.user_id == UUID(str(user_id)))
            .delete(synchronize_session=False)
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        log(f"❌ Failed to clear applications: {exc}")
        sys.exit(1)
    finally:
        db.close()

    log(f"🗑️  Cleared {deleted} application(s) for current user")


# ─── JOB & APPLICATION MANAGEMENT ────────────────────────────────────────────

def get_or_create_job(token: str, application_url: str) -> str:
    """Get or create a job by application_url. Returns the job ID."""
    log(f"Looking for job matching {application_url[:60]}...")
    
    # Try to find existing jobs
    resp, _ = _run_timed(
        "Loading jobs",
        lambda: requests.get(
            f"{BASE_URL}/jobs",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        ),
    )
    
    if resp.status_code == 200:
        payload = resp.json()

        # /jobs currently returns a paginated envelope (FeedPage):
        # {"total": ..., "jobs": [...]}.
        # Keep backward compatibility in case an older endpoint returns a raw list.
        if isinstance(payload, dict):
            jobs = payload.get("jobs") or []
        elif isinstance(payload, list):
            jobs = payload
        else:
            jobs = []

        for job in jobs:
            if not isinstance(job, dict):
                continue
            if job.get("apply_url") == application_url:
                job_id = job.get("id")
                log(f"  ✓ Found existing job: {job_id}")
                return job_id
    
    # Create a new job record
    log(f"  Creating new job record...")
    
    resp, _ = _run_timed(
        "Creating job",
        lambda: requests.post(
            f"{BASE_URL}/jobs",
            json={"apply_url": application_url},
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        ),
    )
    
    if resp.status_code not in (200, 201):
        log(f"  ❌ Job creation failed — HTTP {resp.status_code}")
        log(f"     Response: {resp.text[:300]}")
        raise ValueError(f"Could not create job for {application_url}")
    
    job_id = resp.json().get("id")
    log(f"  ✓ Created job: {job_id}")
    return job_id


def create_application(token: str, job_id: str) -> str:
    """Create an application for the given job. Returns the application ID."""
    log(f"Creating application for job {job_id}...")
    
    resp, _ = _run_timed(
        "Creating application",
        lambda: requests.post(
            f"{BASE_URL}/applications",
            json={"job_id": job_id},
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        ),
    )
    
    if resp.status_code not in (200, 201):
        log(f"  ❌ Application creation failed — HTTP {resp.status_code}: {resp.text}")
        raise ValueError(f"Could not create application for job {job_id}")
    
    app_id = resp.json().get("id")
    log(f"  ✓ Created application: {app_id}")
    return app_id


def get_application(token: str, app_id: str, timed: bool = False) -> dict:
    """Fetch current application record."""
    request = lambda: requests.get(
        f"{BASE_URL}/applications/{app_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    if timed:
        resp, _ = _run_timed(f"Fetching application {app_id}", request)
    else:
        resp = request()
    
    if resp.status_code != 200:
        log(f"  ❌ Could not fetch application — HTTP {resp.status_code}")
        raise ValueError(f"Could not fetch application {app_id}")
    
    return resp.json()


def authorize_application(token: str, app_id: str) -> dict:
    """Explicitly authorize an application for submission."""
    log(f"Authorizing application {app_id} for submission...")

    resp, _ = _run_timed(
        "Authorizing application",
        lambda: requests.post(
            f"{BASE_URL}/applications/{app_id}/authorize",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        ),
    )

    if resp.status_code != 200:
        log(f"  ❌ Authorization failed — HTTP {resp.status_code}: {resp.text}")
        raise ValueError(f"Could not authorize application {app_id}: {resp.text}")

    log(f"  ✓ Authorized application: {app_id}")
    return resp.json()


# ─── PIPELINE RUNNER ─────────────────────────────────────────────────────────

def run_pipeline(token: str, job: dict, run_dir: str, resume_path: str | None = None, enable_submit: bool = False) -> None:
    """Run the pipeline orchestrator for a job and track status progression."""
    label = job["label"]
    section(f"[{label}]  {job['application_url']}")
    
    status_progression = []
    application_id = None
    error_msg = None
    pipeline_start = time.time()

    try:
        # Step 1: Get or create job
        job_id = get_or_create_job(token, job["application_url"])

        # Step 2: Create application
        application_id = create_application(token, job_id)

        # Step 3: Run pipeline orchestrator
        log(f"Running pipeline for application {application_id}...")
        log(f"POST {BASE_URL}/applications/{application_id}/run")

        resp, _ = _run_timed(
            "Dispatching pipeline",
            lambda: requests.post(
                f"{BASE_URL}/applications/{application_id}/run",
                headers={"Authorization": f"Bearer {token}"},
                timeout=300,  # pipeline can take longer
            ),
        )

        if resp.status_code != 200:
            log(f"❌ Pipeline failed — HTTP {resp.status_code}")
            log(f"   Response: {resp.text}")
            error_msg = f"HTTP {resp.status_code}: {resp.text}"
        else:
            app_data = resp.json()
            final_status = app_data.get("status")
            task_id = app_data.get("task_id")

            if task_id:
                log(f"✅ Pipeline dispatched — task_id: {task_id}")
                log("Polling application status until terminal state...")

                last_status = None
                poll_deadline = time.time() + PIPELINE_POLL_TIMEOUT_SECONDS
                poll_indicator = _start_loading_indicator("Polling status")
                try:
                    while time.time() < poll_deadline:
                        current_app = get_application(token, application_id)
                        current_status = current_app.get("status")

                        if current_status != last_status:
                            log(f"  status -> {current_status}")
                            status_progression.append(current_status)
                            last_status = current_status

                        if current_status in TERMINAL_APPLICATION_STATUSES:
                            app_data = current_app
                            final_status = current_status
                            break

                        time.sleep(2)
                finally:
                    _stop_loading_indicator(*poll_indicator)

                if final_status not in TERMINAL_APPLICATION_STATUSES:
                    error_msg = (
                        "Pipeline polling timed out before reaching a terminal status "
                        f"(timeout={PIPELINE_POLL_TIMEOUT_SECONDS}s)"
                    )
                    log(f"❌ {error_msg}")
                    app_data = get_application(token, application_id)
                    final_status = app_data.get("status")
            else:
                log(f"✅ Pipeline complete — status: {final_status}")
                status_progression.append(final_status)

            # Optionally run the submit step
            if enable_submit and final_status in ("filled", "awaiting_submission"):
                if app_data.get("manual_review_required") and not app_data.get(
                    "is_authorized_to_submit"
                ):
                    log("--enable-submit set — manual review gate is active, authorizing first...")
                    app_data = authorize_application(token, application_id)

                log(f"--enable-submit set — calling POST /applications/{application_id}/submit ...")
                submit_resp, _ = _run_timed(
                    "Submitting application",
                    lambda: requests.post(
                        f"{BASE_URL}/applications/{application_id}/submit",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=300,
                    ),
                )
                if submit_resp.status_code != 200:
                    log(f"❌ Submit failed — HTTP {submit_resp.status_code}: {submit_resp.text}")
                    error_msg = f"Submit HTTP {submit_resp.status_code}: {submit_resp.text}"
                else:
                    app_data = submit_resp.json()
                    final_status = app_data.get("status")
                    log(f"✅ Submit complete — status: {final_status}")
                    status_progression.append(final_status)
            elif enable_submit:
                log(f"⚠️  --enable-submit set but status '{final_status}' is not eligible for submission; skipping.")

            # Fetch final application state to show results
            log(f"\n── FINAL APPLICATION STATE ──────────────────────")
            log(f"  Status          : {final_status}")
            log(f"  Manual Review   : {app_data.get('manual_review_required')}")
            log(f"  Authorized      : {app_data.get('is_authorized_to_submit')}")
            log(f"  Failed Reason   : {app_data.get('failure_reason')}")

    except ValueError as exc:
        error_msg = str(exc)
        log(f"❌ Error: {error_msg}")
    except requests.exceptions.Timeout:
        error_msg = "Request timed out after 300 s"
        log(f"❌ {error_msg}")
    except requests.exceptions.ConnectionError as exc:
        error_msg = f"Connection error: {exc}"
        log(f"❌ {error_msg}")
    except Exception as exc:
        error_msg = f"Unexpected error: {exc}"
        log(f"❌ {error_msg}")

    # Save result to disk
    if not application_id:
        # If we failed to create an application, save a minimal error record
        run_dir_resolved = run_dir
        os.makedirs(run_dir_resolved, exist_ok=True)
        export = {
            "meta": {
                "label": job["label"],
                "application_url": job["application_url"],
                "timestamp": datetime.now().isoformat(),
            },
            "error": error_msg,
        }
        filename = f"{_slug(job['label'])}.json"
        path = os.path.join(run_dir_resolved, filename)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(export, fh, indent=2, ensure_ascii=False)
        log(f"\n  💾 Error record saved → {path}")
    else:
        elapsed = round(time.time() - pipeline_start, 1)
        result_path = save_result(run_dir, job, application_id, status_progression, elapsed, error=error_msg)
        log(f"  Total elapsed   : {elapsed}s")
        log(f"\n  💾 Result saved → {result_path}")


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Artemis pipeline orchestrator runner")
    parser.add_argument(
        "--clear-screenshots",
        action="store_true",
        help="Delete all screenshots in uploads/automation/ before running.",
    )
    parser.add_argument(
        "--storage",
        choices=["local", "s3"],
        default="local",
        help="Resume storage: 'local' uses RESUME_PATH constant; 's3' fetches the path from GET /resumes.",
    )
    parser.add_argument(
        "--clear-applications",
        action="store_true",
        help="Delete all existing applications for the authenticated user before running.",
    )
    parser.add_argument(
        "--enable-submit",
        action="store_true",
        default=False,
        help=(
            "After a successful fill, auto-authorize when required and then call "
            "POST /applications/{id}/submit. Disabled by default."
        ),
    )
    args = parser.parse_args()

    section("Artemis pipeline orchestrator runner")
    log(f"Base URL : {BASE_URL}")
    log(f"Jobs     : {len(JOBS)}")
    log(f"Storage  : {args.storage}")
    log(f"Submit   : {'enabled' if args.enable_submit else 'disabled (use --enable-submit to turn on)'}")

    if args.clear_screenshots:
        log("--clear-screenshots flag set — clearing screenshots...")
        clear_screenshots()

    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(RESULTS_DIR, run_ts)
    os.makedirs(run_dir, exist_ok=True)
    log(f"Results  : {run_dir}")

    token = authenticate()

    if args.clear_applications:
        clear_applications_for_current_user(token)

    if args.storage == "s3":
        resume_override = fetch_resume_path(token, "s3")
    else:
        # Keep local mode deterministic via the script constant.
        resume_override = RESUME_PATH
        log(f"Resume   : {resume_override}")

    for i, job in enumerate(JOBS, start=1):
        log(f"\n▶ Job {i}/{len(JOBS)}: {job['label']}")
        run_pipeline(token, job, run_dir, resume_path=resume_override, enable_submit=args.enable_submit)
        if i < len(JOBS):
            log("Waiting 3 s before next job...")
            time.sleep(3)

    section("All done")


if __name__ == "__main__":
    main()
