"""
Resume normalizer tests.

Verifies deterministic extraction of common structured resume fields.
"""

from src.domain.resume.normalizer import ResumeNormalizer


def test_normalize_extracts_basic_fields():
    normalizer = ResumeNormalizer()

    text = """
    Jane Doe
    Full Stack Software Engineer | (555) 123-4567 | jane@example.com | https://github.com/janedoe

    SKILLS
    Python, React, Django, Docker

    EXPERIENCE
    Example Corp
    Senior Software Engineer
    Jan 2020 - Current
    Built backend services with FastAPI and PostgreSQL.

    EDUCATION
    State University
    B.S. in Computer Science
    """

    result = normalizer.normalize(text)

    assert result["full_name"] == "Jane Doe"
    assert result["headline_title"] == "Full Stack Software Engineer"
    assert result["email"] == "jane@example.com"
    assert result["phone"] is not None
    assert "https://github.com/janedoe" in result["urls"]
    assert "python" in result["skills"]
    assert result["years_experience"] is not None


def test_normalize_returns_empty_shape_for_blank_input():
    normalizer = ResumeNormalizer()

    result = normalizer.normalize("")

    assert result["full_name"] is None
    assert result["email"] is None
    assert result["skills"] == []
    assert result["years_experience"] is None