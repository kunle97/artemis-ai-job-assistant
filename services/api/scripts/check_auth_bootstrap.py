"""
Auth bootstrap smoke test script.

Validates register/login/session flow for a fresh user.
"""

from __future__ import annotations

import argparse

from _api_script_utils import DEFAULT_BASE_URL, check_health, register_and_login


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate auth bootstrap flow")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL")
    args = parser.parse_args()

    check_health(args.base_url)
    auth = register_and_login(base_url=args.base_url, prefix="auth_smoke")

    print("PASS auth bootstrap")
    print(f"base_url={args.base_url}")
    print(f"email={auth.email}")
    print(f"user_id={auth.user_id}")


if __name__ == "__main__":
    main()
