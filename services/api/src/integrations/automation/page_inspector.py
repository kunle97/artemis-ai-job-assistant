"""
Playwright application inspector.

Extracts structured fields from job application pages.

Current goals:
- detect common form elements reliably
- preserve metadata needed for planning/fill
- group radio buttons by shared name
- preserve select options where available
- identify combobox/select-like inputs
"""

from __future__ import annotations

import uuid
from pathlib import Path

from playwright.sync_api import sync_playwright


class ApplicationPageInspector:
    def inspect(self, application_url: str) -> dict:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            try:
                page.goto(application_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(1800)

                title = page.title()
                fields = self._extract_fields(page)
                screenshot_path = self._save_screenshot(page)

                return {
                    "application_url": application_url,
                    "status": "inspected",
                    "title": title,
                    "fields": fields,
                    "screenshot_path": screenshot_path,
                    "notes": [
                        "Playwright inspection completed.",
                        "Inspector v4 adds richer radio/select/combobox extraction.",
                    ],
                }
            finally:
                context.close()
                browser.close()

    def _extract_fields(self, page) -> list[dict]:
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

          for (const el of allControls) {
            const tag = el.tagName.toLowerCase();
            const type = (el.getAttribute('type') || '').toLowerCase();
            const role = (el.getAttribute('role') || '').toLowerCase();
            const name = clean(el.getAttribute('name'));
            const placeholder = clean(el.getAttribute('placeholder'));

            // Buttons
            if (tag === 'button') {
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

            // Textarea
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

            // Native select
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

            // Radio group
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

            // Checkbox
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

            // File
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

            // Combobox/select-like
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

            // Standard inputs
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

          return fields;
        }
        """

        return page.evaluate(script)

    def _save_screenshot(self, page) -> str:
        screenshot_dir = Path("uploads/automation")
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4()}.png"
        path = screenshot_dir / filename

        page.screenshot(path=str(path), full_page=True)
        return str(path)