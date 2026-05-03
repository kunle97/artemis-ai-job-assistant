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
        input_subtype=field.get("input_subtype"),
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


def fill_autocomplete_location_field(page, field: dict, value: str | None) -> AutomationFillFieldResult:
    """Fill a location autocomplete field (e.g. Lever's Google Places input).

    Strategy (each step falls through to the next on failure):
    1. Type slowly and wait for a Google Places .pac-item suggestion to appear,
       then click it — this is the cleanest confirmation.
    2. Keyboard ArrowDown + Enter to accept the first highlighted suggestion.
    3. Verify the field still has a value after step 1/2. If Lever's React layer
       cleared it (no Places suggestion confirmed), inject the value directly via
       the React native input setter and dispatch 'input'+'change' events so the
       controlled component accepts it without clearing on blur.
    """
    label = field.get("label")
    name = field.get("name")
    placeholder = field.get("placeholder")
    role = field.get("classified_role", "location")

    if not value:
        return _result(label=label, name=name, role=role, value=None, status="skipped_no_value")

    locator = locate_field(page, name=name, label=label, placeholder=placeholder)
    if locator is None:
        return _result(label=label, name=name, role=role, value=value, status="skipped_not_found")

    try:
        locator.click()
        locator.fill("")
        locator.type(value, delay=80)
        page.wait_for_timeout(2000)

        # Step 1: click first Google Places .pac-item suggestion
        try:
            first_suggestion = page.locator(".pac-item").first
            if first_suggestion.is_visible(timeout=2000):
                first_suggestion.click()
                page.wait_for_timeout(300)
        except Exception:
            pass

        # Step 2: keyboard fallback if suggestion didn't appear
        try:
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(300)
            page.keyboard.press("Enter")
            page.wait_for_timeout(400)
        except Exception:
            pass

        # Step 3: verify the field still holds a value; if React cleared it,
        # inject via the native input setter so controlled components accept it.
        try:
            current_val = locator.input_value(timeout=500)
        except Exception:
            current_val = ""

        if not current_val:
            try:
                locator.evaluate(
                    """(el, val) => {
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, 'value'
                        ).set;
                        nativeInputValueSetter.call(el, val);
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    }""",
                    value,
                )
                page.wait_for_timeout(200)
            except Exception:
                pass

        return _result(label=label, name=name, role=role, value=value, status="filled")
    except Exception:
        return _result(label=label, name=name, role=role, value=value, status="error")


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