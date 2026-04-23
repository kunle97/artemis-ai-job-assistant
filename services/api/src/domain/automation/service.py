"""
Automation domain service.

Handles page inspection and normalizes inputs so callers can pass either:
- a raw application URL string
- or an object with an `application_url` attribute
"""

from __future__ import annotations


class AutomationService:
    def __init__(self, page_inspector):
        self.page_inspector = page_inspector

    def inspect_application_page(self, payload):
        application_url = self._extract_application_url(payload)
        return self.page_inspector.inspect(application_url)

    def _extract_application_url(self, payload) -> str:
        if isinstance(payload, str):
            application_url = payload.strip()
        else:
            application_url = getattr(payload, "application_url", None)

        if not application_url:
            raise ValueError("application_url is required")

        return application_url
    