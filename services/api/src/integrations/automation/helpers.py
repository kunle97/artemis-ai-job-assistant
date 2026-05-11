"""
Automation integration helpers.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from urllib.parse import urljoin

from src.core.config import AUTOMATION_UPLOADS_DIR

logger = logging.getLogger(__name__)


def open_lever_application_form(page) -> None:
    candidate_selectors = [
        "text='Apply for this job'",
        "text='Apply for this Job'",
        "button:has-text('Apply for this job')",
        "button:has-text('Apply')",
        "[role='button']:has-text('Apply for this job')",
        "[role='button']:has-text('Apply')",
        "a:has-text('Apply for this job')",
        "a:has-text('Apply')",
    ]

    for selector in candidate_selectors:
        try:
            locator = page.locator(selector).first
            if locator.count() == 0:
                continue

            if locator.is_visible():
                locator.click(timeout=2000)
                page.wait_for_timeout(1200)
                return
        except Exception:
            continue


def _has_detectable_form(page) -> bool:
    """Return True when the current page appears to contain a fillable application form.

    Excludes inputs that are clearly navigation chrome (nav/header/footer elements,
    search inputs, hidden fields, submit/button/reset/image types) to prevent false
    positives on career listing pages that have a search box but no application form.
    """
    return bool(
        page.evaluate(
            """
            () => {
                const isVisible = (el) => {
                    if (!el) return false;
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden') return false;
                    const rect = el.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                };

                // Types that are never real application form fields
                const NON_FORM_TYPES = new Set([
                    'hidden', 'button', 'submit', 'reset', 'search', 'image'
                ]);

                const isRealFormControl = (el) => {
                    if (!isVisible(el)) return false;
                    const type = (el.getAttribute('type') || '').toLowerCase();
                    if (NON_FORM_TYPES.has(type)) return false;
                    // Skip inputs that live inside navigation chrome
                    if (el.closest('nav') || el.closest('header') || el.closest('footer')) return false;
                    return true;
                };

                const controls = Array.from(
                    document.querySelectorAll('input, textarea, select')
                ).filter(isRealFormControl);

                if (controls.length >= 3) return true;

                const formWithControls = Array.from(document.querySelectorAll('form')).some((form) => {
                    const visibleControls = Array.from(
                        form.querySelectorAll('input, textarea, select')
                    ).filter(isRealFormControl).length;
                    return visibleControls >= 2;
                });

                return formWithControls;
            }
            """
        )
    )


def _extract_apply_destinations(page, base_url: str) -> list[str]:
    """Extract likely apply destinations from visible page links/buttons."""
    destinations: list[str] = page.evaluate(
        """
        () => {
            const isVisible = (el) => {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };

            const textLooksLikeApply = (value) => {
                const text = String(value || '').toLowerCase().trim();
                if (!text) return false;
                return (
                    text.includes('apply') ||
                    text.includes('submit application') ||
                    text.includes('continue application') ||
                    text.includes('view job and apply') ||
                    text.includes('start application')
                );
            };

            const nodes = Array.from(document.querySelectorAll('a, button, [role="button"]'));
            const results = [];

            for (const node of nodes) {
                if (!isVisible(node)) continue;

                const text = (node.innerText || node.textContent || '').replace(/\s+/g, ' ').trim();
                const aria = node.getAttribute('aria-label') || '';
                const title = node.getAttribute('title') || '';

                if (!textLooksLikeApply(text) && !textLooksLikeApply(aria) && !textLooksLikeApply(title)) {
                    continue;
                }

                const href = node.getAttribute('href') || node.getAttribute('data-href') || '';
                if (href && !href.startsWith('javascript:') && !href.startsWith('#')) {
                    results.push(href);
                }
            }

            return results;
        }
        """
    )

    prioritized = sorted(
        {
            urljoin(base_url, destination)
            for destination in destinations
            if destination and destination.strip()
        },
        key=lambda value: (
            0 if "greenhouse" in value.lower() else 1,
            0 if "lever" in value.lower() else 1,
            0 if "ashby" in value.lower() else 1,
            0 if "workday" in value.lower() else 1,
            0 if "icims" in value.lower() else 1,
            0 if "smartrecruiters" in value.lower() else 1,
            0 if "/apply" in value.lower() else 1,
            len(value),
        ),
    )
    return prioritized


def _open_first_apply_destination(page) -> bool:
    """Open the most likely apply destination from the current page."""
    current_url = page.url or ""
    for destination in _extract_apply_destinations(page, current_url):
        if destination == current_url:
            continue
        try:
            page.goto(destination, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1200)
            logger.info("[AutomationHelpers] Followed apply destination: %s", destination)
            return True
        except Exception:
            continue
    return False


def _click_apply_cta(page) -> bool:
    """Click visible apply CTAs when direct destination extraction is unavailable."""
    candidate_selectors = [
        "button:has-text('Apply for this role')",
        "a:has-text('Apply for this role')",
        "button:has-text('Apply for this job')",
        "a:has-text('Apply for this job')",
        "button:has-text('Apply now')",
        "a:has-text('Apply now')",
        "button:has-text('Apply')",
        "a:has-text('Apply')",
        "[role='button']:has-text('Apply')",
    ]

    for selector in candidate_selectors:
        try:
            locator = page.locator(selector).first
            if locator.count() == 0 or not locator.is_visible():
                continue

            current_url = page.url
            locator.click(timeout=2500)
            page.wait_for_timeout(1200)

            if page.url != current_url:
                logger.info("[AutomationHelpers] Clicked apply CTA and navigated: %s", selector)
                return True

            # Some pages update content without URL change.
            if _has_detectable_form(page):
                logger.info("[AutomationHelpers] Clicked apply CTA and form appeared: %s", selector)
                return True
        except Exception:
            continue

    return False


_ATS_IFRAME_KEYWORDS = [
    "greenhouse.io",
    "lever.co",
    "ashbyhq.com",
    "myworkdayjobs.com",
    "icims.com",
    "smartrecruiters.com",
    "jobvite.com",
]


def _extract_ats_iframe_src(page) -> str | None:
    """Return the src of the first ATS-hosted iframe on the current page, or None.

    Many company career pages embed the real application form in an iframe that
    points to a third-party ATS (Greenhouse, Lever, Ashby, Workday …).  Neither
    ``_has_detectable_form`` nor ``extract_fields`` can see inside an iframe via
    ``page.evaluate``, so we need to detect these iframes and navigate to their
    src URL directly.
    """
    try:
        srcs: list[str] = page.evaluate(
            """
            () => Array.from(document.querySelectorAll('iframe'))
                .map(f => (f.src || f.getAttribute('src') || '').trim())
                .filter(Boolean)
            """
        )
    except Exception:
        return None

    for src in srcs:
        if any(kw in src.lower() for kw in _ATS_IFRAME_KEYWORDS):
            return src
    return None


def _attempt_open_apply_cta(page) -> bool:
    """Try multiple strategies to progress from listing pages to application forms."""
    if _open_first_apply_destination(page):
        return True
    return _click_apply_cta(page)


def _detect_ashby_application_url(page, application_url: str) -> str | None:
    """Return the Ashby application form URL if the current page is an Ashby job overview.

    Detection strategy (most-reliable to least):
    1. The stored application_url or current page URL contains 'ashbyhq.com'.
    2. The page has a link whose href contains 'ashbyhq.com' (the Apply button on
       company-hosted pages typically links to jobs.ashbyhq.com).
    3. The current page URL + '/application' is a known Ashby pattern — confirmed by
       finding a link that ends with '/application' pointing to a sibling path, OR by
       a footer/body text mention of 'ashby' (least reliable, used as last resort).
    """
    current_url = (page.url or "").rstrip("/")

    # Already on the application form page — nothing to do
    if current_url.lower().endswith("/application"):
        return None

    lowered_stored = (application_url or "").lower()
    lowered_current = current_url.lower()

    # 1. URL-based: ashbyhq.com appears in the stored or live URL
    if "ashbyhq.com" in lowered_stored or "ashbyhq.com" in lowered_current:
        return current_url + "/application"

    # 2. Link-based: page contains a link pointing to ashbyhq.com (most reliable
    #    for company-hosted pages like ramp.com, notion.so, etc.)
    try:
        ashby_href: str | None = page.evaluate(
            """
            () => {
                const links = Array.from(document.querySelectorAll('a[href]'));
                for (const a of links) {
                    const href = (a.href || a.getAttribute('href') || '').toLowerCase();
                    if (href.includes('ashbyhq.com')) return a.href || a.getAttribute('href');
                }
                return null;
            }
            """
        )
        if ashby_href:
            logger.debug("[AutomationHelpers] Detected Ashby via page link: %s", ashby_href)
            return current_url + "/application"
    except Exception:
        pass

    # 3. Text-based: 'powered by ashby' or similar in footer / body (last resort)
    try:
        has_ashby_text: bool = page.evaluate(
            """
            () => {
                const text = (document.body ? document.body.innerText : '') || '';
                const lower = text.toLowerCase();
                return lower.includes('powered by ashby') || lower.includes('ashbyhq.com');
            }
            """
        )
        if has_ashby_text:
            logger.debug("[AutomationHelpers] Detected Ashby via page text")
            return current_url + "/application"
    except Exception:
        pass

    return None


def _navigate_to_ashby_application(page, application_url: str) -> bool:
    """Navigate to the Ashby /application page if on a job overview page."""
    target = _detect_ashby_application_url(page, application_url)
    if not target:
        return False
    try:
        page.goto(target, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(1500)
        logger.info("[AutomationHelpers] Navigated to Ashby application form: %s", target)
        return True
    except Exception as exc:
        logger.warning(
            "[AutomationHelpers] Failed to navigate to Ashby /application page %s: %s",
            target,
            exc,
        )
        return False


def prepare_application_page(page, application_url: str) -> None:
    lowered = (application_url or "").lower()

    if "lever.co" in lowered or "jobs.lever.co" in lowered:
        open_lever_application_form(page)

    # For Ashby-powered pages: navigate to /application before form detection,
    # since the overview page is not the form and may contain enough visible
    # inputs to fool _has_detectable_form (e.g. a search bar or login field).
    _navigate_to_ashby_application(page, application_url)

    # Generic fallback for hosted career pages (Stripe, company careers, etc.):
    # If no application form is detected on the current page, try two strategies
    # in order:
    #   1. Follow an "Apply" CTA link/button to the actual application page.
    #   2. Detect an ATS iframe (Greenhouse, Lever, Ashby …) and navigate to
    #      its src URL directly so that extract_fields can see the real form.
    max_apply_attempts = 3
    max_form_checks = 3

    for apply_attempt in range(max_apply_attempts):
        for form_attempt in range(max_form_checks):
            if _has_detectable_form(page):
                return
            page.wait_for_timeout(700)

        # Check whether the page embeds an ATS form in an iframe and navigate
        # to it directly.  This handles pages like stripe.com/jobs/listing/…/apply
        # which embed boards.greenhouse.io inside an <iframe>.
        ats_iframe_src = _extract_ats_iframe_src(page)
        if ats_iframe_src:
            try:
                page.goto(ats_iframe_src, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(1500)
                logger.info("[AutomationHelpers] Navigated into ATS iframe: %s", ats_iframe_src)
                return
            except Exception as exc:
                logger.warning(
                    "[AutomationHelpers] Failed to navigate to ATS iframe %s: %s",
                    ats_iframe_src,
                    exc,
                )

        opened = _attempt_open_apply_cta(page)
        if not opened:
            break


def extract_fields(page) -> list[dict]:
    script = """
    () => {
    const clean = (value) => {
        if (value === null || value === undefined) return null;
        const text = String(value).replace(/\\s+/g, ' ').trim();
        return text || null;
    };

    const isVisible = (el) => {
        if (!el) return false;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden') return false;
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    };

    const getText = (el) => {
        if (!el) return null;
        return clean(el.innerText || el.textContent || '');
    };

    const getByIdsText = (ids) => {
        if (!ids) return null;
        const texts = ids
        .split(/\\s+/)
        .map((id) => document.getElementById(id))
        .filter(Boolean)
        .map((node) => getText(node))
        .filter(Boolean);
        return texts.length ? clean(texts.join(' ')) : null;
    };

    const getLabelFor = (el) => {
        if (!el) return null;

        const ariaLabel = clean(el.getAttribute('aria-label'));
        if (ariaLabel) return ariaLabel;

        const ariaLabelledBy = el.getAttribute('aria-labelledby');
        const labelledByText = getByIdsText(ariaLabelledBy);
        if (labelledByText) return labelledByText;

        const id = el.id;
        if (id) {
        const explicitLabel = document.querySelector(`label[for="${CSS.escape(id)}"]`);
        const explicitLabelText = getText(explicitLabel);
        if (explicitLabelText) return explicitLabelText;
        }

        const wrappedLabel = el.closest('label');
        const wrappedLabelText = getText(wrappedLabel);
        if (wrappedLabelText) return wrappedLabelText;

        return null;
    };

    const findBestContainer = (el) => {
        return (
        el.closest('fieldset') ||
        el.closest('[role="group"]') ||
        el.closest('.field-wrapper') ||
        el.closest('.form-group') ||
        el.closest('.question') ||
        el.closest('.input-wrapper') ||
        el.closest('[data-testid]') ||
        el.parentElement
        );
    };

    const getNearbyPrompt = (el, options = {}) => {
        const maxTextLength = Number(options.maxTextLength || 300);
        const container = findBestContainer(el);
        if (!container) return null;

        const candidateSelectors = [
        'legend',
        '.question-label',
        '.field-label',
        '.form-label',
        '.label',
        'label',
        'p',
        'span',
        'div',
        'h1',
        'h2',
        'h3',
        'h4',
        ];

        for (const selector of candidateSelectors) {
        const nodes = Array.from(container.querySelectorAll(selector));
        for (const node of nodes) {
            if (!isVisible(node)) continue;
            if (node.contains(el)) continue;

            const text = getText(node);
            if (!text) continue;

            const lowered = text.toLowerCase();
            if (['yes', 'no', 'true', 'false'].includes(lowered)) continue;
            if (text.length > maxTextLength) continue;

            return text;
        }
        }

        let prev = container.previousElementSibling;
        let hops = 0;
        while (prev && hops < 3) {
        if (isVisible(prev)) {
            const text = getText(prev);
            if (text && text.length <= maxTextLength) return text;
        }
        prev = prev.previousElementSibling;
        hops += 1;
        }

        return null;
    };

    const isGenericFileLabel = (label) => {
        const normalized = clean(label)?.toLowerCase();
        if (!normalized) return true;

        return [
        'attach',
        'upload',
        'upload file',
        'choose file',
        'browse',
        ].includes(normalized);
    };

    const getMeaningfulFileLabel = (el) => {
        const directLabel = getLabelFor(el);
        if (directLabel && !isGenericFileLabel(directLabel)) {
        return directLabel;
        }

        const ancestorCandidates = [];
        let current = el;
        let depth = 0;

        while (current && depth < 6) {
        current = current.parentElement;
        if (!current) break;
        ancestorCandidates.push(current);
        depth += 1;
        }

        const candidateSelectors = [
        'legend',
        '.question-label',
        '.field-label',
        '.form-label',
        '.label',
        'label',
        'h1',
        'h2',
        'h3',
        'h4',
        'p',
        'span',
        'div',
        ];

        for (const ancestor of ancestorCandidates) {
        for (const selector of candidateSelectors) {
            const nodes = Array.from(ancestor.querySelectorAll(selector));

            for (const node of nodes) {
            if (!isVisible(node)) continue;
            if (node.contains(el)) continue;

            const text = getText(node);
            if (!text) continue;

            const lowered = text.toLowerCase();

            if (isGenericFileLabel(text)) continue;

            if (
                [
                'dropbox',
                'google drive',
                'enter manually',
                'toggle flyout',
                ].includes(lowered)
            ) {
                continue;
            }

            if (text.length > 300) continue;

            if (
                lowered.includes('resume') ||
                lowered.includes('cv') ||
                lowered.includes('resume/cv') ||
                lowered.includes('cover letter') ||
                lowered.includes('cover-letter')
            ) {
                return text;
            }
            }
        }
        }

        return directLabel || getNearbyPrompt(el);
    };

    const inferFieldLabel = (el) => {
        const tag = (el.tagName || '').toLowerCase();
        const type = (el.getAttribute?.('type') || '').toLowerCase();

        // Consent/acknowledgement checkbox prompts are often long policy text.
        // Allow a larger prompt length so those questions are not dropped.
        if (tag === 'input' && type === 'checkbox') {
        return getLabelFor(el) || getNearbyPrompt(el, { maxTextLength: 2000 });
        }

        return getLabelFor(el) || getNearbyPrompt(el);
    };

    const inferRadioOptionLabel = (radio) => {
        const direct = getLabelFor(radio);
        if (direct) return direct;

        const container = findBestContainer(radio);
        if (container) {
        const labelish = Array.from(container.querySelectorAll('label, span, div'))
            .filter(isVisible)
            .map((node) => getText(node))
            .filter(Boolean);

        for (const text of labelish) {
            const lowered = text.toLowerCase();
            if (['yes', 'no', 'true', 'false'].includes(lowered)) {
            return text;
            }
        }
        }

        return clean(radio.value);
    };

    const inferRadioGroupLabel = (radios) => {
        if (!radios.length) return null;

        const first = radios[0];
        const fieldset = first.closest('fieldset');
        if (fieldset) {
        const legend = fieldset.querySelector('legend');
        const legendText = getText(legend);
        if (legendText && !['yes', 'no'].includes(legendText.toLowerCase())) {
            return legendText;
        }
        }

        const ariaLabelledBy = first.getAttribute('aria-labelledby');
        const labelledByText = getByIdsText(ariaLabelledBy);
        if (labelledByText && !['yes', 'no'].includes(labelledByText.toLowerCase())) {
        return labelledByText;
        }

        return getNearbyPrompt(first);
    };

    const textImpliesRequired = (text) => {
        if (!text) return false;
        const normalized = String(text).trim();
        if (!normalized) return false;
        return /\*/.test(normalized) || /\brequired\b/i.test(normalized);
    };

    const getRequired = (el) => {
        if (!el) return false;

        if (
        el.required ||
        el.getAttribute('aria-required') === 'true' ||
        el.getAttribute('required') !== null ||
        el.getAttribute('data-required') === 'true'
        ) {
        return true;
        }

        const labelledByText = getByIdsText(el.getAttribute('aria-labelledby'));
        const directLabel = getLabelFor(el);
        const nearbyPrompt = getNearbyPrompt(el);
        const candidateTexts = [labelledByText, directLabel, nearbyPrompt]
        .filter(Boolean)
        .map((value) => String(value).trim());

        if (candidateTexts.some((text) => textImpliesRequired(text))) {
        return true;
        }

        const container = findBestContainer(el);
        if (!container) return false;

        if (
        container.getAttribute('aria-required') === 'true' ||
        container.getAttribute('data-required') === 'true'
        ) {
        return true;
        }

        let current = el;
        let depth = 0;
        while (current && depth < 4) {
        if (
            current.getAttribute && (
            current.getAttribute('aria-required') === 'true' ||
            current.getAttribute('data-required') === 'true' ||
            current.getAttribute('required') !== null ||
            current.classList?.contains('required')
            )
        ) {
            return true;
        }
        current = current.parentElement;
        depth += 1;
        }

        return false;
    };

    const getNativeSelectOptions = (selectEl) => {
        const options = Array.from(selectEl.querySelectorAll('option'))
        .map((option) => ({
            label: clean(option.innerText || option.textContent),
            value: clean(option.value),
        }))
        .filter((option) => option.label || option.value);

        return options;
    };

    const getComboboxOptionsFromDom = (el) => {
        const options = [];
        const container = findBestContainer(el);
        if (!container) return options;

        const listboxCandidates = Array.from(
        container.querySelectorAll('[role="option"], option')
        );

        for (const option of listboxCandidates) {
        if (!isVisible(option)) continue;
        const label = getText(option);
        const value = clean(option.getAttribute('value')) || label;
        if (!label && !value) continue;
        options.push({ label, value });
        }

        return options;
    };

    const allControls = Array.from(
        document.querySelectorAll('input, textarea, select, button')
    ).filter(isVisible);

    const fields = [];
    const seenRadioNames = new Set();

    // === Detect Ashby-style Yes/No pill button groups ===
    // These appear as pairs of <button>Yes</button><button>No</button> inside a
    // question container. We group them into a radio_group so they can be
    // classified and filled like any other binary choice field.
    const pillButtonElements = new Set();
    const pillGroupFields = [];

    const yesNoCandidates = allControls.filter((el) => {
        if (el.tagName.toLowerCase() !== 'button') return false;
        const t = (getText(el) || '').toLowerCase().trim();
        return t === 'yes' || t === 'no';
    });

    const seenPillContainers = new Set();

    for (const btn of yesNoCandidates) {
        if (pillButtonElements.has(btn)) continue;

        // Walk up to find the smallest container that holds both a Yes and a No button.
        let pillContainer = null;
        let current = btn.parentElement;
        let depth = 0;
        while (current && depth < 6) {
        const btns = Array.from(current.querySelectorAll('button')).filter(isVisible);
        const hasYes = btns.some((b) => (getText(b) || '').toLowerCase().trim() === 'yes');
        const hasNo = btns.some((b) => (getText(b) || '').toLowerCase().trim() === 'no');
        if (hasYes && hasNo) {
            pillContainer = current;
            break;
        }
        current = current.parentElement;
        depth += 1;
        }

        if (!pillContainer) continue;
        if (seenPillContainers.has(pillContainer)) continue;
        seenPillContainers.add(pillContainer);

        const containerBtns = Array.from(pillContainer.querySelectorAll('button')).filter(isVisible);
        const yesBtn = containerBtns.find((b) => (getText(b) || '').toLowerCase().trim() === 'yes');
        const noBtn = containerBtns.find((b) => (getText(b) || '').toLowerCase().trim() === 'no');
        if (!yesBtn || !noBtn) continue;

        // Find the question text for this pill group.
        let questionLabel = null;

        // 1. Look for visible text nodes inside the container that aren't the pill buttons.
        const textNodes = Array.from(
        pillContainer.querySelectorAll('label, p, span, div, h1, h2, h3, h4, legend')
        )
        .filter(isVisible)
        .filter((n) => !n.contains(yesBtn) && !n.contains(noBtn));

        for (const node of textNodes) {
        const t = getText(node);
        if (!t) continue;
        const lower = t.toLowerCase().trim();
        if (['yes', 'no', 'true', 'false'].includes(lower)) continue;
        if (t.length < 4 || t.length > 300) continue;
        questionLabel = t;
        break;
        }

        // 2. Fall back to the previous sibling element of the container.
        if (!questionLabel) {
        let prev = pillContainer.previousElementSibling;
        let hops = 0;
        while (prev && hops < 3) {
            if (isVisible(prev)) {
            const t = getText(prev);
            if (t && t.length >= 4 && t.length <= 300) {
                questionLabel = t;
                break;
            }
            }
            prev = prev.previousElementSibling;
            hops += 1;
        }
        }

        // Only emit if we found a meaningful question label.
        if (!questionLabel) continue;

        pillButtonElements.add(yesBtn);
        pillButtonElements.add(noBtn);

        pillGroupFields.push({
        field_type: 'radio_group',
        input_subtype: 'pill',
        label: questionLabel,
        name: null,
        placeholder: null,
        required: textImpliesRequired(questionLabel) ||
            pillContainer.getAttribute('aria-required') === 'true' ||
            pillContainer.getAttribute('data-required') === 'true' ||
            pillContainer.classList?.contains('required'),
        options: [
            { label: getText(yesBtn), value: (getText(yesBtn) || 'yes').toLowerCase().trim() },
            { label: getText(noBtn), value: (getText(noBtn) || 'no').toLowerCase().trim() },
        ],
        });
    }

    for (const el of allControls) {
        const tag = el.tagName.toLowerCase();
        const type = (el.getAttribute('type') || '').toLowerCase();
        const role = (el.getAttribute('role') || '').toLowerCase();
        const name = clean(el.getAttribute('name'));
        const placeholder = clean(el.getAttribute('placeholder'));

        if (tag === 'button') {
        // Skip buttons that were consumed as part of a pill group above.
        if (pillButtonElements.has(el)) continue;
        fields.push({
            field_type: 'button',
            input_subtype: null,
            label: getText(el) || clean(el.getAttribute('aria-label')),
            name,
            placeholder: null,
            required: false,
        });
        continue;
        }

        if (tag === 'textarea') {
        fields.push({
            field_type: 'textarea',
            input_subtype: null,
            label: inferFieldLabel(el),
            name,
            placeholder,
            required: getRequired(el),
        });
        continue;
        }

        if (tag === 'select') {
        fields.push({
            field_type: 'select',
            input_subtype: 'native_select',
            label: inferFieldLabel(el),
            name,
            placeholder,
            required: getRequired(el),
            options: getNativeSelectOptions(el),
        });
        continue;
        }

        if (tag === 'input' && type === 'radio') {
        if (!name) continue;
        if (seenRadioNames.has(name)) continue;
        seenRadioNames.add(name);

        const radios = allControls.filter((candidate) => {
            return (
            candidate.tagName.toLowerCase() === 'input' &&
            (candidate.getAttribute('type') || '').toLowerCase() === 'radio' &&
            clean(candidate.getAttribute('name')) === name
            );
        });

        const options = radios.map((radio) => {
            const label = inferRadioOptionLabel(radio);
            const value = clean(radio.value) || label;
            return { label, value };
        });

        const radioGroupLabel = inferRadioGroupLabel(radios);
        const radioGroupRequired =
            radios.some((radio) => getRequired(radio)) ||
            textImpliesRequired(radioGroupLabel);

        fields.push({
            field_type: 'radio_group',
            input_subtype: 'radio_group',
            label: radioGroupLabel,
            name,
            placeholder: null,
            required: radioGroupRequired,
            options,
        });
        continue;
        }

        if (tag === 'input' && type === 'checkbox') {
        // Deferred: checkboxes are grouped into checkbox_group fields below.
        continue;
        }

        if (tag === 'input' && type === 'file') {
        fields.push({
            field_type: 'file',
            input_subtype: 'file',
            label: getMeaningfulFileLabel(el),
            name,
            placeholder: null,
            required: getRequired(el),
        });
        continue;
        }

        if (
        (tag === 'input' && role === 'combobox') ||
        role === 'combobox'
        ) {
        fields.push({
            field_type: 'select_like',
            input_subtype: 'combobox',
            label: inferFieldLabel(el),
            name,
            placeholder,
            required: getRequired(el),
            options: getComboboxOptionsFromDom(el),
        });
        continue;
        }

        if (tag === 'input') {
        fields.push({
            field_type: 'input',
            input_subtype: type || 'text',
            label: inferFieldLabel(el),
            name,
            placeholder,
            required: getRequired(el),
        });
        }
    }

    // === Group checkboxes into checkbox_group (or standalone checkbox) fields ===
    // Consecutive checkboxes sharing a common container are merged into a single
    // checkbox_group with each checkbox as an option.  Isolated checkboxes (e.g.
    // a single consent box) remain as individual checkbox fields.
    {
        const checkboxEls = allControls.filter(
        (c) => c.tagName.toLowerCase() === 'input' &&
                (c.getAttribute('type') || '').toLowerCase() === 'checkbox'
        );
        const checkboxElsSet = new Set(checkboxEls);
        const seenCheckboxEls = new Set();

        for (const cb of checkboxEls) {
        if (seenCheckboxEls.has(cb)) continue;

        // Find the smallest container that holds 2+ of our visible checkboxes.
        let groupContainer = null;
        let cur = cb.parentElement;
        let d = 0;
        while (cur && d < 8) {
            const cbsInCur = Array.from(cur.querySelectorAll('input[type="checkbox"]'))
            .filter((c) => checkboxElsSet.has(c));
            if (cbsInCur.length >= 2) {
            groupContainer = cur;
            break;
            }
            cur = cur.parentElement;
            d += 1;
        }

        if (groupContainer) {
            const groupCbs = Array.from(groupContainer.querySelectorAll('input[type="checkbox"]'))
            .filter((c) => checkboxElsSet.has(c) && !seenCheckboxEls.has(c));

            if (groupCbs.length >= 2) {
            // Look for a group label: preceding sibling text or nearby prompt.
            let groupLabel = null;
            let prevEl = groupContainer.previousElementSibling;
            let hops = 0;
            while (prevEl && hops < 3) {
                if (isVisible(prevEl)) {
                const t = getText(prevEl);
                if (t && t.length >= 3 && t.length <= 2000) {
                    groupLabel = t;
                    break;
                }
                }
                prevEl = prevEl.previousElementSibling;
                hops += 1;
            }
            if (!groupLabel) {
                groupLabel = getNearbyPrompt(groupCbs[0]);
            }

            const options = groupCbs.map((c) => {
                const lbl = inferFieldLabel(c);
                const val = (c.getAttribute('name') || lbl || '').trim();
                return { label: lbl, value: val };
            });

            fields.push({
                field_type: 'checkbox_group',
                input_subtype: 'checkbox_group',
                label: groupLabel,
                name: null,
                placeholder: null,
                required: groupCbs.some((c) => getRequired(c)),
                options,
            });

            groupCbs.forEach((c) => seenCheckboxEls.add(c));
            continue;
            }
        }

        // Standalone checkbox (consent, single toggle, etc.)
        fields.push({
            field_type: 'checkbox',
            input_subtype: 'checkbox',
            label: inferFieldLabel(cb),
            name: (cb.getAttribute('name') || '').trim() || null,
            placeholder: null,
            required: getRequired(cb),
        });
        seenCheckboxEls.add(cb);
        }
    }

    // Append pill groups discovered above.
    for (const pillField of pillGroupFields) {
        fields.push(pillField);
    }

    return fields;
    }
    """

    return page.evaluate(script)

def normalize_application_url(application_url: str) -> str:
    url = (application_url or "").strip()
    lowered = url.lower()

    if "jobs.lever.co" in lowered or "lever.co" in lowered:
        if not lowered.endswith("/apply"):
            return url.rstrip("/") + "/apply"

    if "ashbyhq.com" in lowered:
        if not lowered.endswith("/application"):
            return url.rstrip("/") + "/application"

    return url

def _platform_subfolder(url: str | None) -> str:
    lowered = (url or "").lower()
    if "greenhouse" in lowered:
        return "greenhouse"
    if "ashbyhq" in lowered or "ashby" in lowered:
        return "ashby"
    if "lever" in lowered:
        return "lever"
    return "generic"


def save_screenshot(page, url: str | None = None) -> str | None:
    from src.core.config import settings
    if not settings.save_screenshots:
        return None
    platform = _platform_subfolder(url)
    screenshot_dir = AUTOMATION_UPLOADS_DIR / platform
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}.png"
    path = screenshot_dir / filename

    page.screenshot(path=str(path), full_page=True)
    return str(path)


def detect_already_applied_signal(page) -> bool:
    """Return True when the page indicates the user already applied.

    This checks both the current URL and visible page text for common ATS
    confirmation messages used after a prior submission.
    """
    current_url = (page.url or "").lower()
    if any(token in current_url for token in ["already-applied", "already_applied", "application-submitted"]):
        return True

    text = page.evaluate(
        """
        () => {
            const root = document.querySelector('main') || document.body;
            if (!root) return '';
            return (root.innerText || '').toLowerCase();
        }
        """
    )

    signals = [
        "you have already applied",
        "you already applied",
        "already applied",
        "application has already been submitted",
        "you've already submitted",
    ]
    return any(signal in text for signal in signals)