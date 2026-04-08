"""
Resume normalizer.

Transforms extracted raw resume text into a lightweight structured format
by orchestrating specialized resume extractors.
"""

from __future__ import annotations

from src.domain.resume.constants import COMMON_SKILLS
from src.domain.resume.extractors.dates import ResumeDateExtractor
from src.domain.resume.extractors.header import ResumeHeaderExtractor
from src.domain.resume.extractors.links import ResumeLinkExtractor
from src.domain.resume.extractors.sections import ResumeSectionExtractor


class ResumeNormalizer:
    """
    Converts extracted resume text into structured fields using
    specialized extractor modules.
    """

    def __init__(self):
        self.header_extractor = ResumeHeaderExtractor()
        self.section_extractor = ResumeSectionExtractor()
        self.link_extractor = ResumeLinkExtractor()
        self.date_extractor = ResumeDateExtractor()

    def normalize(self, extracted_text: str | None, file_path: str | None = None) -> dict:
        """
        Build a structured representation from raw resume text.
        """
        if not extracted_text or not extracted_text.strip():
            return self._empty_result()

        lines = [line.strip() for line in extracted_text.splitlines() if line.strip()]
        lower_text = extracted_text.lower()

        header_data = self.header_extractor.extract(lines)
        section_data = self.section_extractor.extract(lines, header_data["header_lines"])
        link_data = self.link_extractor.extract(extracted_text, file_path=file_path)
        date_data = self.date_extractor.extract(lines)

        return {
            "full_name": header_data["full_name"],
            "headline_title": header_data["headline_title"],
            "current_job_title": section_data["current_job_title"],
            "email": header_data["email"],
            "phone": header_data["phone"],
            "urls": link_data["urls"],
            "linkedin_url": link_data["linkedin_url"],
            "github_url": link_data["github_url"],
            "portfolio_url": link_data["portfolio_url"],
            "skills": self._extract_skills(lower_text),
            "summary": section_data["summary"],
            "experience_sections": section_data["experience_sections"],
            "education_sections": section_data["education_sections"],
            "date_ranges": date_data["date_ranges"],
            "years_experience": date_data["years_experience"],
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

    def _extract_skills(self, lower_text: str) -> list[str]:
        found = []

        for skill in sorted(COMMON_SKILLS):
            if skill in lower_text:
                found.append(skill)

        return found