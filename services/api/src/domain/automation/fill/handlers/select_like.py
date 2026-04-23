"""
Handlers for select-like / combobox fields.
"""

from __future__ import annotations

from playwright.sync_api import Page

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
        return _result(
            label=label,
            name=name,
            role=role,
            value=value,
            status="skipped_not_found",
        )

    textbox = find_textbox_in_container(container)
    if textbox is None:
        return _result(
            label=label,
            name=name,
            role=role,
            value=value,
            status="skipped_not_found",
        )

    before_value = read_combobox_value(textbox)

    toggle = find_toggle_button(container)
    if toggle is not None:
        try:
            toggle.click()
            page.wait_for_timeout(300)
        except Exception:
            pass

    status = _apply_combobox_selection(
        page=page,
        container=container,
        textbox=textbox,
        target_value=value,
        before_value=before_value,
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
) -> str:
    try:
        textbox.click()
        page.wait_for_timeout(150)
    except Exception:
        pass

    typed = False

    try:
        textbox.fill("")
        page.wait_for_timeout(100)
        textbox.type(target_value, delay=50)
        page.wait_for_timeout(900)
        typed = True
    except Exception:
        try:
            textbox.click()
            try:
                textbox.press("Meta+a")
            except Exception:
                textbox.press("Control+a")
            textbox.press("Backspace")
            textbox.type(target_value, delay=50)
            page.wait_for_timeout(900)
            typed = True
        except Exception:
            typed = False

    option = find_best_combobox_option(page, target_value)
    if option is not None:
        try:
            option.click()
            page.wait_for_timeout(400)
        except Exception:
            try:
                option.click(force=True)
                page.wait_for_timeout(400)
            except Exception:
                pass

        if _selection_looks_applied(
            page=page,
            container=container,
            textbox=textbox,
            before_value=before_value,
            target_value=target_value,
        ):
            return "filled"

    if typed:
        try:
            textbox.press("ArrowDown")
            page.wait_for_timeout(200)
            textbox.press("Enter")
            page.wait_for_timeout(450)

            if _selection_looks_applied(
                page=page,
                container=container,
                textbox=textbox,
                before_value=before_value,
                target_value=target_value,
            ):
                return "filled"
        except Exception:
            pass

    return "skipped_option_not_applied"


def find_best_combobox_option(page: Page, value: str):
    selectors = [
        '[role="option"]',
        '[role="listbox"] [role="option"]',
        'div[role="option"]',
        'li',
        'ul li',
    ]

    candidates: list[tuple[int, object, str]] = []

    for selector in selectors:
        try:
            elements = page.locator(selector)
            count = min(elements.count(), 80)

            for i in range(count):
                el = elements.nth(i)

                try:
                    text = (el.inner_text() or "").strip()
                except Exception:
                    continue

                if not text:
                    continue

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
    after_value = read_combobox_value(textbox)
    if combobox_value_changed(before_value, after_value):
        return True

    target_norm = normalize_choice_text(target_value)

    try:
        container_text = (container.inner_text() or "").strip()
    except Exception:
        container_text = ""

    if container_text:
        container_norm = normalize_choice_text(container_text)
        if target_norm and target_norm in container_norm:
            return True

    try:
        page_text = (page.locator("body").inner_text() or "").strip()
    except Exception:
        page_text = ""

    if page_text:
        page_norm = normalize_choice_text(page_text)
        if target_norm and target_norm in page_norm:
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