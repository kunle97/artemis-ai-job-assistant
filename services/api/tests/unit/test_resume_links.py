"""
Resume link extractor tests.
"""

from src.domain.resume.extractors.links import ResumeLinkExtractor


def test_link_extractor_does_not_treat_mailto_as_portfolio():
    extractor = ResumeLinkExtractor()

    result = extractor.extract(
        text="""
        Contact me at mailto:jane@example.com
        GitHub https://github.com/janedoe
        """,
        file_path=None,
    )

    assert result["github_url"] == "https://github.com/janedoe"
    assert result["portfolio_url"] is None