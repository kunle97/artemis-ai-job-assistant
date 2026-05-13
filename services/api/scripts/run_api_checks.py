"""
Parent runner for API validation scripts.

Runs all validation scripts with optional per-script argument overrides.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys


SCRIPTS = {
    "env": "env_diagnostics.py",
    "auth": "check_auth_bootstrap.py",
    "storage": "preflight_storage_backend.py",
    "resume": "check_resume_upload_parse.py",
    "async": "verify_async_pipeline_dispatch.py",
    "guardrails": "check_submission_guardrails.py",
    "feed": "check_feed_scan_persist.py",
    "discovery": "check_job_source_discovery.py",
    "migrations": "check_db_migrations.py",
}


def _resolve_python() -> str:
    """Prefer project venv python; allow override via SCRIPT_PYTHON."""
    override = os.getenv("SCRIPT_PYTHON")
    if override:
        return override

    venv_python = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "venv", "bin", "python"))
    if os.path.exists(venv_python):
        return venv_python
    return sys.executable


def _run_script(script_file: str, raw_args: str, python_exec: str) -> int:
    cmd = [python_exec, f"scripts/{script_file}"] + shlex.split(raw_args or "")
    print("\n==>", " ".join(cmd))
    proc = subprocess.run(cmd, check=False)
    return proc.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Run API validation script suite")
    parser.add_argument(
        "--only",
        default="all",
        help="Comma separated script keys to run (default: all)."
             " Keys: " + ",".join(SCRIPTS.keys()),
    )
    parser.add_argument("--continue-on-error", action="store_true", help="Continue after failures")

    for key in SCRIPTS:
        parser.add_argument(
            f"--{key}-args",
            default="",
            help=f"Extra args passed to {SCRIPTS[key]}",
        )

    args = parser.parse_args()

    selected = list(SCRIPTS.keys())
    if args.only != "all":
        requested = [item.strip() for item in args.only.split(",") if item.strip()]
        invalid = [item for item in requested if item not in SCRIPTS]
        if invalid:
            raise ValueError("Unknown script key(s): " + ", ".join(invalid))
        selected = requested

    failures: list[str] = []
    python_exec = _resolve_python()

    print(f"Using python executable: {python_exec}")

    for key in selected:
        rc = _run_script(SCRIPTS[key], getattr(args, f"{key}_args"), python_exec)
        if rc != 0:
            failures.append(f"{key} (exit={rc})")
            if not args.continue_on_error:
                break

    if failures:
        print("\nFAIL run_api_checks")
        for item in failures:
            print("-", item)
        sys.exit(1)

    print("\nPASS run_api_checks")


if __name__ == "__main__":
    main()
