"""
Handlers for checkbox and checkbox_group fields.
"""

from __future__ import annotations

import logging

from src.domain.automation.fill.helpers import score_choice_match
from src.domain.automation.fill.models import AutomationFillFieldResult

logger = logging.getLogger(__name__)


def fill_checkbox_group(page, field: dict, value: str | None) -> AutomationFillFieldResult:
    """Tick checkboxes whose labels best match the resolved value.

    *value* may be a comma-separated list of preferred options (e.g. "Remote, San Francisco").
    Each comma-separated token is matched against the field options and the
    corresponding checkbox is checked.
    """
    label = field.get("label")
    role = field.get("classified_role", "preferred_office_location")
    options: list[dict] = field.get("options") or []

    if not value:
        return _result(label=label, role=role, value=None, status="skipped_no_value")

    if not options:
        return _result(label=label, role=role, value=value, status="skipped_no_options")

    tokens = [t.strip() for t in value.split(",") if t.strip()]
    filled_any = False

    for token in tokens:
        best_option, best_score = _find_best_option(options, token)
        if not best_option or best_score < 40:
            continue

        option_label = best_option.get("label") or best_option.get("value") or ""
        option_value = best_option.get("value") or option_label

        checked = _check_checkbox(page, option_label=option_label, option_value=option_value)
        if checked:
            filled_any = True
            logger.debug(
                "[CheckboxGroup] Checked option '%s' for token '%s' (score=%s)",
                option_label, token, best_score,
            )

    status = "filled" if filled_any else "skipped_option_not_applied"
    return _result(label=label, role=role, value=value, status=status)


def _find_best_option(options: list[dict], token: str) -> tuple[dict | None, int]:
    best = None
    best_score = -1
    for opt in options:
        lbl = opt.get("label") or ""
        val = opt.get("value") or ""
        score = max(score_choice_match(token, lbl), score_choice_match(token, val))
        if score > best_score:
            best_score = score
            best = opt
    return best, best_score


def _check_checkbox(page, *, option_label: str, option_value: str) -> bool:
    """Try multiple strategies to check a checkbox by its visible label or value."""
    # Strategy 1: by associated label text
    if option_label:
        try:
            cb = page.get_by_label(option_label, exact=False).first
            if cb.count() > 0 and not cb.is_checked():
                cb.scroll_into_view_if_needed()
                cb.check()
                return True
            if cb.count() > 0 and cb.is_checked():
                return True  # already checked — treat as success
        except Exception:
            pass

    # Strategy 2: by checkbox name/value attribute
    if option_value:
        try:
            cb = page.locator(f'input[type="checkbox"][name="{option_value}"]').first
            if cb.count() > 0 and not cb.is_checked():
                cb.scroll_into_view_if_needed()
                cb.check()
                return True
            if cb.count() > 0 and cb.is_checked():
                return True
        except Exception:
            pass

    # Strategy 3: find label element containing text, then click its checkbox
    if option_label:
        try:
            label_el = page.locator(f'label:has-text("{option_label}")').first
            if label_el.count() > 0:
                label_el.scroll_into_view_if_needed()
                label_el.click()
                return True
        except Exception:
            pass

    return False


def _result(*, label, role, value, status) -> AutomationFillFieldResult:
    return AutomationFillFieldResult(
        field_label=label,
        field_role=role,
        resolved_value=value,
        fill_status=status,
    )
