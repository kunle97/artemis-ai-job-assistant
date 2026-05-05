"""
Database migration smoke checker.

Runs alembic current and alembic upgrade head from services/api.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys


def _resolve_python() -> str:
    """Prefer project venv python when available."""
    venv_python = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "venv", "bin", "python"))
    return venv_python if os.path.exists(venv_python) else sys.executable


def _run(cmd: list[str]) -> None:
    completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run migration smoke checks")
    parser.add_argument("--skip-upgrade", action="store_true", help="Only run alembic current")
    args = parser.parse_args()

    py = _resolve_python()

    _run([py, "-m", "alembic", "current"])
    if not args.skip_upgrade:
        _run([py, "-m", "alembic", "upgrade", "head"])

    print("PASS db migrations")


if __name__ == "__main__":
    main()
