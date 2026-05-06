"""
Automation integration helpers.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from src.core.config import AUTOMATION_UPLOADS_DIR


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


def prepare_application_page(page, application_url: str) -> None:
    lowered = (application_url or "").lower()

    if "lever.co" in lowered or "jobs.lever.co" in lowered:
        open_lever_application_form(page)


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

    const getNearbyPrompt = (el) => {
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
            if (text.length > 300) continue;

            return text;
        }
        }

        let prev = container.previousElementSibling;
        let hops = 0;
        while (prev && hops < 3) {
        if (isVisible(prev)) {
            const text = getText(prev);
            if (text && text.length <= 300) return text;
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

    const getRequired = (el) => {
        return Boolean(
        el.required ||
        el.getAttribute('aria-required') === 'true'
        );
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
        required: false,
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

        fields.push({
            field_type: 'radio_group',
            input_subtype: 'radio_group',
            label: inferRadioGroupLabel(radios),
            name,
            placeholder: null,
            required: radios.some((radio) => getRequired(radio)),
            options,
        });
        continue;
        }

        if (tag === 'input' && type === 'checkbox') {
        fields.push({
            field_type: 'checkbox',
            input_subtype: 'checkbox',
            label: inferFieldLabel(el),
            name,
            placeholder: null,
            required: getRequired(el),
        });
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