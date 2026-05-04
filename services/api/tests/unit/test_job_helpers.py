"""
Unit tests for job helper utilities.

Covers title keyword filtering behavior used by job ingestion.
"""

from src.domain.jobs.helpers import filter_job_by_title


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
