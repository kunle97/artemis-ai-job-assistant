"""
Resume header extractor tests.
"""

from src.domain.resume.extractors.header import ResumeHeaderExtractor


def test_header_extractor_handles_extra_pdf_spacing_in_phone():
    extractor = ResumeHeaderExtractor()

    lines = [
        "Jane Doe",
        "Full  Stack  Software  Engineer  |  (555) 919-8872  |  jane@example.com  |  GitHub",
        "SKILLS",
    ]

    result = extractor.extract(lines)

    assert result["full_name"] == "Jane Doe"
    assert result["headline_title"] == "Full Stack Software Engineer"
    assert result["email"] == "jane@example.com"
    assert result["phone"] == "(555) 919-8872"