"""
Resume date extractor.

Extracts experience date ranges from resume text and computes approximate
years of professional experience.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.domain.resume.constants import DATE_RANGE_PATTERN, MONTH_MAP, YEAR_RANGE_PATTERN


@dataclass
class DateRange:
    """
    Represents a parsed work-date interval.
    """

    start_year: int
    start_month: int
    end_year: int
    end_month: int


class ResumeDateExtractor:
    """
    Extract and normalize date intervals from a resume.
    """

    def extract(self, lines: list[str]) -> dict:
        """
        Extract parsed date ranges and compute years of experience.
        """
        date_ranges = self._extract_date_ranges(lines)
        years_experience = self._calculate_years_experience(date_ranges)

        return {
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

    def _extract_date_ranges(self, lines: list[str]) -> list[DateRange]:
        """
        Extract date ranges from resume lines.
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
        Merge overlapping or adjacent date ranges to avoid double-counting.
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