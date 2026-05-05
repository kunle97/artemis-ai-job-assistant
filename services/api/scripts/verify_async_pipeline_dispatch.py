"""
Async pipeline dispatch verifier.

Creates a user/application, dispatches run, and polls until terminal state.
"""

from __future__ import annotations

import argparse
import time

import requests

from _api_script_utils import (
    DEFAULT_BASE_URL,
    check_health,
    create_job_and_application,
    register_and_login,
)


TERMINAL = {"filled", "awaiting_submission", "submitted", "failed"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify async pipeline dispatch flow")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL")
    parser.add_argument("--apply-url", default="https://example.com/async-dispatch-check", help="Job apply URL")
    parser.add_argument("--timeout-seconds", type=int, default=120, help="Polling timeout")
    args = parser.parse_args()

    check_health(args.base_url)
    auth = register_and_login(base_url=args.base_url, prefix="async_dispatch")
    _, app_id = create_job_and_application(auth=auth, apply_url=args.apply_url)

    run_resp = requests.post(
        f"{args.base_url}/applications/{app_id}/run",
        headers=auth.headers,
        timeout=30,
    )
    run_resp.raise_for_status()
    payload = run_resp.json()
    task_id = payload.get("task_id")
    if not task_id:
        raise RuntimeError("Run response missing task_id")

    deadline = time.time() + args.timeout_seconds
    final_status = None
    while time.time() < deadline:
        app_resp = requests.get(f"{args.base_url}/applications/{app_id}", headers=auth.headers, timeout=20)
        app_resp.raise_for_status()
        status = app_resp.json().get("status")
        if status in TERMINAL:
            final_status = status
            break
        time.sleep(2)

    if final_status is None:
        raise TimeoutError(f"Application {app_id} did not reach terminal status within timeout")

    print("PASS async dispatch")
    print(f"application_id={app_id}")
    print(f"task_id={task_id}")
    print(f"final_status={final_status}")


if __name__ == "__main__":
    main()
