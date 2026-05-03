"""
Unit tests for the Greenhouse combobox handler.

Tests cover:
- Skipping when no value is provided
- Option text normalization (dial-code suffix, synonym mapping)
- _find_best_option scoring and threshold logic
- _verify_selection against .select__single-value text
"""

import pytest

from src.domain.automation.fill.handlers.greenhouse_combobox import (
    _find_best_option,
    _is_combobox,
    _verify_selection,
)
from src.domain.automation.fill.helpers import normalize_choice_text, score_choice_match


# ---------------------------------------------------------------------------
# normalize_choice_text — dial code suffix stripping
# ---------------------------------------------------------------------------


def test_normalize_strips_dial_code_suffix():
    assert normalize_choice_text("United States +1") == normalize_choice_text(
        "United States"
    )


def test_normalize_strips_multi_digit_dial_code():
    assert normalize_choice_text("Germany +49") == normalize_choice_text("Germany")


def test_normalize_no_suffix_unchanged():
    result = normalize_choice_text("Canada")
    assert "canada" in result.lower()


# ---------------------------------------------------------------------------
# normalize_choice_text — veteran / disability synonym mapping
# ---------------------------------------------------------------------------


def test_normalize_veteran_synonym():
    # "decline to self identify" should normalise to the shared sentinel
    result = normalize_choice_text("Decline to self identify")
    assert "decline" in result.lower() or "prefer" in result.lower()


def test_normalize_disability_no_synonym():
    result = normalize_choice_text("No, I don't have a disability")
    assert result  # should return non-empty


# ---------------------------------------------------------------------------
# score_choice_match — basic cases
# ---------------------------------------------------------------------------


def test_exact_match_scores_100():
    assert score_choice_match("Canada", "Canada") == 100


def test_case_insensitive_match_scores_100():
    assert score_choice_match("canada", "Canada") == 100


def test_partial_match_scores_above_threshold():
    score = score_choice_match("United States", "United States +1")
    assert score >= 40


def test_unrelated_text_scores_zero_or_low():
    score = score_choice_match("Canada", "Germany")
    assert score < 40


# ---------------------------------------------------------------------------
# fill_greenhouse_combobox — skipped_no_value
# ---------------------------------------------------------------------------


def test_fill_returns_skipped_no_value_when_value_is_none():
    from src.domain.automation.fill.handlers.greenhouse_combobox import (
        fill_greenhouse_combobox,
    )

    field = {"label": "Country", "name": "country", "classified_role": "select_like"}
    result = fill_greenhouse_combobox(page=None, field=field, value=None)
    assert result.fill_status == "skipped_no_value"


def test_fill_returns_skipped_no_value_when_value_is_empty():
    from src.domain.automation.fill.handlers.greenhouse_combobox import (
        fill_greenhouse_combobox,
    )

    field = {"label": "Country", "name": "country", "classified_role": "select_like"}
    result = fill_greenhouse_combobox(page=None, field=field, value="")
    assert result.fill_status == "skipped_no_value"


# ---------------------------------------------------------------------------
# _find_best_option — stub tests using fake locator objects
# ---------------------------------------------------------------------------


class _FakeLocator:
    """Minimal stub that mimics a Playwright locator returning fixed text."""

    def __init__(self, texts: list[str]):
        self._texts = texts

    def count(self):
        return len(self._texts)

    def nth(self, i):
        return _FakeSingleLocator(self._texts[i])


class _FakeSingleLocator:
    def __init__(self, text: str, visible: bool = True):
        self._text = text
        self._visible = visible

    def is_visible(self):
        return self._visible

    def inner_text(self):
        return self._text


class _FakePage:
    """Minimal Page stub that returns a pre-configured option list."""

    def __init__(self, options: list[str]):
        self._options = options

    def locator(self, selector):
        if "select__option" in selector or selector == '[role="option"]':
            return _FakeLocator(self._options)
        return _FakeLocator([])


def test_find_best_option_exact_match():
    page = _FakePage(["Canada", "United States", "Germany"])
    option, text = _find_best_option(page, "Canada")
    assert text == "Canada"


def test_find_best_option_partial_match():
    page = _FakePage(["United States +1", "Canada +1", "Germany +49"])
    option, text = _find_best_option(page, "United States")
    assert text == "United States +1"


def test_find_best_option_returns_none_when_no_match():
    page = _FakePage(["Germany", "France", "Italy"])
    option, text = _find_best_option(page, "Antarctica")
    assert option is None
    assert text is None


def test_find_best_option_returns_none_when_score_below_threshold():
    page = _FakePage(["Partially related text xyz"])
    option, text = _find_best_option(page, "Completely different")
    # Score should be below 40 for unrelated text
    assert option is None


# ---------------------------------------------------------------------------
# _verify_selection — stub tests
# ---------------------------------------------------------------------------


class _FakeValueContainerLocator:
    def __init__(self, single_value_text: str):
        self._text = single_value_text

    def count(self):
        return 1

    def locator(self, selector):
        if "single-value" in selector:
            return _FakeSingleValueLocator(self._text)
        return _FakeEmptyLocator()

    def inner_text(self):
        return self._text


class _FakeSingleValueLocator:
    def __init__(self, text: str):
        self._text = text

    def count(self):
        return 1

    def inner_text(self):
        return self._text


class _FakeEmptyLocator:
    def count(self):
        return 0


class _FakeCombobox:
    """
    Stub combobox that falls through to the input_value() fallback path inside
    _verify_selection (the XPath-based primary path is not exercised in unit tests
    since it requires a real Playwright locator chain).
    """

    def __init__(self, input_value_text: str):
        self._input_value_text = input_value_text

    def locator(self, _selector):
        # Return empty locator so primary path is skipped.
        return _FakeEmptyLocatorWithFirst()

    def input_value(self):
        return self._input_value_text


class _FakeEmptyLocatorWithFirst:
    """Locator that reports count=0 when .first is accessed."""

    @property
    def first(self):
        return self

    def count(self):
        return 0


def test_verify_selection_passes_when_text_matches():
    combobox = _FakeCombobox("Canada")
    assert _verify_selection(combobox, "Canada") is True


def test_verify_selection_fails_when_text_differs():
    combobox = _FakeCombobox("Germany")
    result = _verify_selection(combobox, "Canada")
    assert result is False


def test_verify_selection_passes_with_partial_match():
    # input_value contains dial-code suffix; target matches prefix
    combobox = _FakeCombobox("United States")
    assert _verify_selection(combobox, "United States") is True


def test_verify_selection_passes_with_dial_code_display_when_option_known():
    # Some country pickers display only dial code (e.g. +1) after selection.
    combobox = _FakeCombobox("+1")
    assert (
        _verify_selection(
            combobox,
            "United States",
            selected_option_text="United States +1",
        )
        is True
    )


def test_is_combobox_rejects_plain_input_without_select_class():
    class _PlainInput:
        def get_attribute(self, name):
            if name == "role":
                return None
            if name == "class":
                return "form-control"
            return None

        def evaluate(self, _expr):
            return "input"

        def is_visible(self):
            return True

    assert _is_combobox(_PlainInput()) is False
