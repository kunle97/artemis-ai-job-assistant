"""
Unit tests for job helper utilities.

Covers title and location preference matching used by job ingestion.
"""

from src.domain.jobs.helpers import filter_job_by_title, matches_job_location


def test_filter_job_by_title_all_positive_match():
    assert filter_job_by_title(
        title="Senior Python Backend Engineer",
        positive=["python", "backend"],
        negative=[],
    )


def test_filter_job_by_title_partial_positive_match():
    assert filter_job_by_title(
        title="Senior Platform Engineer",
        positive=["platform", "golang"],
        negative=[],
    )


def test_filter_job_by_title_negative_blocks_match():
    assert not filter_job_by_title(
        title="Senior Platform Engineer",
        positive=["platform"],
        negative=["senior"],
    )


def test_filter_job_by_title_empty_positive_list():
    assert filter_job_by_title(
        title="People Operations Specialist",
        positive=[],
        negative=["intern"],
    )


def test_filter_job_by_title_empty_positive_and_negative_lists():
    assert filter_job_by_title(
        title="Any Job Title",
        positive=[],
        negative=[],
    )


def test_matches_job_location_matches_new_york_aliases():
    assert matches_job_location("NYC-Privy", ["New York, NY"])


def test_matches_job_location_matches_new_york_city_text():
    assert matches_job_location("New York City", ["New York, NY"])


def test_matches_job_location_matches_san_francisco_variants():
    assert matches_job_location(
        "San Francisco, California, United States",
        ["San Francisco, CA"],
    )


def test_matches_job_location_matches_mexico_city_variants():
    assert matches_job_location("Mexico City", ["Mexico City, MX"])


def test_matches_job_location_rejects_other_locations():
    assert not matches_job_location("San Francisco, California, United States", ["New York, NY"])
