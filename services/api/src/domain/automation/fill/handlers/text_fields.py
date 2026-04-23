"""
Handlers for plain text-like fields.
"""

from __future__ import annotations

from src.domain.automation.fill.locators import locate_field
from src.domain.automation.fill.models import AutomationFillFieldResult


def fill_text_field(page, field: dict, value: str | None) -> AutomationFillFieldResult:
    label = field.get("label")
    name = field.get("name")
    placeholder = field.get("placeholder")
    role = field.get("classified_role", "text")

    if not value:
        return _result(
            label=label,
            name=name,
            role=role,
            value=None,
            status="skipped_no_value",
        )

    locator = locate_field(
        page,
        name=name,
        label=label,
        placeholder=placeholder,
    )

    if locator is None:
        return _result(
            label=label,
            name=name,
            role=role,
            value=value,
            status="skipped_not_found",
        )

    try:
        locator.fill(value)
        return _result(
            label=label,
            name=name,
            role=role,
            value=value,
            status="filled",
        )
    except Exception:
        try:
            locator.click()
            locator.fill("")
            locator.type(value, delay=15)
            return _result(
                label=label,
                name=name,
                role=role,
                value=value,
                status="filled",
            )
        except Exception:
            return _result(
                label=label,
                name=name,
                role=role,
                value=value,
                status="error",
            )


def _result(
    *,
    label: str | None,
    name: str | None,
    role: str,
    value: str | None,
    status: str,
) -> AutomationFillFieldResult:
    return AutomationFillFieldResult(
        label=label,
        name=name,
        classified_role=role,
        resolved_value=value,
        fill_status=status,
    )