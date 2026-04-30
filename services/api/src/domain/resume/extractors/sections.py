"""
Resume section extractor.

Extracts major resume sections such as experience and education,
and derives lightweight summary candidates from early content.
"""

from __future__ import annotations

import re

from src.domain.resume.constants import (
    EDUCATION_SECTION_HEADERS,
    EXPERIENCE_SECTION_HEADERS,
    EXTRA_SECTION_HEADERS,
    SKILLS_SECTION_HEADERS,
    TITLE_KEYWORDS,
)

# Matches "Jan 2025 – Current" or "Aug 2022 – December 2024" etc.
_ENTRY_DATE_RE = re.compile(
    r"((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
    r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:t)?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\.?\s+\d{4})\s*[–—\-]+\s*"
    r"((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
    r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:t)?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\.?\s+\d{4}|Current|Present)",
    re.IGNORECASE,
)

# Matches city/state patterns like "New York, NY" or "Wharton, NJ".
# Limited to 1-2 word cities (one optional extra word) to prevent the regex
# from absorbing company-name words like "Corporation".
_LOCATION_RE = re.compile(
    r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?,\s*[A-Z]{2})\b"
)

# Company-name suffixes whose capitalised form can bleed into city matches.
# When the first word of a candidate match is in this set it is skipped.
_COMPANY_SUFFIXES = frozenset({
    "corporation", "corp", "inc", "incorporated", "ltd", "llc", "company",
})

# Section boundary markers used to slice the experience section from raw text.
_SECTION_BOUNDARY_RE = re.compile(
    r"\b(EDUCATION|PROJECTS|SKILLS|CERTIFICATIONS|AWARDS|PUBLICATIONS"
    r"|REFERENCES|VOLUNTEER|SUMMARY|PROFILE)\b",
    re.IGNORECASE,
)


