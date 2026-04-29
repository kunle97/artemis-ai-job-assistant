"""
Locator helpers for automation fill flows.
"""

from __future__ import annotations

from playwright.sync_api import Page


def locate_field(
    page: Page,
    *,
    name: str | None,
    label: str | None,
    placeholder: str | None,
    input_subtype: str | None = None,
):
    # For tel fields use input[type="tel"] — avoids filling the flag/country-code
    # dropdown that Greenhouse renders alongside the phone number input.
    if input_subtype == "tel":
        try:
            locator = page.locator('input[type="tel"]').first
            if locator.count() > 0:
                return locator
        except Exception:
            pass
    if name:
        try:
            locator = page.locator(f'[name="{name}"]').first
            if locator.count() > 0:
                return locator
        except Exception:
            pass

    if label:
        try:
            locator = page.get_by_label(label, exact=False).first
            if locator.count() > 0:
                return locator
        except Exception:
            pass

        try:
            locator = page.locator(f'[aria-label="{label}"]').first
            if locator.count() > 0:
                return locator
        except Exception:
            pass

    if placeholder:
        try:
            locator = page.get_by_placeholder(placeholder, exact=False).first
            if locator.count() > 0:
                return locator
        except Exception:
            pass

    return None


def find_field_container(page: Page, label: str | None):
    if not label:
        return None

    safe_label = label.replace('"', '\\"')

    selectors = [
        f'xpath=//label[contains(normalize-space(.), "{safe_label}")]/ancestor::*[self::div or self::fieldset][1]',
        f'xpath=//*[self::legend or self::label or self::div or self::span][contains(normalize-space(.), "{safe_label}")]/ancestor::*[self::div or self::fieldset][1]',
    ]

    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if locator.count() > 0:
                return locator
        except Exception:
            continue

    return None


def find_toggle_button(container):
    button_selectors = [
        'button[aria-label*="Toggle"]',
        'button[aria-label*="toggle"]',
        'button:has-text("Toggle flyout")',
    ]

    for selector in button_selectors:
        try:
            locator = container.locator(selector).first
            if locator.count() > 0:
                return locator
        except Exception:
            continue

    try:
        buttons = container.locator("button")
        count = buttons.count()

        for i in range(count):
            btn = buttons.nth(i)
            text = (btn.inner_text() or "").strip().lower()
            aria = (btn.get_attribute("aria-label") or "").strip().lower()

            if (
                "toggle" in text
                or "toggle" in aria
                or "flyout" in text
                or "flyout" in aria
            ):
                return btn
    except Exception:
        pass

    return None


def find_textbox_in_container(container):
    selectors = [
        '[role="combobox"]',
        'input[type="text"]',
        'input:not([type])',
    ]

    for selector in selectors:
        try:
            locator = container.locator(selector).first
            if locator.count() > 0:
                return locator
        except Exception:
            continue

    return None