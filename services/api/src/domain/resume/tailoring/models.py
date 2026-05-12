"""
Resume tailoring models.

Holds internal data structures used by the resume tailoring service.
"""

from dataclasses import dataclass, field


@dataclass
class TailoringContext:
    """Aggregated context required to generate tailoring recommendations."""

    resume_text: str
    profile_summary: str
    job_description: str
    job_title: str
    company_name: str
    skills: list[str] = field(default_factory=list)
