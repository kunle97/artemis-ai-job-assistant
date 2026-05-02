"""
Test fill runner — authenticates then runs /automation/test-fill for each job URL.

Usage:
    python scripts/test_fill_runner.py [--clear-screenshots] [--storage {local,s3}]

Flags:
    --clear-screenshots   Delete all files in uploads/automation/ before running.
    --storage local       Use the local resume file path from RESUME_PATH (default).
    --storage s3          Fetch the latest S3 resume path from GET /resumes.

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

import requests
from test_application_urls import JOBS, RESUME_PATH
# ─── CONFIG ──────────────────────────────────────────────────────────────────

BASE_URL = "http://localhost:8000"
USERNAME = "adekunledev97@gmail.com"
PASSWORD = "password"

SCREENSHOTS_DIR = os.path.join(
    os.path.dirname(__file__),
    "../services/api/uploads/automation",
)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "test_results")


# ─── RESULT EXPORTER ─────────────────────────────────────────────────────────

def _slug(label: str) -> str:
    """Convert a job label to a filesystem-safe slug."""
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def save_result(run_dir: str, job: dict, body: dict, elapsed: float) -> str:
    """Write the raw API response plus metadata to a JSON file.

    Returns the path of the written file.
    """
    os.makedirs(run_dir, exist_ok=True)

    inspect = body.get("inspect", {})
    fill = body.get("fill", {})
    fields = fill.get("fields", [])
    total = len(fields)
    filled_count = fill.get("filled_count", 0)

    export = {
        "meta": {
            "label": job["label"],
            "application_url": job["application_url"],
            "timestamp": datetime.now().isoformat(),
            "elapsed_s": elapsed,
        },
        "inspect": {
            "status": inspect.get("status"),
            "title": inspect.get("title"),
            "field_count": len(inspect.get("fields", [])),
            "notes": inspect.get("notes", []),
            "screenshot_path": inspect.get("screenshot_path"),
            "fields": inspect.get("fields", []),
        },
        "fill": {
            "filled_count": filled_count,
            "skipped_count": fill.get("skipped_count", 0),
            "total_fields": total,
            "fill_rate_pct": round(filled_count / total * 100, 1) if total else 0.0,
            "notes": fill.get("notes", []),
            "screenshot_path": fill.get("screenshot_path"),
            "fields": fields,
            "unresolved_fields": fill.get("unresolved_fields", []),
        },
    }

    filename = f"{_slug(job['label'])}.json"
    path = os.path.join(run_dir, filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(export, fh, indent=2, ensure_ascii=False)

    return path


def _save_error(run_dir: str, job: dict, error_type: str, detail: str | None) -> None:
    """Write a minimal error record when the API call fails."""
    os.makedirs(run_dir, exist_ok=True)
    export = {
        "meta": {
            "label": job["label"],
            "application_url": job["application_url"],
            "timestamp": datetime.now().isoformat(),
        },
        "error": error_type,
        "detail": detail,
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
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": USERNAME, "password": PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
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
    resp = requests.get(
        f"{BASE_URL}/resumes",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
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


# ─── FILL RUNNER ─────────────────────────────────────────────────────────────

def run_test_fill(token: str, job: dict, run_dir: str, resume_path: str | None = None) -> None:
    label = job["label"]
    section(f"[{label}]  {job['application_url']}")

    payload = {
        "application_url": job["application_url"],
        "resume_file_path": resume_path if resume_path is not None else job["resume_file_path"],
    }

    log(f"POST {BASE_URL}/automation/test-fill")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    # Spinner that prints progress dots until the request completes
    stop_spinner = threading.Event()

    def _spinner():
        symbols = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        idx = 0
        elapsed_s = 0
        while not stop_spinner.is_set():
            sym = symbols[idx % len(symbols)]
            print(f"\r[{ts()}] {sym}  Running fill... {elapsed_s}s elapsed", end="", flush=True)
            time.sleep(0.5)
            idx += 1
            elapsed_s += 1 if idx % 2 == 0 else 0
        print()  # newline after spinner ends

    spinner_thread = threading.Thread(target=_spinner, daemon=True)
    spinner_thread.start()

    start = time.time()
    try:
        resp = requests.post(
            f"{BASE_URL}/automation/test-fill",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=180,  # form fill can take a while
        )
    except requests.exceptions.Timeout:
        stop_spinner.set()
        log("❌ Request timed out after 180 s")
        _save_error(run_dir, job, "timeout", None)
        return
    except requests.exceptions.ConnectionError as exc:
        stop_spinner.set()
        log(f"❌ Connection error: {exc}")
        _save_error(run_dir, job, "connection_error", str(exc))
        return

    stop_spinner.set()
    elapsed = round(time.time() - start, 1)
    log(f"HTTP {resp.status_code}  ({elapsed} s)")

    if resp.status_code != 200:
        log(f"❌ Non-200 response body:\n{resp.text}")
        _save_error(run_dir, job, f"http_{resp.status_code}", resp.text)
        return

    try:
        body = resp.json()
    except Exception:
        log(f"❌ Could not parse JSON response:\n{resp.text}")
        _save_error(run_dir, job, "json_parse_error", resp.text)
        return

    # ── Inspect summary ──────────────────────────────────────────────────────
    inspect = body.get("inspect", {})
    log(f"\n── INSPECT ──────────────────────────────────────────")
    log(f"  Status  : {inspect.get('status')}")
    log(f"  Title   : {inspect.get('title')}")
    log(f"  Fields  : {len(inspect.get('fields', []))}")
    log(f"  Notes   : {inspect.get('notes')}")
    log(f"  Screenshot: {inspect.get('screenshot_path')}")

    # ── Fill summary ─────────────────────────────────────────────────────────
    fill = body.get("fill", {})
    total_fields = len(fill.get("fields", []))
    filled = fill.get("filled_count", 0)
    skipped = fill.get("skipped_count", 0)
    pct = round((filled / total_fields * 100), 1) if total_fields else 0.0

    log(f"\n── FILL ─────────────────────────────────────────────")
    log(f"  Filled  : {filled} / {total_fields}  ({pct}%)")
    log(f"  Skipped : {skipped}")
    log(f"  Notes   : {fill.get('notes')}")
    log(f"  Screenshot: {fill.get('screenshot_path')}")

    # ── Per-field table ───────────────────────────────────────────────────────
    fields = fill.get("fields", [])
    if fields:
        log(f"\n── FIELD RESULTS ─────────────────────────────────────")
        col_w = 45
        header = f"  {'Label':<{col_w}}  {'Role':<28}  {'Status':<32}  Resolved Value"
        log(header)
        log(f"  {'-' * (col_w)}  {'-' * 28}  {'-' * 32}  {'-' * 30}")
        for f in fields:
            label_str = (f.get("label") or "")[:col_w]
            role_str  = (f.get("classified_role") or "")[:28]
            status    = f.get("fill_status", "")
            value     = (f.get("resolved_value") or "")[:50]
            icon = "✅" if status == "filled" else ("⏭️ " if "skipped" in status else "❌")
            log(f"  {label_str:<{col_w}}  {role_str:<28}  {icon} {status:<30}  {value}")

    # ── Unresolved fields ─────────────────────────────────────────────────────
    unresolved = fill.get("unresolved_fields", [])
    if unresolved:
        log(f"\n── UNRESOLVED FIELDS ({len(unresolved)}) ──────────────────────────")
        for u in unresolved:
            log(f"  ⚠️  [{u.get('classified_role')}]  {u.get('label', '')[:70]}")
            log(f"       resolved_value : {u.get('resolved_value')}")
            log(f"       fill_status    : {u.get('fill_status')}")
            log(f"       reason         : {u.get('reason')}")

    # ── Save result to disk ───────────────────────────────────────────────────
    result_path = save_result(run_dir, job, body, elapsed)
    log(f"\n  💾 Result saved → {result_path}")


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Artemis test-fill runner")
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
    args = parser.parse_args()

    section("Artemis test-fill runner")
    log(f"Base URL : {BASE_URL}")
    log(f"Jobs     : {len(JOBS)}")
    log(f"Storage  : {args.storage}")

    if args.clear_screenshots:
        log("--clear-screenshots flag set — clearing screenshots...")
        clear_screenshots()

    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(RESULTS_DIR, run_ts)
    os.makedirs(run_dir, exist_ok=True)
    log(f"Results  : {run_dir}")

    token = authenticate()

    if args.storage == "s3":
        resume_override = fetch_resume_path(token, "s3")
    else:
        # Keep local mode deterministic via the script constant.
        resume_override = RESUME_PATH
        log(f"Resume   : {resume_override}")

    for i, job in enumerate(JOBS, start=1):
        log(f"\n▶ Job {i}/{len(JOBS)}: {job['label']}")
        run_test_fill(token, job, run_dir, resume_path=resume_override)
        if i < len(JOBS):
            log("Waiting 3 s before next job...")
            time.sleep(3)

    section("All done")


if __name__ == "__main__":
    main()
