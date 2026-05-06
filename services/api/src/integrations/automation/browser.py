"""
Browser helpers for automation.

Provides a stealth-configured Playwright browser context to reduce
bot-detection fingerprinting on ATS platforms like Lever.
"""

from __future__ import annotations

import os
import random
import time

import logging

from playwright.sync_api import Browser, BrowserContext, Page, Playwright

logger = logging.getLogger(__name__)

_STEALTH_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_STEALTH_LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-infobars",
    "--disable-notifications",
    "--disable-extensions",
    "--disable-gpu",
    "--window-size=1280,800",
    "--start-maximized",
    "--lang=en-US,en",
]

# Injected into every page before any scripts run.
# Patches the most commonly fingerprinted navigator/window properties
# that betray a headless Chromium session.
_STEALTH_INIT_SCRIPT = """
// Patch 1: Remove webdriver flag — delete from prototype so the property is truly absent
// (defineProperty still leaves it present; delete makes it undetectable)
delete Object.getPrototypeOf(navigator).webdriver;

// Spoof plugins — headless has 0, real Chrome has several
Object.defineProperty(navigator, 'plugins', {
  get: () => {
    const arr = [
      { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
      { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
      { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
    ];
    arr.__proto__ = PluginArray.prototype;
    return arr;
  }
});

// Spoof languages
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });

// Spoof hardware concurrency (headless defaults can be suspicious)
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });

// Spoof device memory
Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });

// Mask WebGL renderer strings — "SwiftShader" is a known headless signal
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
  if (parameter === 37445) return 'Intel Inc.';           // UNMASKED_VENDOR_WEBGL
  if (parameter === 37446) return 'Intel Iris OpenGL Engine'; // UNMASKED_RENDERER_WEBGL
  return getParameter.call(this, parameter);
};

// Patch 2: chrome.runtime — full enum object expected by Cloudflare and sannysoft
if (!window.chrome) window.chrome = {};
if (!window.chrome.runtime) {
  window.chrome.runtime = {
    PlatformOs: { MAC: 'mac', WIN: 'win', ANDROID: 'android', CROS: 'cros', LINUX: 'linux', OPENBSD: 'openbsd' },
    PlatformArch: { ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64' },
    PlatformNaclArch: { ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64' },
    RequestUpdateCheckStatus: { THROTTLED: 'throttled', NO_UPDATE: 'no_update', UPDATE_AVAILABLE: 'update_available' },
    OnInstalledReason: { INSTALL: 'install', UPDATE: 'update', CHROME_UPDATE: 'chrome_update', SHARED_MODULE_UPDATE: 'shared_module_update' },
    OnRestartRequiredReason: { APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' }
  };
}

// Spoof permissions query so Notification.permission doesn't betray automation
const originalQuery = window.navigator.permissions && window.navigator.permissions.query;
if (originalQuery) {
  window.navigator.permissions.query = (parameters) =>
    parameters.name === 'notifications'
      ? Promise.resolve({ state: Notification.permission })
      : originalQuery(parameters);
}

// Patch 7: outerWidth / outerHeight — always override; headless can report 0 or equal-to-inner
Object.defineProperty(window, 'outerWidth',  { get: () => window.innerWidth  + 16 });
Object.defineProperty(window, 'outerHeight', { get: () => window.innerHeight + 88 });

// Patch 8: Canvas fingerprint noise — intercept at getContext level so ALL canvas reads are
// affected, not just export. XOR-flips one bit every 400 bytes (reference approach).
(function () {
  const _getContext = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (type, ...args) {
    const ctx = _getContext.call(this, type, ...args);
    if (type === '2d' && ctx) {
      const _getImageData = ctx.getImageData.bind(ctx);
      ctx.getImageData = function (x, y, w, h) {
        const data = _getImageData(x, y, w, h);
        for (let i = 0; i < data.data.length; i += 400) {
          data.data[i] ^= 1;
        }
        return data;
      };
    }
    return ctx;
  };
})();
"""


def create_stealth_context(playwright: Playwright) -> tuple:
    """Launch a Chromium browser and return (browser, context, page).

    Applies a multi-layer stealth configuration to pass common bot-detection
    checks used by ATS platforms (Lever nCaptcha, DataDome, etc.).

    Set the ``PLAYWRIGHT_BROWSER_CHANNEL`` environment variable to ``chrome``
    to use the locally installed Google Chrome binary instead of bundled
    Chromium (recommended for production, requires Chrome to be installed).
    """
    channel = os.environ.get("PLAYWRIGHT_BROWSER_CHANNEL") or None
    # headless=True by default; set PLAYWRIGHT_HEADLESS=false (with Xvfb) for full stealth in production
    headless = os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
    browser = playwright.chromium.launch(
        headless=headless,
        args=_STEALTH_LAUNCH_ARGS,
        channel=channel,
    )
    context: BrowserContext = browser.new_context(
        user_agent=_STEALTH_UA,
        viewport={"width": 1280, "height": 800},
        locale="en-US",
        timezone_id="America/New_York",
        java_script_enabled=True,
        accept_downloads=False,
        # NOTE: extra_http_headers were removed because Sec-Fetch-* navigation
        # headers applied to all requests (including XHR/fetch by React Select)
        # cause those sub-requests to be blocked/misrouted, breaking dynamic
        # dropdowns on platforms like Greenhouse.  The UA + locale + init script
        # are sufficient for bot-detection evasion on Lever / Ashby / Greenhouse.
    )
    context.add_init_script(_STEALTH_INIT_SCRIPT)
    page = context.new_page()
    return browser, context, page


