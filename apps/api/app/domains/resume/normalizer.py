"""
Resume normalizer.

Transforms extracted raw resume text into a lightweight structured format
using deterministic rule-based parsing. This is the first normalization
layer before any future AI-assisted enrichment.
"""

from __future__ import annotations

import re


class ResumeNormalizer:
    """
    Converts extracted resume text into structured fields.
    """

    EMAIL_PATTERN = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
    PHONE_PATTERN = re.compile(
        r"(\+?\d{1,2}[\s\-.]?)?(\(?\d{3}\)?[\s\-.]?)\d{3}[\s\-.]?\d{4}"
    )
    URL_PATTERN = re.compile(r"https?://[^\s]+|www\.[^\s]+")

    COMMON_SKILLS = {
        "python",
        "django",
        "fastapi",
        "flask",
        "javascript",
        "typescript",
        "react",
        "next.js",
        "nextjs",
        "node.js",
        "nodejs",
        "express",
        "postgresql",
        "mysql",
        "sqlite",
        "docker",
        "kubernetes",
        "aws",
        "redis",
        "graphql",
        "java",
        "spring boot",
        "tailwind",
        "html",
        "css",
        "cypress",
        "playwright",
        "git",
    }

    def normalize(self, extracted_text: str | None) -> dict:
        """
        Build a lightweight structured representation from raw resume text.
        """
        if not extracted_text or not extracted_text.strip():
            return {
                "full_name": None,
                "email": None,
                "phone": None,
                "urls": [],
                "skills": [],
                "summary": None,
                "experience_sections": [],
                "education_sections": [],
            }

        lines = [line.strip() for line in extracted_text.splitlines() if line.strip()]
        lower_text = extracted_text.lower()

        return {
            "full_name": self._extract_name(lines),
            "email": self._extract_email(extracted_text),
            "phone": self._extract_phone(extracted_text),
            "urls": self._extract_urls(extracted_text),
            "skills": self._extract_skills(lower_text),
            "summary": self._extract_summary(lines),
            "experience_sections": self._extract_section_lines(lines, "experience"),
            "education_sections": self._extract_section_lines(lines, "education"),
        }

    def _extract_name(self, lines: list[str]) -> str | None:
        """
        Use the first plausible line as the candidate's name.
        """
        if not lines:
            return None

        first_line = lines[0]

        if len(first_line.split()) < 2 or len(first_line.split()) > 5:
            return None

        if "@" in first_line or "http" in first_line.lower():
            return None

        return first_line

    def _extract_email(self, text: str) -> str | None:
        match = self.EMAIL_PATTERN.search(text)
        return match.group(0) if match else None

    def _extract_phone(self, text: str) -> str | None:
        match = self.PHONE_PATTERN.search(text)
        return match.group(0) if match else None

    def _extract_urls(self, text: str) -> list[str]:
        urls = self.URL_PATTERN.findall(text)
        seen = []
        for url in urls:
            if url not in seen:
                seen.append(url)
        return seen

    def _extract_skills(self, lower_text: str) -> list[str]:
        found = []
        for skill in sorted(self.COMMON_SKILLS):
            if skill in lower_text:
                found.append(skill)
        return found

    def _extract_summary(self, lines: list[str]) -> str | None:
        """
        Return a short early-career summary from the first few lines
        after the name/contact block.
        """
        if len(lines) < 3:
            return None

        summary_candidates = []
        for line in lines[1:6]:
            lowered = line.lower()
            if "@" in line or "http" in lowered:
                continue
            if len(line) < 25:
                continue
            summary_candidates.append(line)

        return " ".join(summary_candidates[:2]) if summary_candidates else None

    def _extract_section_lines(self, lines: list[str], section_name: str) -> list[str]:
        """
        Extract a few lines following a section header like EXPERIENCE or EDUCATION.
        """
        target = section_name.lower()
        collected = []

        for index, line in enumerate(lines):
            if target in line.lower():
                next_lines = lines[index + 1:index + 6]
                for next_line in next_lines:
                    if next_line.isupper() and next_line.lower() != target:
                        break
                    collected.append(next_line)
                break

        return collected