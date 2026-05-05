"""
Resume upload and parse smoke test script.

Uploads a resume for a fresh user and validates list endpoint visibility.
"""

from __future__ import annotations

import argparse
import os
import tempfile

import requests

from _api_script_utils import DEFAULT_BASE_URL, check_health, register_and_login
from constants import RESUME_PATH


def _resolve_resume_path(candidate_path: str) -> tuple[str, bool]:
    """Return a usable resume path and whether it is a temporary generated file."""
    if candidate_path and os.path.exists(candidate_path):
        return candidate_path, False

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    tmp.write(
        "Sample Resume\n"
        "Name: Script Runner\n"
        "Email: script.runner@example.com\n"
        "Experience: API testing and automation\n"
    )
    tmp.flush()
    tmp.close()
    return tmp.name, True


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate resume upload and listing")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL")
    parser.add_argument("--resume-path", default=RESUME_PATH, help="Path to resume file")
    args = parser.parse_args()

    check_health(args.base_url)
    auth = register_and_login(base_url=args.base_url, prefix="resume_smoke")

    resume_path, is_temp = _resolve_resume_path(args.resume_path)

    with open(resume_path, "rb") as fh:
        filename = os.path.basename(resume_path)
        content_type = "text/plain" if filename.lower().endswith(".txt") else "application/pdf"
        upload = requests.post(
            f"{args.base_url}/resumes/upload",
            headers=auth.headers,
            files={"file": (filename, fh, content_type)},
            timeout=120,
        )
    upload.raise_for_status()

    if is_temp:
        os.unlink(resume_path)

    listed = requests.get(f"{args.base_url}/resumes", headers=auth.headers, timeout=30)
    listed.raise_for_status()
    resumes = listed.json()
    if not resumes:
        raise RuntimeError("Resume list is empty after upload")

    print("PASS resume upload + parse")
    print(f"uploaded_resume_id={upload.json().get('id')}")
    print(f"resume_count={len(resumes)}")


if __name__ == "__main__":
    main()
