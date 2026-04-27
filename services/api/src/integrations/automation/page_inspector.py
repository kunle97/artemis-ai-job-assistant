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

import uuid
from pathlib import Path

from playwright.sync_api import sync_playwright

from src.integrations.automation.helpers import prepare_application_page, extract_fields, save_screenshot, normalize_application_url


class ApplicationPageInspector:
    @staticmethod
    def inspect(application_url: str) -> dict:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            try:
                normalized_application_url = normalize_application_url(application_url)
                page.goto(normalized_application_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(1800)

                prepare_application_page(page, application_url)
                page.wait_for_timeout(1000)

                title = page.title()
                fields = extract_fields(page)
                screenshot_path = save_screenshot(page, url=application_url)

                return {
                    "application_url": normalized_application_url,
                    "status": "inspected",
                    "title": title,
                    "fields": fields,
                    "screenshot_path": screenshot_path,
                    "notes": [
                        "Playwright inspection completed.",
                        "Inspector v4 adds richer radio/select/combobox extraction.",
                    ],
                }
            finally:
                context.close()
                browser.close()
