"""
Resume header extractor.

Extracts top-of-resume identity and contact signals such as name,
headline title, email, and phone number.
"""

from __future__ import annotations

import re

from src.domain.resume.constants import (
    EDUCATION_SECTION_HEADERS,
    EMAIL_PATTERN,
    EXPERIENCE_SECTION_HEADERS,
    EXTRA_SECTION_HEADERS,
    PHONE_PATTERN,
    SKILLS_SECTION_HEADERS,
    TITLE_KEYWORDS,
)


class ResumeHeaderExtractor:
    """
    Extract structured identity/contact fields from the header block.
    """

    def extract(self, lines: list[str]) -> dict:
        """
        Extract header fields from the top lines of a resume.
        """
        header_lines = self._extract_header_block(lines)

        return {
            "header_lines": header_lines,
            "full_name": self._extract_name(header_lines),
            "headline_title": self._extract_headline_title(header_lines),
            "email": self._extract_email(header_lines),
            "phone": self._extract_phone(header_lines),
        }

    def _extract_header_block(self, lines: list[str]) -> list[str]:
        headings = (
            EXPERIENCE_SECTION_HEADERS
            | EDUCATION_SECTION_HEADERS
            | SKILLS_SECTION_HEADERS
            | EXTRA_SECTION_HEADERS
        )

        header = []

        for line in lines[:12]:
            normalized = line.strip().lower()
            if normalized in headings:
                break
            header.append(line)

        return header

    def _extract_name(self, header_lines: list[str]) -> str | None:
        for line in header_lines[:4]:
            tokens = line.split()
            if not 2 <= len(tokens) <= 4:
                continue
            if "@" in line or "http" in line.lower():
                continue
            if any(char.isdigit() for char in line):
                continue

            capitalized_count = sum(1 for word in tokens if word[:1].isupper())
            if capitalized_count >= 2:
                return line

        return None

    def _extract_headline_title(self, header_lines: list[str]) -> str | None:
        for line in header_lines[:6]:
            segments = self._split_header_segments(line)

            for segment in segments:
                lowered = segment.lower()

                if "@" in lowered or "http" in lowered or "www." in lowered:
                    continue
                if PHONE_PATTERN.search(self._normalize_spacing(segment)):
                    continue
                if any(keyword in lowered for keyword in TITLE_KEYWORDS):
                    return self._normalize_spacing(segment)

        return None

    def _extract_email(self, header_lines: list[str]) -> str | None:
        header_text = self._normalize_spacing("\n".join(header_lines))
        match = EMAIL_PATTERN.search(header_text)
        return match.group(0) if match else None

    def _extract_phone(self, header_lines: list[str]) -> str | None:
        """
        Extract phone from the header block, prioritizing segmented header content.
        """
        for line in header_lines[:6]:
            for segment in self._split_header_segments(line):
                normalized_segment = self._normalize_spacing(segment)
                match = PHONE_PATTERN.search(normalized_segment)
                if match:
                    return match.group(0)

        header_text = self._normalize_spacing("\n".join(header_lines))
        match = PHONE_PATTERN.search(header_text)
        return match.group(0) if match else None

    def _split_header_segments(self, line: str) -> list[str]:
        if "|" in line:
            return [segment.strip() for segment in line.split("|") if segment.strip()]

        if "•" in line:
            return [segment.strip() for segment in line.split("•") if segment.strip()]

        return [line.strip()] if line.strip() else []

    def _normalize_spacing(self, text: str) -> str:
        """
        Collapse repeated whitespace commonly introduced by PDF extraction.
        """
        return re.sub(r"\s+", " ", text).strip()