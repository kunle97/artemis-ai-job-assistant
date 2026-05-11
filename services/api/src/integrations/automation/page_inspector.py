"""
Playwright application inspector.

Extracts structured fields from job application pages.

Current goals:
- detect common form elements reliably
- preserve metadata needed for planning/fill
- group radio buttons by shared name
- preserve select options where available
- identify combobox/select-like inputs
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from urllib.parse import unquote, urlparse

import random

from playwright.sync_api import Browser, sync_playwright

from src.integrations.automation.browser import create_fresh_context, create_stealth_context
from src.integrations.automation.helpers import (
    detect_already_applied_signal,
    extract_fields,
    normalize_application_url,
    prepare_application_page,
    save_screenshot,
)


logger = logging.getLogger(__name__)


def _extract_job_context(page) -> str | None:
        """Extract a compact text snapshot of the job description before the form."""
        try:
                text = page.evaluate(
                        """
                        () => {
                            const root = document.querySelector('main') || document.body;
                            if (!root) return '';

                            const stopPhrases = ['apply for this job', 'autofill with mygreenhouse'];
                            const nodes = Array.from(root.querySelectorAll('h1, h2, h3, p, li'));
                            const lines = [];
                            for (const node of nodes) {
                                const text = (node.innerText || '').replace(/\s+/g, ' ').trim();
                                if (!text) continue;
                                const lowered = text.toLowerCase();
                                if (stopPhrases.some((phrase) => lowered.includes(phrase))) break;
                                if (lines.length && lines[lines.length - 1] === text) continue;
                                lines.push(text);
                                if (lines.join('\n').length >= 2400) break;
                            }
                            return lines.join('\n').slice(0, 2400);
                        }
                        """
                )
        except Exception:
                return None

        cleaned = (text or "").strip()
        return cleaned or None


class ApplicationPageInspector:
    @staticmethod
    def _is_local_snapshot_url(application_url: str) -> bool:
        parsed = urlparse((application_url or "").strip())
        return parsed.scheme == "file"

    @staticmethod
    def _load_local_snapshot(page, application_url: str) -> None:
        parsed = urlparse((application_url or "").strip())
        if parsed.scheme != "file":
            raise ValueError("Local snapshot URL must use the file:// scheme")

        snapshot_path = Path(unquote(parsed.path or "")).expanduser().resolve()
        if not snapshot_path.exists() or not snapshot_path.is_file():
            raise ValueError(f"Local snapshot file does not exist: {snapshot_path}")

        logger.info("[PageInspector] Loading local snapshot for inspect: %s", snapshot_path)
        html = snapshot_path.read_text(encoding="utf-8")
        page.set_content(html, wait_until="domcontentloaded")

    @staticmethod
    def inspect(application_url: str, browser: Browser | None = None) -> dict:
        """Inspect a job application page and return structured field data.

        When *browser* is supplied the caller's browser process is reused and
        only a fresh context is created (no new browser launch).  When it is
        ``None`` a full Playwright stack is launched and torn down internally.
        """
        if browser is not None:
            context, page = create_fresh_context(browser)
            try:
                return ApplicationPageInspector._do_inspect(page, application_url)
            finally:
                context.close()
        else:
            with sync_playwright() as playwright:
                _browser, context, page = create_stealth_context(playwright)
                try:
                    return ApplicationPageInspector._do_inspect(page, application_url)
                finally:
                    context.close()
                    _browser.close()

    @staticmethod
    def _do_inspect(page, application_url: str) -> dict:
        normalized_application_url = normalize_application_url(application_url)
        local_snapshot_mode = ApplicationPageInspector._is_local_snapshot_url(normalized_application_url)

        if local_snapshot_mode:
            logger.info("[PageInspector] Inspect mode=local_snapshot url=%s", normalized_application_url)
            ApplicationPageInspector._load_local_snapshot(page, normalized_application_url)
            page.wait_for_timeout(400)
        else:
            logger.info("[PageInspector] Inspect mode=live_navigation url=%s", normalized_application_url)
            page.goto(normalized_application_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(random.randint(1800, 3200))

            prepare_application_page(page, application_url)
            page.wait_for_timeout(1000)

        title = page.title()
        job_context = _extract_job_context(page)
        already_applied = detect_already_applied_signal(page)
        fields = extract_fields(page)
        screenshot_path = save_screenshot(page, url=application_url)

        return {
            "application_url": normalized_application_url,
            "status": "inspected",
            "title": title,
            "job_context": job_context,
            "already_applied": already_applied,
            "fields": fields,
            "screenshot_path": screenshot_path,
            "notes": [
                "Playwright inspection completed.",
                "Inspector v4 adds richer radio/select/combobox extraction.",
                "Inspection used local HTML snapshot." if local_snapshot_mode else "Inspection used live page navigation.",
            ],
        }
