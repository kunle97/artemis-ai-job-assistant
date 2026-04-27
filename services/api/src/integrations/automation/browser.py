"""
Browser helpers for automation.

Provides a stealth-configured Playwright browser context to reduce
bot-detection fingerprinting on ATS platforms like Lever.
"""

from __future__ import annotations

from playwright.sync_api import BrowserContext, Playwright

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
// Remove webdriver flag
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

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

// Ensure chrome runtime object exists (absent in plain headless)
if (!window.chrome) {
  window.chrome = { runtime: {} };
}

// Spoof permissions query so Notification.permission doesn't betray automation
const originalQuery = window.navigator.permissions && window.navigator.permissions.query;
if (originalQuery) {
  window.navigator.permissions.query = (parameters) =>
    parameters.name === 'notifications'
      ? Promise.resolve({ state: Notification.permission })
      : originalQuery(parameters);
}
"""


def create_stealth_context(playwright: Playwright) -> tuple:
    """Launch a Chromium browser and return (browser, context, page).

    Applies a multi-layer stealth configuration to pass common bot-detection
    checks used by ATS platforms (Lever nCaptcha, DataDome, etc.).
    """
    browser = playwright.chromium.launch(
        headless=True,
        args=_STEALTH_LAUNCH_ARGS,
    )
    context: BrowserContext = browser.new_context(
        user_agent=_STEALTH_UA,
        viewport={"width": 1280, "height": 800},
        locale="en-US",
        timezone_id="America/New_York",
        java_script_enabled=True,
        accept_downloads=False,
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Upgrade-Insecure-Requests": "1",
        },
    )
    context.add_init_script(_STEALTH_INIT_SCRIPT)
    page = context.new_page()
    return browser, context, page


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
