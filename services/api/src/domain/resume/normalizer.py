"""
Resume normalizer.

Transforms extracted raw resume text into a lightweight structured format
using generic, rule-based parsing heuristics. The goal is to support common
resume layouts without depending on one exact template.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.domain.resume.constants import (
    COMMON_SKILLS,
    DATE_RANGE_PATTERN,
    EDUCATION_SECTION_HEADERS,
    EMAIL_PATTERN,
    EXPERIENCE_SECTION_HEADERS,
    EXTRA_SECTION_HEADERS,
    MONTH_MAP,
    PHONE_PATTERN,
    SKILLS_SECTION_HEADERS,
    TITLE_KEYWORDS,
    URL_PATTERN,
    YEAR_RANGE_PATTERN,
)


@dataclass
class DateRange:
    """
    Represents a parsed work-date interval.
    """

    start_year: int
    start_month: int
    end_year: int
    end_month: int


class ResumeNormalizer:
    """
    Converts extracted resume text into structured fields using
    generic heuristics and fallback rules.
    """

    def normalize(self, extracted_text: str | None) -> dict:
        """
        Build a structured representation from raw resume text using
        generic heuristics and section-aware parsing.
        """
        if not extracted_text or not extracted_text.strip():
            return self._empty_result()

        lines = [line.strip() for line in extracted_text.splitlines() if line.strip()]
        lower_text = extracted_text.lower()

        header_lines = self._extract_header_block(lines)
        experience_lines = self._extract_section_lines(lines, EXPERIENCE_SECTION_HEADERS)
        education_lines = self._extract_section_lines(lines, EDUCATION_SECTION_HEADERS)

        urls = self._extract_urls(extracted_text)
        linkedin_url = self._find_url_containing(urls, "linkedin.com")
        github_url = self._find_url_containing(urls, "github.com")
        portfolio_url = self._find_portfolio_url(urls, linkedin_url, github_url)

        headline_title = self._extract_headline_title(header_lines)
        current_job_title = self._extract_current_job_title(experience_lines)
        date_ranges = self._extract_date_ranges(lines)
        years_experience = self._calculate_years_experience(date_ranges)

        return {
            "full_name": self._extract_name(header_lines, lines),
            "headline_title": headline_title,
            "current_job_title": current_job_title,
            "email": self._extract_email("\n".join(header_lines) or extracted_text),
            "phone": self._extract_phone("\n".join(header_lines) or extracted_text),
            "urls": urls,
            "linkedin_url": linkedin_url,
            "github_url": github_url,
            "portfolio_url": portfolio_url,
            "skills": self._extract_skills(lower_text),
            "summary": self._extract_summary(lines, header_lines),
            "experience_sections": experience_lines,
            "education_sections": education_lines,
            "date_ranges": [
                {
                    "start_year": item.start_year,
                    "start_month": item.start_month,
                    "end_year": item.end_year,
                    "end_month": item.end_month,
                }
                for item in date_ranges
            ],
            "years_experience": years_experience,
        }

    def _empty_result(self) -> dict:
        return {
            "full_name": None,
            "headline_title": None,
            "current_job_title": None,
            "email": None,
            "phone": None,
            "urls": [],
            "linkedin_url": None,
            "github_url": None,
            "portfolio_url": None,
            "skills": [],
            "summary": None,
            "experience_sections": [],
            "education_sections": [],
            "date_ranges": [],
            "years_experience": None,
        }

    def _extract_header_block(self, lines: list[str]) -> list[str]:
        """
        Extract the likely identity/header block from the top of the resume.
        Stops when it hits a clear section heading.
        """
        header = []

        for line in lines[:12]:
            normalized = line.strip().lower()
            if self._is_section_heading(normalized):
                break
            header.append(line)

        return header

    def _extract_name(self, header_lines: list[str], all_lines: list[str]) -> str | None:
        """
        Extract a likely candidate name from early resume lines.
        """
        candidate_lines = header_lines[:4] if header_lines else all_lines[:4]

        for line in candidate_lines:
            tokens = line.split()
            if not 2 <= len(tokens) <= 4:
                continue
            if "@" in line or "http" in line.lower():
                continue
            if any(char.isdigit() for char in line):
                continue
            if not self._looks_like_person_name(line):
                continue
            return line

        return None

    def _looks_like_person_name(self, line: str) -> bool:
        words = line.split()
        if not words:
            return False

        capitalized_count = sum(1 for word in words if word[:1].isupper())
        alpha_ratio = sum(char.isalpha() or char.isspace() for char in line) / max(len(line), 1)

        return capitalized_count >= 2 and alpha_ratio > 0.8

    def _extract_headline_title(self, header_lines: list[str]) -> str | None:
        """
        Extract a likely headline title from the header block.

        This supports lines where a title may appear alongside contact info,
        such as:
        "Full Stack Software Engineer | (555) 123-4567 | jane@example.com | ..."
        """
        for line in header_lines[:6]:
            segments = [segment.strip() for segment in line.split("|") if segment.strip()]

            for segment in segments:
                lowered = segment.lower()

                if "@" in lowered or "http" in lowered or "www." in lowered:
                    continue

                if self._contains_title_keyword(lowered):
                    return segment

        return None

    def _extract_current_job_title(self, experience_lines: list[str]) -> str | None:
        """
        Extract the current/most recent job title from the experience section.
        """
        for line in experience_lines[:10]:
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

    def _extract_email(self, text: str) -> str | None:
        match = EMAIL_PATTERN.search(text)
        return match.group(0) if match else None

    def _extract_phone(self, text: str) -> str | None:
        match = PHONE_PATTERN.search(text)
        return match.group(0) if match else None

    def _extract_urls(self, text: str) -> list[str]:
        urls = URL_PATTERN.findall(text)
        seen = []
        for url in urls:
            cleaned = url.rstrip(".,);]")
            if cleaned not in seen:
                seen.append(cleaned)
        return seen

    def _find_url_containing(self, urls: list[str], match_text: str) -> str | None:
        for url in urls:
            if match_text in url.lower():
                return url
        return None

    def _find_portfolio_url(
        self,
        urls: list[str],
        linkedin_url: str | None,
        github_url: str | None,
    ) -> str | None:
        for url in urls:
            if url == linkedin_url or url == github_url:
                continue
            return url
        return None

    def _extract_skills(self, lower_text: str) -> list[str]:
        found = []
        for skill in sorted(COMMON_SKILLS):
            if skill in lower_text:
                found.append(skill)
        return found

    def _extract_summary(self, lines: list[str], header_lines: list[str]) -> str | None:
        """
        Extract a lightweight summary from early non-contact, non-heading lines.
        """
        candidates = []

        for line in lines[:10]:
            lowered = line.lower()
            if line in header_lines and ("@" in line or "http" in lowered):
                continue
            if self._is_section_heading(lowered):
                break
            if len(line) < 30:
                continue
            if self._looks_like_date_line(line):
                continue
            if self._contains_title_keyword(lowered):
                continue
            candidates.append(line)

        return " ".join(candidates[:2]) if candidates else None

    def _extract_section_lines(self, lines: list[str], section_headers: set[str]) -> list[str]:
        """
        Extract the content lines following a matching section heading until the
        next major section heading.
        """
        collected = []
        inside_section = False

        for line in lines:
            normalized = line.strip().lower()

            if normalized in section_headers:
                inside_section = True
                continue

            if inside_section and self._is_section_heading(normalized):
                break

            if inside_section:
                collected.append(line)

        return collected

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

    def _contains_title_keyword(self, lowered_line: str) -> bool:
        return any(keyword in lowered_line for keyword in TITLE_KEYWORDS)

    def _looks_like_date_line(self, line: str) -> bool:
        return bool(DATE_RANGE_PATTERN.search(line) or YEAR_RANGE_PATTERN.search(line))

    def _extract_date_ranges(self, lines: list[str]) -> list[DateRange]:
        """
        Extract date ranges from work experience lines.
        """
        results = []

        for line in lines:
            month_match = DATE_RANGE_PATTERN.search(line)
            if month_match:
                start_month = self._month_to_int(month_match.group("start_month"))
                start_year = int(month_match.group("start_year"))

                end_year_raw = month_match.group("end_year")
                if end_year_raw.lower() in {"current", "present"}:
                    today = date.today()
                    end_year = today.year
                    end_month = today.month
                else:
                    end_year = int(end_year_raw)
                    end_month_raw = month_match.group("end_month")
                    end_month = self._month_to_int(end_month_raw) if end_month_raw else 12

                results.append(
                    DateRange(
                        start_year=start_year,
                        start_month=start_month,
                        end_year=end_year,
                        end_month=end_month,
                    )
                )
                continue

            year_match = YEAR_RANGE_PATTERN.search(line)
            if year_match:
                start_year = int(year_match.group("start_year"))
                end_year_raw = year_match.group("end_year")

                if end_year_raw.lower() in {"current", "present"}:
                    today = date.today()
                    end_year = today.year
                    end_month = today.month
                else:
                    end_year = int(end_year_raw)
                    end_month = 12

                results.append(
                    DateRange(
                        start_year=start_year,
                        start_month=1,
                        end_year=end_year,
                        end_month=end_month,
                    )
                )

        return self._merge_date_ranges(results)

    def _merge_date_ranges(self, ranges: list[DateRange]) -> list[DateRange]:
        """
        Merge overlapping/adjacent date ranges to avoid double-counting.
        """
        if not ranges:
            return []

        sorted_ranges = sorted(
            ranges,
            key=lambda item: (item.start_year, item.start_month, item.end_year, item.end_month),
        )

        merged = [sorted_ranges[0]]

        for current in sorted_ranges[1:]:
            previous = merged[-1]

            previous_end = previous.end_year * 12 + previous.end_month
            current_start = current.start_year * 12 + current.start_month
            current_end = current.end_year * 12 + current.end_month

            if current_start <= previous_end + 1:
                if current_end > previous_end:
                    previous.end_year = current.end_year
                    previous.end_month = current.end_month
            else:
                merged.append(current)

        return merged

    def _calculate_years_experience(self, ranges: list[DateRange]) -> int | None:
        """
        Calculate approximate total years of experience from merged intervals.
        """
        if not ranges:
            return None

        total_months = 0
        for item in ranges:
            start = item.start_year * 12 + item.start_month
            end = item.end_year * 12 + item.end_month
            total_months += max(0, end - start + 1)

        if total_months <= 0:
            return None

        return max(1, round(total_months / 12))

    def _month_to_int(self, month_text: str | None) -> int:
        if not month_text:
            return 1
        return MONTH_MAP[month_text.strip().lower()]