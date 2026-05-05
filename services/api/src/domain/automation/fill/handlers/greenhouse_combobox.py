"""
Handler for Greenhouse-specific combobox fields.

Greenhouse forms use a React Select variant where combobox inputs have an
`aria-labelledby` attribute pointing to a sibling label, and the flyout is
opened via a `button[aria-label="Toggle flyout"]` element within the
`.select__control` container.  Options render inside a `.select__menu-list`
with `class*="select__option"` and `role="option"`.

This handler targets that structure directly instead of delegating to the
generic select_like approach, which struggles with Greenhouse's specific DOM
layout and verification behaviour.
"""

from __future__ import annotations

import logging
import re
import time

from playwright.sync_api import Page

from src.domain.automation.fill.helpers import (
    normalize_choice_text,
    score_choice_match,
)
from src.domain.automation.fill.models import AutomationFillFieldResult

logger = logging.getLogger(__name__)

_HUMAN_COMBOBOX_TYPING_DELAY_MS = 75

# Selectors used to wait for / collect dropdown options.
# li[role="option"] is listed first — it's the most specific Greenhouse selector
# per community guidance (click input → fill to filter → click li[role="option"]).
_OPTION_SELECTORS = [
    'li[role="option"]',
    '[class*="select__option"]',
    '[role="option"]',
    '.iti__country-list .iti__country',
    '.iti__country',
]

# Selectors tried in order to detect a search input inside the flyout.
_SEARCH_INPUT_SELECTORS = [
    'input[aria-label="Search"]',
    '[class*="iti__search"] input',
    '[class*="search-input"] input',
    '.select__menu input[type="text"]',
]


