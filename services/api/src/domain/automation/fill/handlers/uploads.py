"""
Handlers for file uploads (Ashby, Lever, Greenhouse).
"""

from __future__ import annotations

import os
from pathlib import Path
from playwright.sync_api import Page

from src.domain.automation.fill.models import AutomationFillFieldResult
from src.integrations.storage.helpers import open_stored_file


def upload_resume(page: Page, field: dict, resume_path: str | None, platform: str | None = None):
    if not resume_path:
        return _result(field, None, "skipped_no_file")

    # Resolve S3 URIs and pre-signed URLs to a local path before using Playwright.
    # open_stored_file returns (local_path, is_temp) — we clean up temp files after use.
    local_path_str, is_temp = open_stored_file(resume_path)
    file_path = Path(local_path_str)

    if not file_path.exists():
        return _result(field, resume_path, "skipped_invalid_resume_path")

    try:
        if platform == "greenhouse":
            return _upload_greenhouse(page, field, file_path)

        if platform == "lever":
            return _upload_lever(page, field, file_path)

        return _upload_generic(page, field, file_path)

    except Exception as exc:
        return _result(
            field,
            f"{str(file_path)} | error={type(exc).__name__}: {exc}",
            "error",
        )
    finally:
        if is_temp:
            try:
                os.unlink(local_path_str)
            except OSError:
                pass


# ========================
# GREENHOUSE ONLY
# ========================
def _upload_greenhouse(page: Page, field: dict, file_path: Path):
    try:
        locator = page.locator("input#resume[type='file']").first

        if locator.count() == 0:
            locator = page.locator(
                ".file-upload:has-text('Resume') input[type='file']"
            ).first

        if locator.count() == 0:
            return _result(field, str(file_path), "skipped_not_found")

        locator.set_input_files(str(file_path))

        locator.evaluate(
            """
            (el) => {
              el.dispatchEvent(new Event("input", { bubbles: true }));
              el.dispatchEvent(new Event("change", { bubbles: true }));
            }
            """
        )

        page.wait_for_timeout(1500)

        uploaded = locator.evaluate("(el) => el.files && el.files.length > 0")

        if not uploaded:
            return _result(field, str(file_path), "skipped_not_found")

        filename = file_path.name

        page.evaluate(
            """
            ({ filename }) => {
              const input = document.querySelector("input#resume[type='file']");
              if (!input) return;

              const wrapper = input.closest(".file-upload__wrapper");
              if (!wrapper) return;

              let status = wrapper.querySelector("[data-artemis-upload-status='resume']");
              if (!status) {
                status = document.createElement("p");
                status.setAttribute("data-artemis-upload-status", "resume");
                status.style.marginTop = "8px";
                status.style.fontSize = "12px";
                status.style.color = "#0a7f35";
                wrapper.appendChild(status);
              }

              status.textContent = `Uploaded: ${filename}`;
            }
            """,
            {"filename": filename},
        )

        page.wait_for_timeout(500)

        return _result(field, str(file_path), "filled")

    except Exception as exc:
        return _result(
            field,
            f"{str(file_path)} | error={type(exc).__name__}: {exc}",
            "error",
        )

# ========================
# LEVER (FIXED)
# ========================
def _upload_lever(page: Page, field: dict, file_path: Path):
    try:
        # 🔥 Lever uses invisible input
        file_input = page.locator('input[type="file"]')

        if file_input.count() == 0:
            return _result(field, str(file_path), "skipped_not_found")

        target = None

        for i in range(file_input.count()):
            el = file_input.nth(i)

            try:
                html = el.evaluate("el => el.outerHTML").lower()
            except Exception:
                continue

            if "resume" in html or "upload" in html or "invisible-resume-upload" in html:
                target = el
                break

        if target is None:
            target = file_input.first

        # 🔥 THIS is critical
        target.set_input_files(str(file_path))

        # trigger change manually (Lever sometimes needs it)
        page.evaluate(
            """
            el => {
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }
            """,
            target,
        )

        page.wait_for_timeout(2500)

        # UI verification
        body = page.locator("body").inner_text().lower()

        if file_path.name.lower() in body:
            return _result(field, str(file_path), "filled")

        # fallback: file attached but hidden UI
        count = target.evaluate("el => el.files.length")

        if count > 0:
            return _result(field, str(file_path), "filled")

        return _result(field, str(file_path), "skipped_ui_not_updated")

    except Exception:
        return _result(field, str(file_path), "skipped_not_found")


# ========================
# GENERIC (ASHBY ETC)
# ========================
def _upload_generic(page: Page, field: dict, file_path: Path):
    try:
        file_input = page.locator('input[type="file"]').first

        file_input.set_input_files(str(file_path))
        page.wait_for_timeout(1500)

        return _result(field, str(file_path), "filled")

    except Exception:
        return _result(field, str(file_path), "skipped_not_found")


# ========================
# RESULT BUILDER
# ========================
def _result(field: dict, value: str | None, status: str):
    return AutomationFillFieldResult(
        label=field.get("label"),
        name=field.get("name"),
        classified_role=field.get("classified_role", "unknown"),
        resolved_value=value,
        fill_status=status,
    )


def skip_cover_letter_upload(field: dict):
    return _result(field, None, "skipped_cover_letter_upload")