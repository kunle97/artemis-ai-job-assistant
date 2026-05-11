"""
Unit tests for ApplicationPatternService and its helpers.

Tests cover outcome classification, descriptive statistics, the
insufficient-data guard, and recommendation generation rules.
"""

import uuid
from datetime import datetime, UTC
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.domain.applications.analytics.service import (
    MIN_THRESHOLD,
    ApplicationPatternService,
    _classify_outcome,
    _generate_recommendations,
    _score_stats,
)
from src.domain.applications.analytics.schemas import ScoreByOutcome, ScoreStats


# ---------------------------------------------------------------------------
# _classify_outcome
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status,expected",
    [
        ("applied", "positive"),
        ("interviewing", "positive"),
        ("offer_received", "positive"),
        ("offer_accepted", "positive"),
        ("rejected", "negative"),
        ("archived", "self_filtered"),
        ("queued", "pending"),
        ("inspecting", "pending"),
        ("planned", "pending"),
        ("filled", "pending"),
        ("awaiting_submission", "pending"),
        ("submitted", "pending"),
        ("saved", "pending"),  # not in _PIPELINE_OR_LATER but classify still maps it
    ],
)
def test_classify_outcome(status, expected):
    assert _classify_outcome(status) == expected


# ---------------------------------------------------------------------------
# _score_stats
# ---------------------------------------------------------------------------


def test_score_stats_empty():
    stats = _score_stats([])
    assert stats.count == 0
    assert stats.avg == 0.0
    assert stats.min == 0.0
    assert stats.max == 0.0


def test_score_stats_single():
    stats = _score_stats([4.0])
    assert stats.count == 1
    assert stats.avg == 4.0
    assert stats.min == 4.0
    assert stats.max == 4.0


def test_score_stats_multiple():
    stats = _score_stats([3.0, 4.0, 5.0])
    assert stats.count == 3
    assert stats.avg == pytest.approx(4.0)
    assert stats.min == 3.0
    assert stats.max == 5.0


# ---------------------------------------------------------------------------
# ApplicationPatternService.compute_patterns — sparse guard
# ---------------------------------------------------------------------------


def _make_app(status, user_id=None, created_at=None):
    """Build a minimal mock Application."""
    app = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user_id or uuid.uuid4(),
        status=status,
        created_at=created_at or datetime(2024, 6, 1, tzinfo=UTC),
    )
    return app


def _build_service(apps, score_map=None):
    """Wire a service with a mock repository."""
    repo = MagicMock()
    repo.list_applications_by_user.return_value = apps
    repo.list_scores_for_applications.return_value = score_map or {}
    return ApplicationPatternService(repository=repo)


def test_compute_patterns_insufficient_data_below_threshold():
    """Fewer than MIN_THRESHOLD meaningful apps → is_sufficient_data=False."""
    user_id = uuid.uuid4()
    apps = [_make_app("applied", user_id=user_id) for _ in range(MIN_THRESHOLD - 1)]

    service = _build_service(apps)
    result = service.compute_patterns(user_id=user_id)

    assert result.is_sufficient_data is False
    assert result.outcome_summary is None
    assert result.funnel is None
    assert result.recommendations is None
    assert result.minimum_threshold == MIN_THRESHOLD


def test_compute_patterns_non_meaningful_statuses_do_not_count():
    """Applications in 'saved' status are not in _PIPELINE_OR_LATER and shouldn't count."""
    user_id = uuid.uuid4()
    # 10 total but none are meaningful
    apps = [_make_app("saved", user_id=user_id) for _ in range(10)]

    service = _build_service(apps)
    result = service.compute_patterns(user_id=user_id)

    assert result.is_sufficient_data is False
    assert result.total_applications == 10


