"""
Submission guardrails checker.

Confirms submission is blocked when pipeline/safety requirements are unmet.
"""

from __future__ import annotations

import argparse

import requests

from _api_script_utils import (
    DEFAULT_BASE_URL,
    check_health,
    create_job_and_application,
    register_and_login,
)


def _assert_blocked(resp: requests.Response, context: str) -> None:
    if resp.status_code != 400:
        raise AssertionError(f"Expected 400 for {context}, got {resp.status_code}: {resp.text}")
    detail = str(resp.json().get("detail", ""))
    if "Submission blocked" not in detail:
        raise AssertionError(f"Expected guardrail detail for {context}, got: {detail}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify submission guardrail enforcement")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL")
    parser.add_argument("--apply-url", default="https://example.com/guardrails-check", help="Job apply URL")
    args = parser.parse_args()

    check_health(args.base_url)
    auth = register_and_login(base_url=args.base_url, prefix="guardrails")
    _, app_id = create_job_and_application(auth=auth, apply_url=args.apply_url)

    submit_before = requests.post(
        f"{args.base_url}/applications/{app_id}/submit",
        headers=auth.headers,
        timeout=30,
    )
    _assert_blocked(submit_before, "submit before authorize")

    authz = requests.post(
        f"{args.base_url}/applications/{app_id}/authorize",
        headers=auth.headers,
        timeout=30,
    )
    authz.raise_for_status()

    submit_after_auth = requests.post(
        f"{args.base_url}/applications/{app_id}/submit",
        headers=auth.headers,
        timeout=30,
    )
    _assert_blocked(submit_after_auth, "submit after authorize but before run")

    print("PASS submission guardrails")
    print(f"application_id={app_id}")


if __name__ == "__main__":
    main()
