"""
Run automation test fill against multiple application URLs.

Usage:
python scripts/run_test_fill.py
"""

import os
import sys
import requests
from test_application_urls import TEST_APPLICATION_URLS, TEST_RESUME_PATH
# =========================
# CONFIG
# =========================
BASE_URL = "http://localhost:8000"
ENDPOINT = "/automation-test-fill"

MAX_URLS_TO_TEST = 5  # controls how many URLs to test


# =========================
# AUTH CONFIG
# =========================
AUTH_TOKEN = os.getenv("ARTEMIS_AUTH_TOKEN")
AUTH_SCHEME = os.getenv("ARTEMIS_AUTH_SCHEME", "Token")  # or "Bearer"

if not AUTH_TOKEN:
    print("❌ Missing ARTEMIS_AUTH_TOKEN environment variable")
    sys.exit(1)

print(f"🔐 Using auth scheme: {AUTH_SCHEME}")
print(f"🔐 Token present: {'yes' if AUTH_TOKEN else 'no'}")

# =========================
# HELPERS
# =========================
def calculate_fill_percentage(fill_result: dict) -> float:
    total = len(fill_result.get("fields", []))
    filled = fill_result.get("filled_count", 0)

    if total == 0:
        return 0.0

    return round((filled / total) * 100, 2)


# =========================
# RUNNER
# =========================
def run():
    print("\n🚀 Starting automation test fill run...\n")

    urls_to_test = TEST_APPLICATION_URLS[:MAX_URLS_TO_TEST]

    results = []

    for i, url in enumerate(urls_to_test, start=1):
        print(f"\n🔍 [{i}/{len(urls_to_test)}] Testing: {url}")

        payload = {
            "application_url": url,
            "resume_file_path": TEST_RESUME_PATH,
        }

        try:
            response = requests.post(
                f"{BASE_URL}{ENDPOINT}",
                json=payload,
                headers={
                    "Authorization": f"{AUTH_SCHEME} {AUTH_TOKEN}",
                },
                timeout=120,
            )

            if response.status_code != 200:
                print(f"❌ Failed ({response.status_code}): {response.text}")
                continue

            data = response.json()
            fill = data.get("fill", {})

            percent = calculate_fill_percentage(fill)

            filled = fill.get("filled_count", 0)
            skipped = fill.get("skipped_count", 0)

            print(f"✅ Fill Rate: {percent}%")
            print(f"   Filled: {filled}")
            print(f"   Skipped: {skipped}")

            results.append((url, percent))

        except Exception as e:
            print(f"❌ Error: {str(e)}")

    # =========================
    # SUMMARY
    # =========================
    print("\n📊 FINAL RESULTS\n")

    for url, percent in results:
        print(f"{percent}%  ->  {url}")

    if results:
        avg = round(sum(p for _, p in results) / len(results), 2)
        print(f"\n🔥 Average Fill Rate: {avg}%\n")


if __name__ == "__main__":
    run()