def test_compute_patterns_full_response_shape():
    """With sufficient meaningful applications the response is fully populated."""
    user_id = uuid.uuid4()
    statuses = ["applied", "interviewing", "rejected", "rejected", "rejected"]
    apps = [_make_app(s, user_id=user_id) for s in statuses]

    score_map = {str(app.id): 3.5 for app in apps}
    service = _build_service(apps, score_map=score_map)
    result = service.compute_patterns(user_id=user_id)

    assert result.is_sufficient_data is True
    assert result.outcome_summary is not None
    assert result.outcome_summary.total == len(statuses)
    assert result.outcome_summary.positive == 2  # applied + interviewing
    assert result.outcome_summary.negative == 3  # three rejected
    assert result.funnel is not None
    assert result.trend is not None
    assert result.score_by_outcome is not None


def test_compute_patterns_correct_outcome_counts():
    user_id = uuid.uuid4()
    statuses = [
        "applied",         # positive
        "interviewing",    # positive
        "offer_received",  # positive
        "rejected",        # negative
        "archived",        # self_filtered
    ]
    apps = [_make_app(s, user_id=user_id) for s in statuses]

    service = _build_service(apps)
    result = service.compute_patterns(user_id=user_id)

    summary = result.outcome_summary
    assert summary.positive == 3
    assert summary.negative == 1
    assert summary.self_filtered == 1
    assert summary.pending == 0


# ---------------------------------------------------------------------------
# _generate_recommendations
# ---------------------------------------------------------------------------


def _score_by_outcome(pos_avg=4.0, neg_avg=2.0, pos_count=2, neg_count=2):
    return ScoreByOutcome(
        positive=ScoreStats(avg=pos_avg, min=pos_avg, max=pos_avg, count=pos_count),
        negative=ScoreStats(avg=neg_avg, min=neg_avg, max=neg_avg, count=neg_count),
        self_filtered=ScoreStats(avg=0.0, min=0.0, max=0.0, count=0),
        pending=ScoreStats(avg=0.0, min=0.0, max=0.0, count=0),
    )


def test_recommendations_low_conversion_triggers_high():
    """3+ rejections and <20% conversion → high-impact targeting recommendation."""
    # 1 positive + 4 negative = 5 total → 20% conversion (exactly at threshold, won't trigger)
    # So we need 0 positive + 3+ negative to get <20%
    outcome_counts = {"positive": 0, "negative": 4, "self_filtered": 0, "pending": 1}
    recs = _generate_recommendations(
        outcome_counts=outcome_counts,
        score_by_outcome=_score_by_outcome(neg_count=4, pos_count=0),
        total=5,
    )
    impacts = [r.impact for r in recs]
    # With 0 positive outcomes, we should get a high-impact "no positive" recommendation
    assert "high" in impacts


def test_recommendations_zero_positive_triggers_high():
    """No positive outcomes after threshold → high-impact score threshold recommendation."""
    outcome_counts = {"positive": 0, "negative": 3, "self_filtered": 0, "pending": 2}
    recs = _generate_recommendations(
        outcome_counts=outcome_counts,
        score_by_outcome=_score_by_outcome(pos_count=0, neg_count=3),
        total=5,
    )
    impacts = [r.impact for r in recs]
    assert "high" in impacts


def test_recommendations_high_pending_ratio_triggers_medium():
    """More than 50% pending → medium-impact follow-up recommendation."""
    outcome_counts = {"positive": 1, "negative": 0, "self_filtered": 0, "pending": 4}
    recs = _generate_recommendations(
        outcome_counts=outcome_counts,
        score_by_outcome=_score_by_outcome(pos_count=1, neg_count=0),
        total=5,
    )
    impacts = {r.impact for r in recs}
    assert "medium" in impacts


def test_recommendations_good_profile_no_recs():
    """Healthy conversion rate and no concerning patterns → empty recommendations."""
    outcome_counts = {"positive": 4, "negative": 0, "self_filtered": 0, "pending": 1}
    recs = _generate_recommendations(
        outcome_counts=outcome_counts,
        score_by_outcome=_score_by_outcome(pos_avg=4.5, neg_avg=0.0, pos_count=4, neg_count=0),
        total=5,
    )
    assert recs == []
