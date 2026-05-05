"""
Feed scan persist checker.

Triggers feed scan for a fresh user and validates feed endpoint access.
"""

from __future__ import annotations

import argparse

import requests

from _api_script_utils import DEFAULT_BASE_URL, check_health, register_and_login


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify feed scan + feed read endpoints")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL")
    parser.add_argument("--skip-scan", action="store_true", help="Skip POST /jobs/feed/scan")
    args = parser.parse_args()

    check_health(args.base_url)
    auth = register_and_login(base_url=args.base_url, prefix="feed_scan")

    if not args.skip_scan:
        scan_resp = requests.post(f"{args.base_url}/jobs/feed/scan", headers=auth.headers, timeout=120)
        scan_resp.raise_for_status()
        new_jobs = scan_resp.json().get("new_jobs_found", 0)
    else:
        new_jobs = -1

    feed_resp = requests.get(f"{args.base_url}/jobs/feed?skip=0&limit=5", headers=auth.headers, timeout=30)
    feed_resp.raise_for_status()
    payload = feed_resp.json()
    total = payload.get("total")
    jobs = payload.get("jobs", [])

    print("PASS feed scan persist")
    print(f"scan_new_jobs={new_jobs}")
    print(f"feed_total={total}")
    print(f"feed_returned={len(jobs)}")


if __name__ == "__main__":
    main()
