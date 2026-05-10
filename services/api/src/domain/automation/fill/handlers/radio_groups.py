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

    best_option, best_index = _find_best_radio_option(options, value)
    if not best_option:
        best_option = _fallback_binary_option(value)
        best_index = -1

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
            field_label=label,
            name=name,
            option_label=option_label,
            option_value=option_value,
            option_index=best_index,
        )

    return _result(
        label=label,
        name=name,
        role=role,
        value=value,
        status="filled" if clicked else "skipped_option_not_applied",
    )


def _find_best_radio_option(options: list[dict], target_value: str) -> tuple[dict | None, int]:
    best_option = None
    best_score = -1
    best_index = -1

    for i, option in enumerate(options):
        label = option.get("label") or ""
        value = option.get("value") or ""
        score = max(
            score_choice_match(target_value, label),
            score_choice_match(target_value, value),
        )

        if score > best_score:
            best_score = score
            best_option = option
            best_index = i

    if best_score < 50:
        return None, -1

    return best_option, best_index


def _fallback_binary_option(target_value: str) -> dict | None:
    normalized = (target_value or "").strip().lower()
    if normalized in {"yes", "y", "true"}:
        return {"label": "Yes", "value": "yes"}
    if normalized in {"no", "n", "false"}:
        return {"label": "No", "value": "no"}
    return None


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


def _click_radio_option(
    page,
    *,
    field_label: str | None,
    name: str | None,
    option_label: str | None,
    option_value: str | None,
    option_index: int = -1,
) -> bool:
    if name and option_index >= 0:
        try:
            radio = page.locator(f'input[type="radio"][name="{name}"]').nth(option_index)
            if _activate_radio(page, radio):
                return True
        except Exception:
            pass

    # Strategy 2: unique value-based selector (works for non-Ashby platforms
    # where each option has a distinct value attribute).
    if name and option_value:
        try:
            group = page.locator(f'input[type="radio"][name="{name}"][value="{option_value}"]')
            if group.count() == 1 and _activate_radio(page, group.first):
                return True
        except Exception:
            pass

    # Strategy 3: match by label text within the named radio group.
    if name and option_label:
        try:
            radios = page.locator(f'input[type="radio"][name="{name}"]')
            count = min(radios.count(), 8)
            for index in range(count):
                radio = radios.nth(index)
                radio_id = radio.get_attribute("id")
                if not radio_id:
                    continue
                label_locator = page.locator(f'label[for="{radio_id}"]')
                if label_locator.count() == 0:
                    continue
                text = (label_locator.first.inner_text() or "").strip().lower()
                if text == option_label.strip().lower() and _activate_radio(page, radio):
                    return True
        except Exception:
            pass

    # Strategy 4: scope by the question label text and click the matching option.
    if field_label and option_label:
        try:
            scoped = page.locator(
                f'div:has-text("{field_label}"):has(label:text-is("{option_label}"))'
            ).last
            if scoped.count() > 0:
                target_label = scoped.locator(f'label:text-is("{option_label}")').first
                if target_label.count() > 0:
                    target_label.scroll_into_view_if_needed()
                    target_label.click()
                    return True
        except Exception:
            pass

    # Strategy 5: page-wide label fallback — used when name is absent.
    if option_label:
        try:
            locator = page.get_by_label(option_label, exact=False).first
            if locator.count() > 0:
                locator.check(force=True)
                return True
        except Exception:
            pass

        try:
            text_locator = page.get_by_text(option_label, exact=True).first
            if text_locator.count() > 0:
                text_locator.click()
                return True
        except Exception:
            pass

    return False


def _activate_radio(page, radio) -> bool:
    try:
        radio_id = radio.get_attribute("id")
        if radio_id:
            lbl = page.locator(f'label[for="{radio_id}"]')
            if lbl.count() > 0:
                lbl.scroll_into_view_if_needed()
                lbl.click()
                return True
    except Exception:
        pass

    try:
        parent_label = radio.locator('xpath=ancestor::label[1]').first
        if parent_label.count() > 0:
            parent_label.scroll_into_view_if_needed()
            parent_label.click()
            return True
    except Exception:
        pass

    try:
        radio.check(force=True)
        return True
    except Exception:
        pass

    try:
        radio.dispatch_event("click")
        radio.dispatch_event("input")
        radio.dispatch_event("change")
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