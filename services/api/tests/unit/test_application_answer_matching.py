"""
Application answer matching tests.
"""

from src.domain.application_answers.matching.normalizer import QuestionTextNormalizer
from src.domain.application_answers.matching.service import ApplicationAnswerMatcher


def test_question_text_normalizer_handles_case_spacing_and_punctuation():
    normalizer = QuestionTextNormalizer()

    result = normalizer.normalize(
        " What are the three most important factors you’re looking for in your next role?* "
    )

    assert result == "what are the three most important factors you're looking for in your next role"


def test_matcher_maps_known_variant_to_canonical_key():
    matcher = ApplicationAnswerMatcher()

    result = matcher.match_question_to_key(
        "What are the three most important factors you’re looking for in your next role?*"
    )

    assert result == "next_role_priorities"


def test_matcher_handles_proudest_accomplishment_variant():
    matcher = ApplicationAnswerMatcher()

    result = matcher.match_question_to_key(
        "Tell us about a project or accomplishment you're most proud of, and why?"
    )

    assert result == "proudest_accomplishment"


def test_matcher_returns_none_for_unknown_question():
    matcher = ApplicationAnswerMatcher()

    result = matcher.match_question_to_key(
        "What is your favorite database migration strategy?"
    )

    assert result is None