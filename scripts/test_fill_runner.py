"""
Test fill runner — authenticates then runs /automation/test-fill for each job URL.

Usage:
    python scripts/test_fill_runner.py [--clear-screenshots]

Flags:
    --clear-screenshots   Delete all files in uploads/automation/ before running.

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

# ─── CONFIG ──────────────────────────────────────────────────────────────────

BASE_URL = "http://localhost:8000"
USERNAME = "janedoe@example.com"
PASSWORD = "password"

SCREENSHOTS_DIR = os.path.join(
    os.path.dirname(__file__),
    "../services/api/uploads/automation",
)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "test_results")

RESUME_PATH = "/Users/kunle/Documents/dev/artemis-ai-job-assistant/services/api/uploads/resumes/9c310282-3ebd-4e8a-a92a-25bf715d8156.pdf"

JOBS = [
    # {
    #     "label": "PermitFlow – Ashby",
    #     "application_url": "https://jobs.ashbyhq.com/permitflow/8d780d11-57e8-4570-a599-b8dc3d4377a1/application?utm_source=LinkedInPaid",
    #     "resume_file_path": RESUME_PATH,
    # },
    # {
    #     "label": "Kiddom – Lever",
    #     "application_url": "https://jobs.lever.co/kiddom/8934d8a1-9b84-4e1d-ad3e-950e98151b16/",
    #     "resume_file_path": RESUME_PATH,
    # },
    {
        "label": "Equal Experts - Greenhouse",
        "application_url": "https://job-boards.greenhouse.io/equalexperts/jobs/8454247002",
        "resume_file_path": RESUME_PATH,
    },
]

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


# ─── FILL RUNNER ─────────────────────────────────────────────────────────────

def run_test_fill(token: str, job: dict, run_dir: str) -> None:
    label = job["label"]
    section(f"[{label}]  {job['application_url']}")

    payload = {
        "application_url": job["application_url"],
        "resume_file_path": job["resume_file_path"],
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
    args = parser.parse_args()

    section("Artemis test-fill runner")
    log(f"Base URL : {BASE_URL}")
    log(f"Jobs     : {len(JOBS)}")

    if args.clear_screenshots:
        log("--clear-screenshots flag set — clearing screenshots...")
        clear_screenshots()

    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(RESULTS_DIR, run_ts)
    os.makedirs(run_dir, exist_ok=True)
    log(f"Results  : {run_dir}")

    token = authenticate()

    for i, job in enumerate(JOBS, start=1):
        log(f"\n▶ Job {i}/{len(JOBS)}: {job['label']}")
        run_test_fill(token, job, run_dir)
        if i < len(JOBS):
            log("Waiting 3 s before next job...")
            time.sleep(3)

    section("All done")


if __name__ == "__main__":
    main()