def create_fresh_context(browser: Browser) -> tuple[BrowserContext, Page]:
    """Create a fresh stealth (context, page) from an already-running browser.

    Use this when the Playwright process and browser are managed externally
    (e.g. WorkerBrowserSession). The caller is responsible for closing the
    returned context after use. The browser itself is NOT closed here.
    """
    context: BrowserContext = browser.new_context(
        user_agent=_STEALTH_UA,
        viewport={"width": 1280, "height": 800},
        locale="en-US",
        timezone_id="America/New_York",
        java_script_enabled=True,
        accept_downloads=False,
    )
    context.add_init_script(_STEALTH_INIT_SCRIPT)
    page = context.new_page()
    return context, page


class WorkerBrowserSession:
    """Reuse a single Playwright browser process within one worker task scope.

    Reuses the browser process; each call to ``new_context()`` returns a
    fresh, isolated context+page. Never share a session across users or
    across different ATS domains.

    Usage::

        with WorkerBrowserSession() as session:
            context, page = session.new_context()
            try:
                # ... do work
            finally:
                context.close()
    """

    def __init__(self) -> None:
        self._playwright_ctx = None
        self._playwright = None
        self.browser: Browser | None = None

    def __enter__(self) -> "WorkerBrowserSession":
        from playwright.sync_api import sync_playwright

        self._playwright_ctx = sync_playwright()
        self._playwright = self._playwright_ctx.__enter__()
        channel = os.environ.get("PLAYWRIGHT_BROWSER_CHANNEL") or None
        headless = os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
        self.browser = self._playwright.chromium.launch(
            headless=headless,
            args=_STEALTH_LAUNCH_ARGS,
            channel=channel,
        )
        logger.info("[BrowserPool] Browser process launched")
        return self

    def __exit__(self, *exc_info) -> None:
        try:
            if self.browser is not None:
                self.browser.close()
                logger.info("[BrowserPool] Browser process closed")
        finally:
            if self._playwright_ctx is not None:
                self._playwright_ctx.__exit__(*exc_info)

    def new_context(self) -> tuple[BrowserContext, Page]:
        """Return a fresh (context, page). Caller must close the context when done."""
        if self.browser is None:
            raise RuntimeError("WorkerBrowserSession is not active — use it as a context manager")
        return create_fresh_context(self.browser)


class PlaywrightBrowser:
    """Minimal wrapper around Playwright browser lifecycle (legacy)."""

    def run(self, callback):
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser, context, page = create_stealth_context(playwright)
            try:
                return callback(page)
            finally:
                context.close()
                browser.close()


# ---------------------------------------------------------------------------
# Human-behaviour helpers
# ---------------------------------------------------------------------------

def human_delay(min_ms: int = 200, max_ms: int = 600) -> None:
    """Sleep for a random duration between *min_ms* and *max_ms* milliseconds.

    Simulates natural pauses between user actions to reduce timing-based bot
    detection signals.
    """
    time.sleep(random.randint(min_ms, max_ms) / 1000.0)


def human_type(page: Page, selector: str, text: str, delay_ms: int = 60) -> None:
    """Type *text* into *selector* one character at a time with random delays.

    Each keystroke is separated by a random interval in the range
    [delay_ms // 2, delay_ms * 2] milliseconds, mimicking natural typing.
    The field is clicked first to ensure focus.
    """
    page.click(selector)
    for char in text:
        page.keyboard.type(char)
        time.sleep(random.randint(delay_ms // 2, delay_ms * 2) / 1000.0)


def simulate_mouse_movement(page: Page, steps: int = 5) -> None:
    """Move the mouse in small random increments across the visible viewport.

    Each move uses ``steps=10`` intermediate positions (Playwright interpolation)
    to produce a smooth Bezier-like path that defeats both "no movement" and
    "teleporting cursor" bot-detection heuristics.
    """
    viewport = page.viewport_size or {"width": 1280, "height": 800}
    w, h = viewport["width"], viewport["height"]
    for _ in range(steps):
        x = random.randint(50, w - 50)
        y = random.randint(50, h - 50)
        page.mouse.move(x, y, steps=10)
        human_delay(30, 120)
