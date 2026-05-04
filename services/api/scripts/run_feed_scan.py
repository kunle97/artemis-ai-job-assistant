"""
scripts/run_feed_scan.py

Dev utility: scan all boards in JOB_SOURCE_REGISTRY and log every job in detail.

Runs entirely without a database by default (dry-run).
Optionally persists results for a specific user via --persist --user-id <uuid>.

Usage
-----
# Scan everything, print all jobs
python scripts/run_feed_scan.py

# Scope to a single ATS
python scripts/run_feed_scan.py --source greenhouse

# Filter job titles (substring match, case-insensitive, OR logic)
python scripts/run_feed_scan.py --keywords "engineer,backend,python"

# Only scan specific companies
python scripts/run_feed_scan.py --companies stripe,coinbase,linear

# Persist to DB for a user (requires DB running)
python scripts/run_feed_scan.py --persist --user-id <uuid>

# Suppress job body, only show summary table
python scripts/run_feed_scan.py --summary-only
"""

from __future__ import annotations

import argparse
import logging
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Ensure the package root is on the path so src.* imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.domain.jobs.source_registry import JOB_SOURCE_REGISTRY
from src.integrations.adapters.registry import get_adapter

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("feed_scan")

_MAX_WORKERS = 10
_SEP = "-" * 80


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan ATS job boards and log results."
    )
    parser.add_argument(
        "--source",
        choices=["greenhouse", "lever", "ashby"],
        default=None,
        help="Restrict scan to a single ATS source.",
    )
    parser.add_argument(
        "--companies",
        default=None,
        help="Comma-separated list of company keys to scan (e.g. stripe,linear).",
    )
    parser.add_argument(
        "--keywords",
        default=None,
        help="Comma-separated title keywords to filter results (OR logic).",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Skip per-job detail, only print the summary table.",
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Persist new jobs to the database (requires --user-id).",
    )
    parser.add_argument(
        "--user-id",
        default=None,
        help="UUID of the user to run JobFeedService for (used with --persist).",
    )
    return parser.parse_args()


def _build_work_items(
    source_filter: str | None,
    company_filter: set[str] | None,
) -> list[tuple[str, str, str]]:
    """Return (source, company_key, board_token) tuples to scan."""
    items: list[tuple[str, str, str]] = []
    for source, companies in JOB_SOURCE_REGISTRY.items():
        if source_filter and source != source_filter:
            continue
        for company_key, cfg in companies.items():
            if company_filter and company_key not in company_filter:
                continue
            items.append((source, company_key, cfg["board_token"]))
    return items


def _fetch_one(source: str, company_key: str, board_token: str) -> list[dict]:
    adapter = get_adapter(source)
    jobs = adapter.search_jobs(board_token=board_token)
    # Annotate display_name for logging convenience
    display = JOB_SOURCE_REGISTRY[source][company_key]["display_name"]
    for j in jobs:
        j["_company_display"] = display
    return jobs


def _log_job(index: int, job: dict) -> None:
    salary = ""
    if job.get("salary_min") or job.get("salary_max"):
        lo = job.get("salary_min", "?")
        hi = job.get("salary_max", "?")
        currency = job.get("currency") or "USD"
        salary = f"  Salary  : {currency} {lo} – {hi}"

    logger.info(
        "\n"
        "  #%-5d  %s\n"
        "  Company : %s  [%s]\n"
        "  Location: %s  |  %s\n"
        "  URL     : %s%s",
        index,
        job.get("title", "(no title)"),
        job.get("_company_display", job.get("company_name", "")),
        job.get("source", ""),
        job.get("location") or "—",
        job.get("workplace_type") or "unspecified",
        job.get("apply_url", ""),
        ("\n" + salary) if salary else "",
    )


# ---------------------------------------------------------------------------
# Persist path (optional)
# ---------------------------------------------------------------------------

def _persist_via_service(user_id: str) -> None:
    from src.infrastructure.db.session import SessionLocal
    from src.domain.jobs.feed_service import JobFeedService

    logger.info("[persist] Running JobFeedService.scan() for user %s", user_id)
    db = SessionLocal()
    try:
        service = JobFeedService(user_id=user_id, db=db)
        new_jobs = service.scan()
        db.commit()
        logger.info("[persist] %d new job(s) stored to DB.", len(new_jobs))
        for job in new_jobs:
            logger.info(
                "  stored  %-60s  %s / %s",
                job.title,
                job.source,
                job.company_name,
            )
    except Exception as exc:
        db.rollback()
        logger.error("[persist] Scan failed: %s", exc)
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = _parse_args()

    if args.persist:
        if not args.user_id:
            logger.error("--persist requires --user-id <uuid>")
            sys.exit(1)
        _persist_via_service(args.user_id)
        return

    company_filter: set[str] | None = None
    if args.companies:
        company_filter = {c.strip().lower() for c in args.companies.split(",")}

    keywords: list[str] = []
    if args.keywords:
        keywords = [k.strip().lower() for k in args.keywords.split(",") if k.strip()]

    work_items = _build_work_items(args.source, company_filter)

    logger.info(
        "%s\n  Artemis Feed Scanner  —  %s\n"
        "  ATS source : %s\n"
        "  Companies  : %s\n"
        "  Keywords   : %s\n"
        "  Boards     : %d\n%s",
        _SEP,
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        args.source or "all",
        ", ".join(sorted(company_filter)) if company_filter else "all",
        ", ".join(keywords) if keywords else "none",
        len(work_items),
        _SEP,
    )

    if not work_items:
        logger.warning("No boards matched the given filters.")
        return

    # Concurrent fetch
    all_jobs: list[dict] = []
    board_counts: dict[str, int] = {}  # "source/company_key" -> count

    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
        futures = {
            executor.submit(_fetch_one, src, ck, bt): (src, ck, bt)
            for src, ck, bt in work_items
        }
        for future in as_completed(futures):
            src, ck, bt = futures[future]
            label = f"{src}/{ck}"
            try:
                jobs = future.result()
                board_counts[label] = len(jobs)
                all_jobs.extend(jobs)
                logger.info("  fetched  %-40s  %d jobs", label, len(jobs))
            except Exception as exc:  # noqa: BLE001
                board_counts[label] = -1
                logger.warning("  FAILED   %-40s  %s", label, exc)

    # Keyword filter
    if keywords:
        before = len(all_jobs)
        all_jobs = [
            j for j in all_jobs
            if any(kw in (j.get("title") or "").lower() for kw in keywords)
        ]
        logger.info(
            "\n  Keyword filter applied: %d → %d jobs", before, len(all_jobs)
        )

    logger.info("%s\n  Total jobs fetched : %d\n%s", _SEP, len(all_jobs), _SEP)

    # Detailed job listing
    if not args.summary_only:
        for i, job in enumerate(all_jobs, start=1):
            _log_job(i, job)

    # Summary table
    logger.info("\n%s\n  BOARD SUMMARY\n%s", _SEP, _SEP)
    logger.info("  %-45s  %s", "Board", "Jobs")
    logger.info("  %-45s  %s", "-" * 45, "----")
    for label in sorted(board_counts):
        count = board_counts[label]
        status = str(count) if count >= 0 else "ERROR"
        logger.info("  %-45s  %s", label, status)

    logger.info(
        "%s\n  Scan complete: %d board(s), %d total job(s)\n%s",
        _SEP,
        len(work_items),
        len(all_jobs),
        _SEP,
    )


if __name__ == "__main__":
    main()
