"""
Job source discovery checker.

Runs discovery crawl and optional promote endpoints to demonstrate ATS discovery in action.
"""

from __future__ import annotations

import argparse

import requests

from _api_script_utils import DEFAULT_BASE_URL, check_health, register_and_login


def _parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run discovery crawl/promote demo")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL")
    parser.add_argument(
        "--hosted-urls",
        default="https://job-boards.greenhouse.io/stripe,https://jobs.lever.co/notion,https://job-boards.greenhouse.io/jobs",
        help="Comma-separated hosted ATS URLs",
    )
    parser.add_argument(
        "--career-urls",
        default="",
        help="Comma-separated career URLs that may redirect to ATS boards",
    )
    parser.add_argument(
        "--skip-promote",
        action="store_true",
        help="Only run crawl; skip promote call",
    )
    args = parser.parse_args()

    hosted_urls = _parse_csv(args.hosted_urls)
    career_urls = _parse_csv(args.career_urls)

    check_health(args.base_url)
    auth = register_and_login(base_url=args.base_url, prefix="discovery_demo")

    crawl_resp = requests.post(
        f"{args.base_url}/jobs/discovery/crawl",
        headers=auth.headers,
        json={"hosted_urls": hosted_urls, "career_urls": career_urls},
        timeout=45,
    )
    crawl_resp.raise_for_status()
    crawl_payload = crawl_resp.json()

    print("PASS discovery crawl")
    print(f"run_id={crawl_payload['run_id']}")
    print(f"total_candidates={crawl_payload['total_candidates']}")
    print(f"provider_counts={crawl_payload['provider_counts']}")

    for idx, candidate in enumerate(crawl_payload.get("candidates", []), start=1):
        print(
            f"candidate_{idx}="
            f"provider={candidate['detected_provider']}"
            f",token={candidate.get('normalized_token')}"
            f",channel={candidate['source_channel']}"
            f",url={candidate['discovered_url']}"
        )

    if args.skip_promote:
        return

    promote_resp = requests.post(
        f"{args.base_url}/jobs/discovery/promote",
        headers=auth.headers,
        json={"run_id": crawl_payload["run_id"], "is_active": True},
        timeout=45,
    )
    promote_resp.raise_for_status()
    promote_payload = promote_resp.json()

    print("PASS discovery promote")
    print(f"selected_candidates={promote_payload['selected_candidates']}")
    print(f"promoted_count={promote_payload['promoted_count']}")
    print(f"skipped_count={promote_payload['skipped_count']}")

    sources_resp = requests.get(
        f"{args.base_url}/jobs/sources",
        headers=auth.headers,
        timeout=30,
    )
    sources_resp.raise_for_status()
    sources_payload = sources_resp.json()
    print(f"active_sources_after_promote={len(sources_payload)}")


if __name__ == "__main__":
    main()
