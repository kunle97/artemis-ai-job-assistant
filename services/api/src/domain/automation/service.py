"""
Automation domain service.
"""

from __future__ import annotations

import logging

from playwright.sync_api import Browser

logger = logging.getLogger(__name__)


class AutomationService:
    def __init__(self, page_inspector):
        self.page_inspector = page_inspector

    def inspect_application_page(self, payload, browser: Browser | None = None):
        application_url = self._extract_application_url(payload)

        logger.info(f"[Automation] Inspecting page: {application_url}")

        result = self.page_inspector.inspect(application_url, browser=browser)

        field_count = len(result.get("fields", [])) if isinstance(result, dict) else len(result.fields)
        logger.info(f"[Automation] Inspection complete: {field_count} fields found")

        return result

    def _extract_application_url(self, payload) -> str:
        if isinstance(payload, str):
            application_url = payload.strip()
        else:
            application_url = getattr(payload, "application_url", None)

        if not application_url:
            raise ValueError("application_url is required")

        return application_url