"""
Storage backend preflight script.

Checks configured storage backend prerequisites before automation runs.
"""

from __future__ import annotations

import argparse
import os


REQUIRED_S3 = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION", "S3_BUCKET_NAME"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate storage backend environment")
    parser.add_argument(
        "--storage-backend",
        default=os.getenv("STORAGE_BACKEND", "local"),
        choices=["local", "s3"],
        help="Expected storage backend",
    )
    args = parser.parse_args()

    if args.storage_backend == "local":
        print("PASS storage preflight")
        print("backend=local")
        return

    missing = [name for name in REQUIRED_S3 if not os.getenv(name)]
    if missing:
        raise RuntimeError("Missing S3 env vars: " + ", ".join(missing))

    print("PASS storage preflight")
    print("backend=s3")
    print("aws_region=" + os.getenv("AWS_REGION", ""))


if __name__ == "__main__":
    main()