class ResumeSectionExtractor:
    """
    Extract section-based content from a resume.
    """

    def extract(self, lines: list[str], header_lines: list[str], raw_text: str = "") -> dict:
        """
        Extract structured section content from parsed resume lines.
        When raw_text is provided it is used for more accurate experience parsing.
        """
        education_lines = self._extract_section_lines(lines, EDUCATION_SECTION_HEADERS)
        experience_entries = self._parse_experience_entries(raw_text) if raw_text else []

        current_job_title = None
        current_company = None
        if experience_entries:
            most_recent = experience_entries[0]
            current_job_title = most_recent.get("position") or None
            if (most_recent.get("end_date") or "").lower() in ("current", "present"):
                current_company = most_recent.get("company") or None

        return {
            "experience_sections": experience_entries,
            "education_sections": education_lines,
            "current_job_title": current_job_title,
            "current_company": current_company,
            "summary": self._extract_summary(lines, header_lines),
        }

    # ------------------------------------------------------------------
    # Experience structured parsing
    # ------------------------------------------------------------------

    # Bullet characters used by PDF resumes and some DOCX templates.
    _BULLET_CHARS = re.compile(r"[●•▪◦]")

    def _parse_experience_entries(self, raw_text: str) -> list[dict]:
        """
        Parse the EXPERIENCE section of a resume into a list of structured
        job entry dicts: company, position, location, start_date, end_date, details.

        Uses a bullet-based strategy for PDF/rich text (where inline bullet chars
        are present) and a line-based strategy for plain DOCX output.
        """
        exp_raw = self._slice_raw_section(raw_text, EXPERIENCE_SECTION_HEADERS)
        if not exp_raw:
            return []

        has_bullets = len(self._BULLET_CHARS.findall(exp_raw)) >= 3
        if has_bullets:
            return self._parse_bullet_based(exp_raw)
        return self._parse_line_based(exp_raw)

    def _parse_bullet_based(self, exp_raw: str) -> list[dict]:
        """
        Strategy for PDF resumes: collapse all whitespace, split on bullet chars,
        then detect entry headers by looking for date ranges.
        """
        flat = re.sub(r"\s+", " ", exp_raw).strip()
        segments = re.split(r"\s*[●•▪◦]\s*", flat)

        entries: list[dict] = []
        current: dict | None = None

        for i, seg in enumerate(segments):
            seg = seg.strip()
            if not seg:
                continue

            date_m = _ENTRY_DATE_RE.search(seg)

            if not date_m:
                if current is not None:
                    current["details"].append(seg)
                continue

            after_date = seg[date_m.end():].strip()

            if i == 0:
                header_text = seg[: date_m.start()].strip()
                company, position, location = self._parse_header_company_parts(header_text)
                current = self._make_entry(company, position, location, date_m)
                entries.append(current)
                if after_date:
                    current["details"].append(after_date)

            elif not after_date:
                before_date = seg[: date_m.start()].strip()
                bullet_text, header_text = self._split_bullet_and_header(before_date)

                if current and bullet_text:
                    current["details"].append(bullet_text)

                company, position, location = self._parse_header_company_parts(header_text)
                current = self._make_entry(company, position, location, date_m)
                entries.append(current)

            else:
                if current is not None:
                    current["details"].append(seg)

        return entries

    def _parse_line_based(self, exp_raw: str) -> list[dict]:
        """
        Strategy for DOCX resumes where each paragraph is a separate line and
        no bullet Unicode chars are present.  Groups lines by date-range headers.
        """
        lines = [l.strip() for l in exp_raw.splitlines() if l.strip()]
        entries: list[dict] = []
        current: dict | None = None
        pending_header: str = ""

        for line in lines:
            date_m = _ENTRY_DATE_RE.search(line)

            if date_m:
                # This line contains the date range and (usually) the job title.
                before_date = line[: date_m.start()].strip()

                # The position is on the same line as the date; the company/location
                # were on the line(s) before.
                position = before_date.strip()
                header_text = pending_header
                company, _, location = self._parse_header_company_parts(header_text)
                current = self._make_entry(company, position, location, date_m)
                entries.append(current)
                pending_header = ""

            elif current is None:
                # Pre-first-entry: accumulate company/location lines.
                pending_header = line

            else:
                # Post-header line — could be a detail bullet or the next company header.
                # If it looks like a header (has a city/state), treat it as such.
                if _LOCATION_RE.search(line) and not _ENTRY_DATE_RE.search(line):
                    pending_header = line
                else:
                    stripped = line.lstrip("●•▪◦- ").strip()
                    if stripped:
                        current["details"].append(stripped)

        return entries

    def _make_entry(self, company: str, position: str, location: str, date_m: re.Match) -> dict:
        return {
            "company": company,
            "position": position,
            "location": location,
            "start_date": date_m.group(1).strip(),
            "end_date": date_m.group(2).strip(),
            "details": [],
        }

    def _split_bullet_and_header(self, before_date: str) -> tuple[str, str]:
        """
        Given the text before a date range in a non-first segment, split it
        into (bullet_text, entry_header_text). The boundary is the last
        sentence-ending period before the company name.
        """
        last_period = before_date.rfind(". ")
        if last_period >= 0:
            bullet = before_date[: last_period + 1].strip()
            header = before_date[last_period + 1 :].strip()
            return bullet, header

        # No clear period boundary — if the whole thing looks like a header, use it.
        if _LOCATION_RE.search(before_date):
            return "", before_date

        return before_date, ""

    def _parse_header_company_parts(self, header_text: str) -> tuple[str, str, str]:
        """
        Parse company, position, location from an entry header string.

        Strategy: find the first city/state match whose leading word is not a
        known company suffix (e.g. skip "Corporation Wharton, NJ" and accept
        "Wharton, NJ").  This is the most reliable anchor because the location
        always sits between the company name and the job title.
        """
        loc_m = self._find_location_match(header_text)
        if loc_m:
            location = loc_m.group(1).strip()
            company = header_text[: loc_m.start()].strip()
            position = header_text[loc_m.end() :].strip()
            return company, position, location

        # Fallback: split on recognisable title-start keywords.
        location = ""
        for kw in (
            "Senior ", "Junior ", "Lead ", "Staff ", "Principal ",
            "Fullstack ", "Full Stack ", "Full-Stack ",
        ):
            idx = header_text.find(kw)
            if idx > 0:
                return header_text[:idx].strip(), header_text[idx:].strip(), location

        return header_text, "", location

    def _find_location_match(self, text: str) -> re.Match | None:
        """
        Return the first city/state regex match whose first word is not a
        known company suffix.  Scanning forward one character at a time lets
        us find matches that partially overlap a longer (invalid) match.
        """
        pos = 0
        while pos < len(text):
            m = _LOCATION_RE.search(text, pos)
            if not m:
                break
            first_word = m.group(1).split()[0].lower()
            if first_word not in _COMPANY_SUFFIXES:
                return m
            pos = m.start() + 1
        return None

    def _slice_raw_section(self, raw_text: str, section_headers: set[str]) -> str:
        """
        Return the raw text belonging to a section, up to the next major section.
        """
        pattern = "|".join(re.escape(h) for h in section_headers)
        start_m = re.search(pattern, raw_text, re.IGNORECASE)
        if not start_m:
            return ""

        remaining = raw_text[start_m.end():]
        end_m = _SECTION_BOUNDARY_RE.search(remaining)
        return remaining[: end_m.start()] if end_m else remaining

    # ------------------------------------------------------------------
    # Legacy line-based helpers (still used for education / summary)
    # ------------------------------------------------------------------

    def _extract_section_lines(self, lines: list[str], section_headers: set[str]) -> list[str]:
        collected = []
        inside_section = False

        for line in lines:
            normalized = self._normalize_line(line)

            if self._matches_section_heading(normalized, section_headers):
                inside_section = True
                continue

            if inside_section and self._is_section_heading(normalized):
                break

            if inside_section:
                collected.append(line)

        return collected

    def _extract_summary(self, lines: list[str], header_lines: list[str]) -> str | None:
        candidates = []

        for line in lines[:10]:
            lowered = line.lower()

            if line in header_lines and ("@" in line or "http" in lowered or "www." in lowered):
                continue
            if self._is_section_heading(self._normalize_line(line)):
                break
            if len(line) < 30:
                continue
            if self._looks_like_date_line(line):
                continue
            if self._contains_title_keyword(lowered):
                continue

            candidates.append(line)

        return " ".join(candidates[:2]) if candidates else None

    def _is_section_heading(self, normalized_line: str) -> bool:
        headings = (
            EXPERIENCE_SECTION_HEADERS
            | EDUCATION_SECTION_HEADERS
            | SKILLS_SECTION_HEADERS
            | EXTRA_SECTION_HEADERS
        )
        return normalized_line in headings or (
            normalized_line.isupper() and len(normalized_line.split()) <= 4
        )

    def _matches_section_heading(self, normalized_line: str, section_headers: set[str]) -> bool:
        if normalized_line in section_headers:
            return True
        compact = normalized_line.replace(" ", "")
        return any(header.replace(" ", "") in compact for header in section_headers)

    def _contains_title_keyword(self, lowered_line: str) -> bool:
        return any(keyword in lowered_line for keyword in TITLE_KEYWORDS)

    def _looks_like_date_line(self, line: str) -> bool:
        lowered = line.lower()
        return any(
            month in lowered
            for month in (
                "jan", "feb", "mar", "apr", "may", "jun",
                "jul", "aug", "sep", "sept", "oct", "nov", "dec",
                "current", "present",
            )
        ) and any(char.isdigit() for char in line)

    def _normalize_line(self, line: str) -> str:
        return re.sub(r"\s+", " ", line).strip().lower()
