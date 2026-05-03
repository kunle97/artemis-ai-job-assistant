"""
Manual fill / retry service.
"""

from __future__ import annotations

from src.domain.automation.fill.models import AutomationFillRequest
from src.domain.automation.manual_fill.helpers import find_matching_override
from src.domain.automation.manual_fill.models import AutomationManualFillRequest


class AutomationManualFillService:
    def __init__(self, automation_service, fill_service):
        self.automation_service = automation_service
        self.fill_service = fill_service

    def manual_fill(self, *, user_id, payload: AutomationManualFillRequest):
        inspect_result = self.automation_service.inspect_application_page(
            payload.application_url
        )

        updated_fields: list[dict] = []

        for field in inspect_result.get("fields", []):
            field_dict = dict(field)

            matched_override = find_matching_override(
                field=field_dict,
                overrides=payload.field_overrides,
            )

            if matched_override:
                field_dict["manual_override_value"] = matched_override.value

            updated_fields.append(field_dict)

        fill_result = self.fill_service.fill_safe_fields(
            user_id=user_id,
            payload=AutomationFillRequest(
                application_url=payload.application_url,
                inspected_fields=updated_fields,
                application_id=payload.application_id,
                resume_file_path=payload.resume_file_path,
            ),
        )

        return {
            "inspect": inspect_result,
            "fill": fill_result,
        }