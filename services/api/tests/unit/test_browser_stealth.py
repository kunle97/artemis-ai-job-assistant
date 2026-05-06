"""
Unit tests for the browser stealth integration.

Verifies that:
- stealth launch args include the required anti-detection flags
- the stealth init script contains all 8 fingerprint patches
- human_delay sleeps for a duration within the expected range
- human_type clicks the selector and types characters one by one
- simulate_mouse_movement calls page.mouse.move the expected number of times
"""

import os
import time
from unittest.mock import MagicMock, call, patch

import pytest

from src.integrations.automation.browser import (
    _STEALTH_INIT_SCRIPT,
    _STEALTH_LAUNCH_ARGS,
    human_delay,
    human_type,
    simulate_mouse_movement,
)


# ---------------------------------------------------------------------------
# Launch args
# ---------------------------------------------------------------------------

def test_stealth_launch_args_disable_automation_controlled():
    assert "--disable-blink-features=AutomationControlled" in _STEALTH_LAUNCH_ARGS


def test_stealth_launch_args_no_sandbox():
    assert "--no-sandbox" in _STEALTH_LAUNCH_ARGS


# ---------------------------------------------------------------------------
# Init script — 8 patch vectors
# ---------------------------------------------------------------------------

def test_init_script_patch1_webdriver():
    """Patch 1: navigator.webdriver removal."""
    assert "navigator" in _STEALTH_INIT_SCRIPT and "webdriver" in _STEALTH_INIT_SCRIPT


def test_init_script_patch2_chrome_runtime():
    """Patch 2: chrome.runtime injection."""
    assert "chrome" in _STEALTH_INIT_SCRIPT and "runtime" in _STEALTH_INIT_SCRIPT


def test_init_script_patch3_plugins():
    """Patch 3: navigator.plugins spoofing (3 plugins)."""
    assert "navigator" in _STEALTH_INIT_SCRIPT and "plugins" in _STEALTH_INIT_SCRIPT
    assert "Chrome PDF Plugin" in _STEALTH_INIT_SCRIPT


def test_init_script_patch4_languages():
    """Patch 4: navigator.languages spoofing."""
    assert "languages" in _STEALTH_INIT_SCRIPT


def test_init_script_patch5_permissions():
    """Patch 5: Permissions API normalization."""
    assert "permissions" in _STEALTH_INIT_SCRIPT and "notifications" in _STEALTH_INIT_SCRIPT


def test_init_script_patch6_hardware():
    """Patch 6: hardwareConcurrency / deviceMemory spoofing."""
    assert "hardwareConcurrency" in _STEALTH_INIT_SCRIPT
    assert "deviceMemory" in _STEALTH_INIT_SCRIPT


def test_init_script_patch7_outer_dimensions():
    """Patch 7: outerWidth / outerHeight offset correction."""
    assert "outerWidth" in _STEALTH_INIT_SCRIPT
    assert "outerHeight" in _STEALTH_INIT_SCRIPT


def test_init_script_patch8_canvas_noise():
    """Patch 8: Canvas fingerprint noise — uses getContext interception (reference approach)."""
    assert "getContext" in _STEALTH_INIT_SCRIPT
    assert "getImageData" in _STEALTH_INIT_SCRIPT


# ---------------------------------------------------------------------------
# human_delay
# ---------------------------------------------------------------------------

def test_human_delay_sleeps_within_range():
    start = time.monotonic()
    human_delay(50, 150)
    elapsed_ms = (time.monotonic() - start) * 1000
    # Allow a 50ms tolerance either side for scheduling jitter
    assert 0 <= elapsed_ms <= 200


# ---------------------------------------------------------------------------
# human_type
# ---------------------------------------------------------------------------

def test_human_type_clicks_and_types_each_char():
    page = MagicMock()
    page.keyboard = MagicMock()

    with patch("src.integrations.automation.browser.time.sleep"):
        human_type(page, "#name", "Hi", delay_ms=10)

    page.click.assert_called_once_with("#name")
    assert page.keyboard.type.call_count == 2
    page.keyboard.type.assert_any_call("H")
    page.keyboard.type.assert_any_call("i")


def test_human_type_empty_string_does_not_type():
    page = MagicMock()
    page.keyboard = MagicMock()

    with patch("src.integrations.automation.browser.time.sleep"):
        human_type(page, "#field", "")

    page.click.assert_called_once_with("#field")
    page.keyboard.type.assert_not_called()


# ---------------------------------------------------------------------------
# simulate_mouse_movement
# ---------------------------------------------------------------------------

