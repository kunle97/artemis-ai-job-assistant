"""
Browser helpers for automation.

Provides a small Playwright wrapper for launching a browser context.
"""

from playwright.sync_api import sync_playwright


class PlaywrightBrowser:
    """
    Minimal wrapper around Playwright browser lifecycle.
    """

    def run(self, callback):
        """
        Launch a browser, execute the callback, and ensure cleanup.
        """
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            try:
                return callback(page)
            finally:
                context.close()
                browser.close()