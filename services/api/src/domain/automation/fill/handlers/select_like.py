"""
Handlers for select-like / combobox fields.
"""

from __future__ import annotations

import logging

from playwright.sync_api import Page

from src.domain.automation.fill.constants import HUMAN_SELECT_TYPING_DELAY_MS
from src.domain.automation.fill.helpers import (
    combobox_value_changed,
    normalize_choice_text,
    score_choice_match,
)
from src.domain.automation.fill.locators import (
    find_field_container,
    find_textbox_in_container,
    find_toggle_button,
)
from src.domain.automation.fill.models import AutomationFillFieldResult

logger = logging.getLogger(__name__)


def fill_select_like(page: Page, field: dict, value: str | None) -> AutomationFillFieldResult:
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

    container = find_field_container(page, label)
    if container is None:
        logger.debug(f"[select_like] {label!r}: container not found")
        return _result(
            label=label,
            name=name,
            role=role,
            value=value,
            status="skipped_not_found",
        )

    textbox = find_textbox_in_container(container)
    if textbox is None:
        logger.debug(f"[select_like] {label!r}: textbox not found in container")
        return _result(
            label=label,
            name=name,
            role=role,
            value=value,
            status="skipped_not_found",
        )

    # Scroll the field into view so portaled dropdowns render within the viewport.
    try:
        container.scroll_into_view_if_needed(timeout=3000)
        page.wait_for_timeout(150)
    except Exception:
        pass

    before_value = read_combobox_value(textbox)
    logger.debug(f"[select_like] {label!r}: value={value!r} before={before_value!r}")

    toggle = find_toggle_button(container)
    if toggle is not None:
        logger.debug(f"[select_like] {label!r}: toggle found — clicking indicator")
        try:
            toggle.click()
            # Wait for options to actually render — not a fixed sleep.
            opts_visible = _wait_for_options(page, timeout=2000)
            logger.debug(f"[select_like] {label!r}: toggle path — options_visible={opts_visible}")
        except Exception as e:
            logger.debug(f"[select_like] {label!r}: toggle click error: {e}")

        # Try direct option click from the fully-open dropdown (all options visible, no
        # typing/filtering needed). This is the most reliable path for React Select.
        option = find_best_combobox_option(page, value)
        logger.debug(f"[select_like] {label!r}: toggle path — best_option_found={option is not None}")
        if option is not None:
            try:
                option.click()
                page.wait_for_timeout(500)
                applied = _selection_looks_applied(
                    page=page,
                    container=container,
                    textbox=textbox,
                    before_value=before_value,
                    target_value=value,
                )
                logger.debug(f"[select_like] {label!r}: toggle path — applied={applied}")
                if applied:
                    return _result(label=label, name=name, role=role, value=value, status="filled")
            except Exception as e:
                logger.debug(f"[select_like] {label!r}: toggle path option click error: {e}")

    status = _apply_combobox_selection(
        page=page,
        container=container,
        textbox=textbox,
        target_value=value,
        before_value=before_value,
        label=label,
    )

    return _result(
        label=label,
        name=name,
        role=role,
        value=value,
        status=status,
    )


def _apply_combobox_selection(
    *,
    page: Page,
    container,
    textbox,
    target_value: str,
    before_value: str,
    label: str | None = None,
) -> str:
    tag = f"[select_like] {label!r}" if label else "[select_like]"

    # --- Step 1: click to open dropdown, wait for options to appear ---
    try:
        textbox.click()
        page.wait_for_timeout(150)
    except Exception:
        pass

    options_visible = _wait_for_options(page, timeout=2000)
    logger.debug(f"{tag}: step1 — options_visible={options_visible}")

    # --- Step 2: direct click when full option list is visible (no typing) ---
    if options_visible:
        option = find_best_combobox_option(page, target_value)
        logger.debug(f"{tag}: step2 — best_option_found={option is not None}")
        if option is not None:
            try:
                option.click()
                page.wait_for_timeout(500)
                applied = _selection_looks_applied(
                    page=page,
                    container=container,
                    textbox=textbox,
                    before_value=before_value,
                    target_value=target_value,
                )
                logger.debug(f"{tag}: step2 — applied={applied}")
                if applied:
                    return "filled"
            except Exception as e:
                logger.debug(f"{tag}: step2 option click error: {e}")

    # --- Step 3: type to filter, wait for filtered options, then click ---
    typed = False
    try:
        # Re-focus the input in case the failed click closed the dropdown.
        textbox.click()
        page.wait_for_timeout(150)
        # Type directly — do NOT use fill() first. fill() does not fire React's
        # synthetic onChange, which breaks React Select's filter behaviour.
        textbox.type(target_value, delay=HUMAN_SELECT_TYPING_DELAY_MS)
        # Wait for options to actually render (not a fixed sleep).
        opts_after_type = _wait_for_options(page, timeout=3000)
        logger.debug(f"{tag}: step3 — typed, options_visible={opts_after_type}")
        typed = True
    except Exception as e:
        logger.debug(f"{tag}: step3 type error: {e}")
        try:
            textbox.click()
            try:
                textbox.press("Meta+a")
            except Exception:
                textbox.press("Control+a")
            textbox.press("Backspace")
            textbox.type(target_value, delay=HUMAN_SELECT_TYPING_DELAY_MS)
            _wait_for_options(page, timeout=3000)
            typed = True
        except Exception:
            typed = False

    option = find_best_combobox_option(page, target_value)
    logger.debug(f"{tag}: step3 — post-type best_option_found={option is not None}")
    if option is not None:
        try:
            option.click()
            page.wait_for_timeout(500)
        except Exception:
            try:
                option.click(force=True)
                page.wait_for_timeout(500)
            except Exception:
                pass

        applied = _selection_looks_applied(
            page=page,
            container=container,
            textbox=textbox,
            before_value=before_value,
            target_value=target_value,
        )
        logger.debug(f"{tag}: step3 post-click — applied={applied}")
        if applied:
            return "filled"

    # --- Step 4: ArrowDown + Enter last resort ---
    if typed:
        try:
            textbox.press("ArrowDown")
            page.wait_for_timeout(200)
            textbox.press("Enter")
            page.wait_for_timeout(500)

            applied = _selection_looks_applied(
                page=page,
                container=container,
                textbox=textbox,
                before_value=before_value,
                target_value=target_value,
            )
            logger.debug(f"{tag}: step4 ArrowDown+Enter — applied={applied}")
            if applied:
                return "filled"
        except Exception:
            pass

    logger.debug(f"{tag}: all steps failed → skipped_option_not_applied")
    return "skipped_option_not_applied"


