"""
Locator helpers for automation fill flows.
"""

from __future__ import annotations

import re

from playwright.sync_api import Page

# Trailing characters that ATS platforms append to labels but that are not
# part of the element's actual accessible name (e.g. "First Name *", "Email *").
_LABEL_SUFFIX_RE = re.compile(r"[\s*\u2009\u200b]+$")


def _clean_label(label: str | None) -> str | None:
    """Strip required-field markers and excess whitespace from a label string."""
    if not label:
        return label
    return _LABEL_SUFFIX_RE.sub("", label).strip() or label.strip()


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

        # Partial-name fallback: e.g. name="applicant[first_name]" — try the
        # last bracket segment as a contains match.
        try:
            bracket_match = re.search(r"\[([^\[\]]+)\]$", name)
            if bracket_match:
                inner = bracket_match.group(1)
                locator = page.locator(f'[name*="{inner}"]').first
                if locator.count() > 0:
                    return locator
        except Exception:
            pass

    clean = _clean_label(label)

    for lbl in _label_variants(label, clean):
        # get_by_label resolves aria-labelledby, <label for="">, and wrapped labels.
        try:
            locator = page.get_by_label(lbl, exact=False).first
            if locator.count() > 0:
                return locator
        except Exception:
            pass

        # Explicit aria-label attribute match.
        try:
            safe = lbl.replace('"', '\\"')
            locator = page.locator(f'[aria-label="{safe}"]').first
            if locator.count() > 0:
                return locator
        except Exception:
            pass

        # id-based lookup: find a <label> whose text matches, read its `for`
        # attribute, then target the element with that id.
        try:
            safe = lbl.replace('"', '\\"')
            locator = page.locator(
                f'xpath=//label[normalize-space(.)="{safe}"]/following::input[1] | '
                f'xpath=//label[normalize-space(.)="{safe}"]/following::select[1] | '
                f'xpath=//label[normalize-space(.)="{safe}"]/following::textarea[1]'
            ).first
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


def _label_variants(raw: str | None, clean: str | None) -> list[str]:
    """Return unique non-empty label variants to try, clean first."""
    seen: list[str] = []
    for v in (clean, raw):
        if v and v not in seen:
            seen.append(v)
    return seen


def find_field_container(page: Page, label: str | None):
    if not label:
        return None

    # Use the cleaned label (no asterisks) so XPath contains() matches reliably.
    clean = _clean_label(label) or label

    for lbl in _label_variants(clean, label):
        safe = lbl.replace('"', '\\"')
        selectors = [
            f'xpath=//label[contains(normalize-space(.), "{safe}")]/ancestor::*[self::div or self::fieldset][1]',
            f'xpath=//*[self::legend or self::label or self::div or self::span][contains(normalize-space(.), "{safe}")]/ancestor::*[self::div or self::fieldset][1]',
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