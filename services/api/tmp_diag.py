import sys
from playwright.sync_api import sync_playwright

LAUNCH_ARGS = [
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
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

EXTRA_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Upgrade-Insecure-Requests": "1",
}

INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', {
  get: () => {
    const arr = [{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }];
    arr.__proto__ = PluginArray.prototype;
    return arr;
  }
});
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
  if (parameter === 37445) return 'Intel Inc.';
  if (parameter === 37446) return 'Intel Iris OpenGL Engine';
  return getParameter.call(this, parameter);
};
if (!window.chrome) { window.chrome = { runtime: {} }; }
const originalQuery = window.navigator.permissions && window.navigator.permissions.query;
if (originalQuery) {
  window.navigator.permissions.query = (parameters) =>
    parameters.name === 'notifications'
      ? Promise.resolve({ state: Notification.permission })
      : originalQuery(parameters);
}
"""

URL = 'https://job-boards.greenhouse.io/equalexperts/jobs/8454247002'

def check(page):
    page.goto(URL, wait_until='networkidle', timeout=25000)
    page.wait_for_timeout(1500)
    cb = page.locator('#country')
    ctrl = cb.locator("xpath=ancestor::div[contains(@class,'select__control')][1]").first
    ctrl.scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    ctrl.click()
    page.wait_for_timeout(600)
    return page.locator('li[role="option"], [class*="select__option"]').count()

# Test 1: all launch args + UA + locale/timezone (no headers, no init script)
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=LAUNCH_ARGS)
    ctx = browser.new_context(
        user_agent=UA, viewport={"width": 1280, "height": 800},
        locale="en-US", timezone_id="America/New_York",
        java_script_enabled=True, accept_downloads=False,
    )
    page = ctx.new_page()
    opt = check(page)
    print(f"no-headers-no-script: options={opt}", flush=True)
    browser.close()

# Test 2: add extra_http_headers
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=LAUNCH_ARGS)
    ctx = browser.new_context(
        user_agent=UA, viewport={"width": 1280, "height": 800},
        locale="en-US", timezone_id="America/New_York",
        java_script_enabled=True, accept_downloads=False,
        extra_http_headers=EXTRA_HEADERS,
    )
    page = ctx.new_page()
    opt = check(page)
    print(f"with-headers-no-script: options={opt}", flush=True)
    browser.close()

# Test 3: add init script too
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=LAUNCH_ARGS)
    ctx = browser.new_context(
        user_agent=UA, viewport={"width": 1280, "height": 800},
        locale="en-US", timezone_id="America/New_York",
        java_script_enabled=True, accept_downloads=False,
        extra_http_headers=EXTRA_HEADERS,
    )
    ctx.add_init_script(INIT_SCRIPT)
    page = ctx.new_page()
    opt = check(page)
    print(f"with-headers-with-script: options={opt}", flush=True)
    browser.close()

# legacy test stubs (unused)
def test(label, args):
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=args)
        ctx = browser.new_context(viewport={'width':1280,'height':800})
        page = ctx.new_page()
        page.goto('https://job-boards.greenhouse.io/equalexperts/jobs/8454247002', wait_until='networkidle', timeout=25000)
        page.wait_for_timeout(1500)
        cb = page.locator('#country')
        ctrl = cb.locator("xpath=ancestor::div[contains(@class,'select__control')][1]").first
        ctrl.scroll_into_view_if_needed()
        page.wait_for_timeout(200)
        ctrl.click()
        page.wait_for_timeout(600)
        opt = page.locator('li[role="option"], [class*="select__option"]').count()
        print(f"{label}: options={opt}", flush=True)
        browser.close()

# Minimal args (known to work when combined with plain headless)
test("no-sandbox only", ['--no-sandbox','--disable-dev-shm-usage'])
# With disable-gpu
test("with-disable-gpu", ['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
