"""
Environment diagnostics script.

Prints key runtime configuration in a redacted/safe way.
"""

from __future__ import annotations

import os


def _redacted(name: str) -> str:
    val = os.getenv(name)
    if not val:
        return "<empty>"
    if len(val) <= 6:
        return "<set>"
    return val[:3] + "***" + val[-2:]


def main() -> None:
    print("ENV diagnostics")
    print(f"APP_ENV={os.getenv('APP_ENV', '<unset>')}")
    print(f"DATABASE_URL={os.getenv('DATABASE_URL', '<unset>')}")
    print(f"REDIS_URL={os.getenv('REDIS_URL', '<unset>')}")
    print(f"STORAGE_BACKEND={os.getenv('STORAGE_BACKEND', '<unset>')}")
    print(f"AWS_REGION={os.getenv('AWS_REGION', '<unset>')}")
    print(f"S3_BUCKET_NAME={os.getenv('S3_BUCKET_NAME', '<unset>')}")
    print(f"AWS_ACCESS_KEY_ID={_redacted('AWS_ACCESS_KEY_ID')}")
    print(f"AWS_SECRET_ACCESS_KEY={_redacted('AWS_SECRET_ACCESS_KEY')}")
    print(f"AWS_SESSION_TOKEN={_redacted('AWS_SESSION_TOKEN')}")
    print(f"GROQ_API_KEY={_redacted('GROQ_API_KEY')}")


if __name__ == "__main__":
    main()