def fill_greenhouse_combobox(
    page: Page, field: dict, value: str | None
) -> AutomationFillFieldResult:
    label = field.get("label")
    name = field.get("name")
    role = field.get("classified_role", "select_like")

    if not value:
        return _result(
            label=label,
            name=name,
            role=role,
            value=value,
            status="skipped_no_value",
        )

    # --- Locate the combobox input ---
    combobox = _locate_combobox(page, label)
    if combobox is None:
        logger.debug(f"[gh_combobox] {label!r}: combobox not found")
        return _result(
            label=label,
            name=name,
            role=role,
            value=value,
            status="skipped_not_found",
        )

    try:
        combobox.scroll_into_view_if_needed(timeout=3000)
        page.wait_for_timeout(150)
    except Exception:
        pass

    # --- Open the dropdown: click the .select__control container (the full-width
    #     clickable area). The React Select input itself is typically only a few px
    #     wide so clicking it directly often misses. Fall back to the toggle button
    #     if the control click doesn't open the menu. ---
    logger.debug(f"[gh_combobox] {label!r}: clicking select__control to open menu")
    _click_control(page, combobox)

    # --- Wait for dropdown options to appear after input click ---
    menu_visible = _wait_for_options(page, timeout=1500)
    logger.debug(f"[gh_combobox] {label!r}: menu_visible after input click={menu_visible}")

    if not menu_visible:
        # Fallback: try the Toggle flyout button.
        toggle = _find_toggle(combobox)
        if toggle is not None:
            logger.debug(f"[gh_combobox] {label!r}: control click didn't open menu, trying toggle button")
            try:
                toggle.click()
                page.wait_for_timeout(200)
            except Exception as exc:
                logger.debug(f"[gh_combobox] {label!r}: toggle click error: {exc}")
            menu_visible = _wait_for_options(page, timeout=1500)
            logger.debug(f"[gh_combobox] {label!r}: menu_visible after toggle={menu_visible}")

    # --- Type value into combobox input to filter options (React Select live filter) ---
    _try_search(page, combobox, value)

    # --- Find and click the best matching option ---
    option, option_text = _find_best_option(page, value)
    logger.debug(
        f"[gh_combobox] {label!r}: best_option_text={option_text!r} found={option is not None}"
    )

    if option is None:
        logger.debug(f"[gh_combobox] {label!r}: no matching option for {value!r}")

        # Stealth/runtime differences can occasionally prevent flyouts from
        # rendering options. As a last resort, attempt direct text entry.
        if _fallback_type_value(page, combobox, value):
            logger.debug(f"[gh_combobox] {label!r}: filled via text fallback")
            return _result(
                label=label,
                name=name,
                role=role,
                value=value,
                status="filled",
            )

        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        return _result(
            label=label,
            name=name,
            role=role,
            value=value,
            status="skipped_option_not_found",
        )

    try:
        option.click()
        page.wait_for_timeout(500)
    except Exception as exc:
        logger.debug(f"[gh_combobox] {label!r}: option click error: {exc}")
        try:
            option.click(force=True)
            page.wait_for_timeout(500)
        except Exception:
            return _result(
                label=label,
                name=name,
                role=role,
                value=value,
                status="error",
            )

    # --- Verify the selection was applied ---
    if _verify_selection(combobox, value, selected_option_text=option_text):
        logger.debug(f"[gh_combobox] {label!r}: filled with {value!r}")
        return _result(
            label=label,
            name=name,
            role=role,
            value=value,
            status="filled",
        )

    logger.debug(f"[gh_combobox] {label!r}: option clicked but not verified for {value!r}")

    if _fallback_type_value(page, combobox, value):
        logger.debug(f"[gh_combobox] {label!r}: recovered via text fallback")
        return _result(
            label=label,
            name=name,
            role=role,
            value=value,
            status="filled",
        )

    return _result(
        label=label,
        name=name,
        role=role,
        value=value,
        status="skipped_option_not_applied",
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _locate_combobox(page: Page, label: str | None):
    """
    Find the Greenhouse combobox input by resolving the field label.

    Greenhouse labels use <label for="<id>"> pointing to
    <input role="combobox" id="<id>">.  Playwright's get_by_label resolves
    both `for` and `aria-labelledby` associations.
    """
    if not label:
        return None

    # Strip the required-field asterisk suffix so label matching works.
    clean = label.rstrip("* \u2009\u200b").strip()

    for lbl in _label_variants(clean, label):
        # get_by_label resolves for/aria-labelledby — returns the associated input.
        try:
            loc = page.get_by_label(lbl, exact=False).first
            if loc.count() > 0 and _is_combobox(loc):
                return loc
        except Exception:
            pass

        # Explicit aria-labelledby fallback: find a label with matching text,
        # then locate the combobox with that label's id as its aria-labelledby.
        try:
            safe = lbl.replace('"', '\\"')
            label_els = page.locator(f'label:has-text("{safe}")')
            n = min(label_els.count(), 5)
            for i in range(n):
                label_el = label_els.nth(i)
                lbl_id = label_el.get_attribute("id")
                if lbl_id:
                    cb = page.locator(
                        f'[role="combobox"][aria-labelledby="{lbl_id}"]'
                    ).first
                    if cb.count() > 0:
                        return cb
        except Exception:
            pass

    return None


def _is_combobox(locator) -> bool:
    try:
        role = locator.get_attribute("role")
        if role == "combobox":
            try:
                return locator.is_visible()
            except Exception:
                return True
        tag = locator.evaluate("el => el.tagName.toLowerCase()")
        if tag != "input":
            return False

        # Greenhouse combobox inputs use this class and are interactable.
        class_name = (locator.get_attribute("class") or "").lower()
        if "select__input" not in class_name:
            return False
        try:
            return locator.is_visible()
        except Exception:
            return True
    except Exception:
        return False


def _label_variants(clean: str | None, raw: str | None) -> list[str]:
    seen: list[str] = []
    for v in (clean, raw):
        if v and v not in seen:
            seen.append(v)
    return seen


def _click_control(page: Page, combobox) -> None:
    """
    Click the .select__control ancestor (the full-width visible container).

    The React Select input inside the control is typically only a few pixels
    wide; clicking it directly often misses.  Clicking the parent control
    element reliably triggers the dropdown open event.
    """
    try:
        control = combobox.locator(
            "xpath=ancestor::div[contains(@class,'select__control')][1]"
        ).first
        if control.count() > 0:
            control.click()
            page.wait_for_timeout(300)
            return
    except Exception:
        pass
    # Last resort: click the combobox input directly.
    try:
        combobox.click()
        page.wait_for_timeout(300)
    except Exception:
        pass


def _find_toggle(combobox):
    """
    Locate the Toggle flyout button that lives inside the same
    .select__control element as the combobox input.
    """
    try:
        # Walk up to the enclosing .select__control and find the button within it.
        control = combobox.locator(
            "xpath=ancestor::div[contains(@class,'select__control')][1]"
        ).first
        if control.count() > 0:
            btn = control.locator('button[aria-label="Toggle flyout"]').first
            if btn.count() > 0:
                return btn
            # Fallback: any toggle-like button in the indicators area.
            btn = control.locator(
                'button[aria-label*="Toggle"], [class*="__dropdown-indicator"]'
            ).first
            if btn.count() > 0:
                return btn
    except Exception:
        pass

    return None


def _wait_for_options(page: Page, timeout: int = 2000) -> bool:
    """Wait until dropdown options are visible in the DOM.

    The ``timeout`` budget is shared across all candidate selectors so that
    a single call never takes longer than ``timeout`` milliseconds total.
    """
    deadline = time.monotonic() + timeout / 1000.0
    per_ms = max(150, timeout // len(_OPTION_SELECTORS))
    for selector in _OPTION_SELECTORS:
        remaining = int((deadline - time.monotonic()) * 1000)
        if remaining <= 0:
            break
        try:
            page.wait_for_selector(
                selector,
                state="visible",
                timeout=min(per_ms, remaining),
            )
            return True
        except Exception:
            pass
    return False


def _try_search(page: Page, combobox, value: str) -> None:
    """
    Filter the open option list by typing the target value.

    Primary approach (per Playwright community guidance for Greenhouse React Select):
    type directly into the combobox input — React Select filters the list live.

    Falls back to dedicated search inputs (e.g. country list search boxes).
    """
    # Primary: type into the combobox input itself to trigger React Select filtering.
    try:
        combobox.click()
        try:
            combobox.press("Meta+a")
        except Exception:
            combobox.press("Control+a")
        combobox.press("Backspace")
        combobox.type(value, delay=_HUMAN_COMBOBOX_TYPING_DELAY_MS)
        page.wait_for_timeout(300)
        # Check if options are now visible after filtering.
        if _wait_for_options(page, timeout=1000):
            return
    except Exception:
        pass

    # Fallback: dedicated search input inside the flyout (e.g. country list).
    for sel in _SEARCH_INPUT_SELECTORS:
        try:
            search = page.locator(sel).first
            if search.count() > 0 and search.is_visible():
                search.click()
                search.fill("")
                search.type(value, delay=_HUMAN_COMBOBOX_TYPING_DELAY_MS)
                page.wait_for_timeout(400)
                return
        except Exception:
            continue


def _find_best_option(page: Page, value: str) -> tuple[object | None, str | None]:
    """
    Collect all visible options from the open dropdown, score each against the
    target value, and return the highest-scoring candidate above the threshold.
    """
    seen: set[int] = set()
    candidates: list[tuple[int, object, str]] = []

    for selector in _OPTION_SELECTORS:
        try:
            elements = page.locator(selector)
            count = min(elements.count(), 100)
            for i in range(count):
                el = elements.nth(i)
                # Some Greenhouse country list items can report non-visible
                # even while rendered. We still attempt text extraction and rely
                # on scoring to pick the best candidate.
                try:
                    _ = el.is_visible()
                except Exception:
                    pass

                try:
                    text = (el.inner_text() or "").strip()
                except Exception:
                    continue

                if not text:
                    continue

                key = hash(text.lower())
                if key in seen:
                    continue
                seen.add(key)

                score = score_choice_match(value, text)
                if score > 0:
                    candidates.append((score, el, text))
        except Exception:
            continue

    if not candidates:
        return None, None

    candidates.sort(key=lambda x: x[0], reverse=True)
    best_score, best_option, best_text = candidates[0]

    if best_score < 40:
        return None, None

    return best_option, best_text


def _verify_selection(
    combobox,
    value: str,
    *,
    selected_option_text: str | None = None,
) -> bool:
    """
    Confirm the selected value matches the target by reading the
    .select__single-value text that React Select renders after a selection.
    Falls back to the combobox's current input value.
    """
    target_norm = normalize_choice_text(value)
    selected_option_norm = normalize_choice_text(selected_option_text)

    # Primary: read .select__single-value inside the value container.
    try:
        value_container = combobox.locator(
            "xpath=ancestor::div[contains(@class,'select__value-container')][1]"
        ).first
        if value_container.count() > 0:
            single_value = value_container.locator(
                '[class*="select__single-value"]'
            ).first
            if single_value.count() > 0:
                text = (single_value.inner_text() or "").strip()
                if text:
                    if selected_option_text and _dial_code_matches(text, selected_option_text):
                        return True
                    norm = normalize_choice_text(text)
                    if target_norm and (
                        target_norm == norm
                        or target_norm in norm
                        or norm in target_norm
                    ):
                        return True
                    if selected_option_norm and norm and (
                        norm == selected_option_norm
                        or norm in selected_option_norm
                        or selected_option_norm in norm
                    ):
                        return True
    except Exception:
        pass

    # Fallback: combobox input_value (may hold selected text in some configurations).
    try:
        val = combobox.input_value()
        if val:
            if selected_option_text and _dial_code_matches(val, selected_option_text):
                return True
            norm = normalize_choice_text(val)
            if target_norm and (target_norm in norm or norm in target_norm):
                return True
            if selected_option_norm and norm and (
                norm in selected_option_norm or selected_option_norm in norm
            ):
                return True
    except Exception:
        pass

    return False


def _dial_code_matches(display_text: str | None, option_text: str | None) -> bool:
    """Return True when displayed text and selected option share the same dial code."""
    if not display_text or not option_text:
        return False

    display_codes = re.findall(r"\+?\d{1,4}", display_text)
    option_codes = re.findall(r"\+?\d{1,4}", option_text)
    if not display_codes or not option_codes:
        return False

    display_code = display_codes[-1].lstrip("+")
    option_code = option_codes[-1].lstrip("+")
    return bool(display_code and option_code and display_code == option_code)


def _fallback_type_value(page: Page, combobox, value: str) -> bool:
    """
    Last-resort fallback when no options are discoverable.

    Types the resolved value directly and accepts it with Enter/Tab. This helps
    with environments where Greenhouse flyout options fail to render while the
    combobox still accepts freeform input.
    """
    target_norm = normalize_choice_text(value)
    if not target_norm:
        return False

    try:
        combobox.click()
        try:
            combobox.press("Meta+a")
        except Exception:
            combobox.press("Control+a")
        combobox.press("Backspace")
        combobox.type(value, delay=_HUMAN_COMBOBOX_TYPING_DELAY_MS)
        page.wait_for_timeout(150)
        try:
            page.keyboard.press("Enter")
        except Exception:
            pass
        try:
            page.keyboard.press("Tab")
        except Exception:
            pass
        page.wait_for_timeout(250)

        typed = combobox.input_value() or ""
        typed_norm = normalize_choice_text(typed)
        if typed_norm and (
            typed_norm == target_norm
            or typed_norm in target_norm
            or target_norm in typed_norm
        ):
            return True
    except Exception:
        return False

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
