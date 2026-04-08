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


class ResumeSectionExtractor:
    """
    Extract section-based content from a resume.
    """

    def extract(self, lines: list[str], header_lines: list[str]) -> dict:
        """
        Extract structured section content from parsed resume lines.
        """
        experience_lines = self._extract_section_lines(lines, EXPERIENCE_SECTION_HEADERS)
        education_lines = self._extract_section_lines(lines, EDUCATION_SECTION_HEADERS)

        return {
            "experience_sections": experience_lines,
            "education_sections": education_lines,
            "current_job_title": self._extract_current_job_title(experience_lines),
            "summary": self._extract_summary(lines, header_lines),
        }

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

    def _extract_current_job_title(self, experience_lines: list[str]) -> str | None:
        for line in experience_lines[:12]:
            lowered = line.lower()

            if line.startswith(("•", "-", "*")):
                continue
            if len(line.split()) > 8:
                continue
            if self._looks_like_date_line(line):
                continue
            if self._contains_title_keyword(lowered):
                return line

        return None

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