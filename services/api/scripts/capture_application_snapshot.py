"""Capture a local HTML snapshot of an application page for offline inspect tests.

Usage:
    python scripts/capture_application_snapshot.py --url <APPLICATION_URL>
    python scripts/capture_application_snapshot.py --url <APPLICATION_URL> --out uploads/automation/snapshots/custom.html
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

API_ROOT = Path(__file__).resolve().parent.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from src.integrations.automation.browser import create_stealth_context
from src.integrations.automation.helpers import normalize_application_url, prepare_application_page
from src.core.config import AUTOMATION_UPLOADS_DIR


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "snapshot"


def _default_output_path(url: str) -> Path:
    snapshots_dir = AUTOMATION_UPLOADS_DIR / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    hostish = url.split("//", 1)[-1].split("/", 1)[0]
    filename = f"{_slug(hostish)}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    return snapshots_dir / filename


def capture_snapshot(application_url: str, output_path: Path, wait_ms: int) -> Path:
    normalized_url = normalize_application_url(application_url)

    with sync_playwright() as playwright:
        browser, context, page = create_stealth_context(playwright)
        try:
            page.goto(normalized_url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(wait_ms)
            prepare_application_page(page, normalized_url)
            page.wait_for_timeout(1200)

            html = page.content()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html, encoding="utf-8")
            return output_path.resolve()
        finally:
            context.close()
            browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture local HTML snapshot for inspect testing")
    parser.add_argument("--url", required=True, help="Application page URL to snapshot")
    parser.add_argument("--out", help="Output .html path (defaults to uploads/automation/snapshots/<host>-<timestamp>.html)")
    parser.add_argument("--wait-ms", type=int, default=2500, help="Extra wait time after initial load in milliseconds")
    args = parser.parse_args()

    output = Path(args.out).expanduser() if args.out else _default_output_path(args.url)
    snapshot_path = capture_snapshot(args.url, output, args.wait_ms)

    print(f"Saved snapshot: {snapshot_path}")
    print(f"Use for inspect: file://{snapshot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