def _wait_for_options(page: Page, timeout: int = 2000) -> bool:
    """Wait for dropdown options to become visible. Returns True if found."""
    for selector in ('[class*="__option"]', '[role="option"]'):
        try:
            # Use state="visible" (Playwright's official param) rather than
            # appending :visible inside the CSS string — both work but the
            # param form is more reliable across Playwright versions.
            page.wait_for_selector(selector, state="visible", timeout=timeout)
            return True
        except Exception:
            pass
    return False


def find_best_combobox_option(page: Page, value: str):
    # React Select class-based selector comes first (most specific);
    # role-based selectors are fallback for non-React-Select comboboxes.
    selectors = [
        '[class*="__option"]',
        '[role="option"]',
        '[role="listbox"] [role="option"]',
        'div[role="option"]',
        'li[role="option"]',
    ]

    seen_ids: set[int] = set()
    candidates: list[tuple[int, object, str]] = []

    for selector in selectors:
        try:
            elements = page.locator(selector)
            count = min(elements.count(), 80)

            for i in range(count):
                el = elements.nth(i)

                # Only consider options that are actually visible on screen.
                try:
                    if not el.is_visible():
                        continue
                except Exception:
                    continue

                try:
                    text = (el.inner_text() or "").strip()
                except Exception:
                    continue

                if not text:
                    continue

                # Deduplicate by text to avoid double-scoring when multiple
                # selectors match the same React Select portal options.
                text_key = hash(text.lower())
                if text_key in seen_ids:
                    continue
                seen_ids.add(text_key)

                score = score_choice_match(value, text)
                if score > 0:
                    candidates.append((score, el, text))
        except Exception:
            continue

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    best_score, best_option, _ = candidates[0]

    if best_score < 40:
        return None

    return best_option


def read_combobox_value(locator) -> str:
    candidates: list[str] = []

    try:
        value = locator.input_value()
        if value:
            candidates.append(value)
    except Exception:
        pass

    try:
        text = locator.inner_text()
        if text:
            candidates.append(text)
    except Exception:
        pass

    try:
        text = locator.text_content()
        if text:
            candidates.append(text)
    except Exception:
        pass

    try:
        aria_value = locator.get_attribute("aria-valuetext")
        if aria_value:
            candidates.append(aria_value)
    except Exception:
        pass

    try:
        aria_label = locator.get_attribute("aria-label")
        if aria_label:
            candidates.append(aria_label)
    except Exception:
        pass

    for candidate in candidates:
        normalized = (candidate or "").strip()
        if normalized:
            return normalized

    return ""


def _selection_looks_applied(*, page: Page, container, textbox, before_value: str, target_value: str) -> bool:
    target_norm = normalize_choice_text(target_value)

    # Container text is the most reliable check. For React Select the selected
    # value appears in a visible child div (e.g. .select__single-value), which IS
    # included in inner_text(). The typed-but-unconfirmed text lives in an <input>
    # whose value is NOT included in inner_text(), so this check has no false positives
    # from mid-typing states.
    try:
        container_text = (container.inner_text() or "").strip()
        if container_text:
            container_norm = normalize_choice_text(container_text)
            if target_norm and target_norm in container_norm:
                return True
    except Exception:
        pass

    # Fallback: combobox value changed to something other than what we typed.
    # Guards against the false positive where input_value() returns the typed search
    # text (React Select clears the input after a real selection, so after_norm would
    # be empty on success — not equal to target_norm on failure).
    after_value = read_combobox_value(textbox)
    after_norm = normalize_choice_text(after_value)
    if after_norm and after_norm != target_norm and combobox_value_changed(before_value, after_value):
        return True

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