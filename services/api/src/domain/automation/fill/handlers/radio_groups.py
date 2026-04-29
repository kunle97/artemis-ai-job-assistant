"""
Handlers for radio group fields.
"""

from __future__ import annotations

from src.domain.automation.fill.helpers import score_choice_match
from src.domain.automation.fill.models import AutomationFillFieldResult


def fill_radio_group(page, field: dict, value: str | None) -> AutomationFillFieldResult:
    label = field.get("label")
    name = field.get("name")
    role = field.get("classified_role", "radio_group")
    input_subtype = field.get("input_subtype")
    options = field.get("options", []) or []

    if not value:
        return _result(
            label=label,
            name=name,
            role=role,
            value=None,
            status="skipped_no_value",
        )

    best_option = _find_best_radio_option(options, value)
    if not best_option:
        return _result(
            label=label,
            name=name,
            role=role,
            value=value,
            status="skipped_option_not_found",
        )

    option_label = best_option.get("label")
    option_value = best_option.get("value")

    if input_subtype == "pill":
        clicked = _click_pill_option(
            page=page,
            field_label=label,
            option_label=option_label,
        )
    else:
        clicked = _click_radio_option(
            page=page,
            name=name,
            option_label=option_label,
            option_value=option_value,
        )

    return _result(
        label=label,
        name=name,
        role=role,
        value=value,
        status="filled" if clicked else "skipped_option_not_applied",
    )


def _find_best_radio_option(options: list[dict], target_value: str) -> dict | None:
    best_option = None
    best_score = -1

    for option in options:
        label = option.get("label") or ""
        value = option.get("value") or ""
        score = max(
            score_choice_match(target_value, label),
            score_choice_match(target_value, value),
        )

        if score > best_score:
            best_score = score
            best_option = option

    if best_score < 50:
        return None

    return best_option


def _click_pill_option(page, *, field_label: str | None, option_label: str | None) -> bool:
    """Click a Yes/No pill button on Ashby-style forms.

    Scopes the click to the container that holds both the question label text
    and the target button, so we don't accidentally click the wrong group when
    multiple pill questions are present on the page.
    """
    if not option_label:
        return False

    if field_label:
        try:
            # Find a <div> that contains both the question text and the target
            # button. Using .last picks the deepest/most-specific match.
            scoped = page.locator(
                f'div:has-text("{field_label}"):has(button:text-is("{option_label}"))'
            ).last
            if scoped.count() > 0:
                btn = scoped.locator(f'button:text-is("{option_label}")').first
                if btn.count() > 0:
                    btn.scroll_into_view_if_needed()
                    btn.click()
                    return True
        except Exception:
            pass

    try:
        # Fallback: first visible button with matching text on the page.
        btn = page.locator(f'button:text-is("{option_label}")').first
        if btn.count() > 0:
            btn.scroll_into_view_if_needed()
            btn.click()
            return True
    except Exception:
        pass

    return False


def _click_radio_option(page, *, name: str | None, option_label: str | None, option_value: str | None) -> bool:
    if name and option_value:
        try:
            locator = page.locator(
                f'input[type="radio"][name="{name}"][value="{option_value}"]'
            ).first
            if locator.count() > 0:
                locator.check(force=True)
                return True
        except Exception:
            pass

    if option_label:
        try:
            locator = page.get_by_label(option_label, exact=False).first
            if locator.count() > 0:
                locator.check(force=True)
                return True
        except Exception:
            pass

        try:
            text_locator = page.get_by_text(option_label, exact=False).first
            if text_locator.count() > 0:
                text_locator.click()
                return True
        except Exception:
            pass

    return False


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