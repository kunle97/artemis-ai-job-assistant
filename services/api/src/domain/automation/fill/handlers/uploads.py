"""
Handlers for file uploads.
"""

from __future__ import annotations

from pathlib import Path

from src.domain.automation.fill.models import AutomationFillFieldResult
from src.domain.automation.fill.locators import find_field_container, locate_field


def upload_resume(page, field: dict, resume_path: str | None) -> AutomationFillFieldResult:
    label = field.get("label")
    name = field.get("name")
    role = field.get("classified_role", "resume_upload")
    placeholder = field.get("placeholder")

    if not resume_path:
        return _result(
            label=label,
            name=name,
            role=role,
            value=None,
            status="skipped_no_file",
        )

    file_path = Path(resume_path)
    if not file_path.exists() or not file_path.is_file():
        return _result(
            label=label,
            name=name,
            role=role,
            value=resume_path,
            status="skipped_invalid_resume_path",
        )

    locator = None

    try:
        container = find_field_container(page, label)
        if container is not None:
            file_inputs = container.locator('input[type="file"]')
            if file_inputs.count() > 0:
                locator = file_inputs.first
    except Exception:
        locator = None

    if locator is None:
        try:
            inputs = page.locator('input[type="file"]')
            count = inputs.count()

            for i in range(count):
                candidate = inputs.nth(i)
                try:
                    candidate_html = (candidate.evaluate("el => el.outerHTML") or "").lower()
                except Exception:
                    candidate_html = ""

                if any(token in candidate_html for token in ["resume", "cv"]):
                    locator = candidate
                    break

            if locator is None and count > 0:
                locator = inputs.first
        except Exception:
            locator = None

    if locator is None:
        return _result(
            label=label,
            name=name,
            role=role,
            value=resume_path,
            status="skipped_not_found",
        )

    try:
        locator.set_input_files(str(file_path))
        return _result(
            label=label,
            name=name,
            role=role,
            value=str(file_path),
            status="filled",
        )
    except Exception as exc:
        return _result(
            label=label,
            name=name,
            role=role,
            value=f"{str(file_path)} | error={type(exc).__name__}: {str(exc)}",
            status="error",
        )
    
def skip_cover_letter_upload(field: dict) -> AutomationFillFieldResult:
    return _result(
        label=field.get("label"),
        name=field.get("name"),
        role=field.get("classified_role", "cover_letter_upload"),
        value=None,
        status="skipped_cover_letter_upload",
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