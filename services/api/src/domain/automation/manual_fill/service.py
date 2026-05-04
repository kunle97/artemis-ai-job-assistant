"""
Manual fill / retry service.
"""

from __future__ import annotations

import logging

from src.domain.automation.fill.models import AutomationFillRequest
from src.domain.automation.manual_fill.helpers import find_matching_override
from src.domain.automation.manual_fill.models import AutomationManualFillRequest

logger = logging.getLogger(__name__)


class AutomationManualFillService:
    def __init__(self, automation_service, fill_service):
        self.automation_service = automation_service
        self.fill_service = fill_service

    def manual_fill(self, *, user_id, payload: AutomationManualFillRequest):
        logger.info(
            "[ManualFillService] manual_fill start user_id=%s url=%s overrides=%d",
            user_id,
            payload.application_url,
            len(payload.field_overrides),
        )
        inspect_result = self.automation_service.inspect_application_page(
            payload.application_url
        )

        raw_field_count = len(inspect_result.get("fields", []))
        logger.info("[ManualFillService] inspect complete fields=%d", raw_field_count)

        updated_fields: list[dict] = []
        override_count = 0

        for field in inspect_result.get("fields", []):
            field_dict = dict(field)

            matched_override = find_matching_override(
                field=field_dict,
                overrides=payload.field_overrides,
            )

            if matched_override:
                field_dict["manual_override_value"] = matched_override.value
                override_count += 1

            updated_fields.append(field_dict)

        logger.info("[ManualFillService] applied overrides=%d", override_count)

        fill_result = self.fill_service.fill_safe_fields(
            user_id=user_id,
            payload=AutomationFillRequest(
                application_url=payload.application_url,
                inspected_fields=updated_fields,
                application_id=payload.application_id,
                resume_file_path=payload.resume_file_path,
            ),
        )

        logger.info(
            "[ManualFillService] manual_fill complete filled=%d skipped=%d",
            fill_result.filled_count,
            fill_result.skipped_count,
        )
        return {
            "inspect": inspect_result,
            "fill": fill_result,
        }