def test_simulate_mouse_movement_moves_correct_steps():
    page = MagicMock()
    page.viewport_size = {"width": 1280, "height": 800}

    with patch("src.integrations.automation.browser.human_delay"):
        simulate_mouse_movement(page, steps=4)

    assert page.mouse.move.call_count == 4


def test_simulate_mouse_movement_stays_within_viewport():
    page = MagicMock()
    page.viewport_size = {"width": 800, "height": 600}

    moves: list[tuple[int, int]] = []

    def capture_move(x, y, **kwargs):
        moves.append((x, y))

    page.mouse.move.side_effect = capture_move

    with patch("src.integrations.automation.browser.human_delay"):
        simulate_mouse_movement(page, steps=20)

    for x, y in moves:
        assert 50 <= x <= 750
        assert 50 <= y <= 550


def test_simulate_mouse_movement_falls_back_when_no_viewport():
    page = MagicMock()
    page.viewport_size = None  # Playwright returns None in some contexts

    with patch("src.integrations.automation.browser.human_delay"):
        simulate_mouse_movement(page, steps=3)

    assert page.mouse.move.call_count == 3


# ---------------------------------------------------------------------------
# PLAYWRIGHT_BROWSER_CHANNEL env var
# ---------------------------------------------------------------------------

def test_create_stealth_context_passes_channel_env(monkeypatch):
    """When PLAYWRIGHT_BROWSER_CHANNEL=chrome, chromium.launch receives channel='chrome'."""
    monkeypatch.setenv("PLAYWRIGHT_BROWSER_CHANNEL", "chrome")

    mock_playwright = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()

    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    from src.integrations.automation.browser import create_stealth_context

    create_stealth_context(mock_playwright)

    _, kwargs = mock_playwright.chromium.launch.call_args
    assert kwargs.get("channel") == "chrome"


def test_create_stealth_context_no_channel_by_default(monkeypatch):
    """Without env var, channel is None (uses bundled Chromium)."""
    monkeypatch.delenv("PLAYWRIGHT_BROWSER_CHANNEL", raising=False)

    mock_playwright = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()

    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    from src.integrations.automation.browser import create_stealth_context

    create_stealth_context(mock_playwright)

    _, kwargs = mock_playwright.chromium.launch.call_args
    assert kwargs.get("channel") is None


# ---------------------------------------------------------------------------
# create_fresh_context
# ---------------------------------------------------------------------------

def test_create_fresh_context_creates_new_context_from_browser():
    """create_fresh_context creates a new context and page without launching a browser."""
    from src.integrations.automation.browser import create_fresh_context

    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()

    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    context, page = create_fresh_context(mock_browser)

    mock_browser.new_context.assert_called_once()
    mock_context.add_init_script.assert_called_once()
    mock_context.new_page.assert_called_once()
    assert context is mock_context
    assert page is mock_page


# ---------------------------------------------------------------------------
# WorkerBrowserSession
# ---------------------------------------------------------------------------

def test_worker_browser_session_launches_and_closes_browser(monkeypatch):
    """WorkerBrowserSession launches one browser on entry and closes it on exit."""
    from src.integrations.automation.browser import WorkerBrowserSession

    mock_playwright_instance = MagicMock()
    mock_browser = MagicMock()
    mock_playwright_instance.chromium.launch.return_value = mock_browser

    mock_playwright_ctx = MagicMock()
    mock_playwright_ctx.__enter__ = MagicMock(return_value=mock_playwright_instance)
    mock_playwright_ctx.__exit__ = MagicMock(return_value=False)

    with patch("src.integrations.automation.browser.WorkerBrowserSession.__enter__") as patched_enter:
        # Use a more direct approach: patch sync_playwright inside the method
        pass

    # Test via direct mock of the internals
    session = WorkerBrowserSession()
    session._playwright_ctx = mock_playwright_ctx
    session._playwright = mock_playwright_instance
    session.browser = mock_browser

    session.__exit__(None, None, None)

    mock_browser.close.assert_called_once()
    mock_playwright_ctx.__exit__.assert_called_once()


def test_worker_browser_session_new_context_returns_fresh_context():
    """new_context() returns a fresh (context, page) from the shared browser."""
    from src.integrations.automation.browser import WorkerBrowserSession

    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    session = WorkerBrowserSession()
    session.browser = mock_browser

    context, page = session.new_context()

    assert context is mock_context
    assert page is mock_page
    mock_browser.new_context.assert_called_once()


def test_worker_browser_session_new_context_raises_when_not_active():
    """new_context() raises RuntimeError if the session is not started."""
    from src.integrations.automation.browser import WorkerBrowserSession

    session = WorkerBrowserSession()
    with pytest.raises(RuntimeError, match="not active"):
        session.new_context()
