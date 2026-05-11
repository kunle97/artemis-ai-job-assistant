"""
Application pattern analysis service.

Aggregates historical application data for a user and produces
structured analytics: outcome breakdown, funnel, score comparison,
time trends, and actionable recommendations.

Adapted from the career-ops ``analyze-patterns.mjs`` pattern detector,
translated to Python and aligned with Artemis status vocabulary.
"""

import logging
from collections import defaultdict
from datetime import date

from src.domain.applications.analytics.schemas import (
    ApplicationPatternsResponse,
    FunnelEntry,
    OutcomeSummary,
    Recommendation,
    ScoreByOutcome,
    ScoreStats,
    TrendPoint,
)

logger = logging.getLogger(__name__)

# Minimum number of applications (in a meaningful state) required before
# we can produce reliable analytics.
MIN_THRESHOLD = 5

# Artemis statuses that indicate a meaningful submission attempt.
# These are excluded from the "trivial" pre-pipeline count.
_PIPELINE_OR_LATER = frozenset({
    "queued", "inspecting", "inspected", "planning", "planned",
    "filling", "filled", "awaiting_submission",
    "submitted", "applied",
    "interviewing", "offer_received", "offer_accepted",
    "rejected", "archived",
})

# Outcome classification — adapted from career-ops classifyOutcome()
_POSITIVE_STATUSES = frozenset({
    "interviewing", "offer_received", "offer_accepted", "applied",
})
_NEGATIVE_STATUSES = frozenset({"rejected"})
_SELF_FILTERED_STATUSES = frozenset({"archived"})

# Canonical funnel order for display
_FUNNEL_ORDER = [
    "queued", "inspecting", "planned", "filled",
    "awaiting_submission", "submitted", "applied",
    "interviewing", "offer_received", "offer_accepted",
    "rejected", "archived",
]


def _classify_outcome(status: str) -> str:
    """Classify an Artemis status into a career-ops outcome bucket."""
    s = status.strip().lower()
    if s in _POSITIVE_STATUSES:
        return "positive"
    if s in _NEGATIVE_STATUSES:
        return "negative"
    if s in _SELF_FILTERED_STATUSES:
        return "self_filtered"
    return "pending"


def _score_stats(scores: list[float]) -> ScoreStats:
    """Compute descriptive statistics for a list of scores."""
    if not scores:
        return ScoreStats(avg=0.0, min=0.0, max=0.0, count=0)
    avg = sum(scores) / len(scores)
    return ScoreStats(
        avg=round(avg, 2),
        min=round(min(scores), 2),
        max=round(max(scores), 2),
        count=len(scores),
    )


class ApplicationPatternService:
    """
    Computes per-user application pattern analytics from historical records.
    """

    def __init__(self, repository):
        self.repository = repository

    def compute_patterns(self, user_id) -> ApplicationPatternsResponse:
        """
        Produce a full analytics payload for the authenticated user.

        Returns an ``is_sufficient_data=False`` response when fewer than
        ``MIN_THRESHOLD`` applications have progressed past the initial
        saved/queued states.
        """
        logger.info(
            "[ApplicationPatternService] compute_patterns start user_id=%s", user_id
        )

        today = date.today().isoformat()
        applications = self.repository.list_applications_by_user(user_id)

        total = len(applications)
        meaningful = [
            app for app in applications
            if app.status in _PIPELINE_OR_LATER
        ]

        logger.info(
            "[ApplicationPatternService] compute_patterns found total=%d meaningful=%d",
            total,
            len(meaningful),
        )

        if len(meaningful) < MIN_THRESHOLD:
            return ApplicationPatternsResponse(
                analysis_date=today,
                total_applications=total,
                is_sufficient_data=False,
                minimum_threshold=MIN_THRESHOLD,
                insufficient_data_message=(
                    f"Not enough data: {len(meaningful)}/{MIN_THRESHOLD} applications "
                    "have progressed past the initial state. Keep applying and check back later."
                ),
            )

        # Enrich with scores
        app_ids = [str(app.id) for app in meaningful]
        score_map = self.repository.list_scores_for_applications(app_ids)

        # Classify outcomes and collect scores per outcome group
        scores_by_outcome: dict[str, list[float]] = defaultdict(list)
        funnel_counts: dict[str, int] = defaultdict(int)
        trend_data: dict[str, dict] = defaultdict(lambda: {"total": 0, "positive": 0})

        for app in meaningful:
            outcome = _classify_outcome(app.status)
            funnel_counts[app.status] += 1

            score = score_map.get(str(app.id))
            if score is not None:
                scores_by_outcome[outcome].append(score)

            # Trend: group by YYYY-MM from created_at
            period = app.created_at.strftime("%Y-%m")
            trend_data[period]["total"] += 1
            if outcome == "positive":
                trend_data[period]["positive"] += 1

        # --- Outcome summary ---
        outcome_counts: dict[str, int] = defaultdict(int)
        for app in meaningful:
            outcome_counts[_classify_outcome(app.status)] += 1

        outcome_summary = OutcomeSummary(
            total=len(meaningful),
            positive=outcome_counts["positive"],
            negative=outcome_counts["negative"],
            self_filtered=outcome_counts["self_filtered"],
            pending=outcome_counts["pending"],
        )

        # --- Funnel ---
        funnel = [
            FunnelEntry(
                status=status,
                count=funnel_counts[status],
                percentage=round((funnel_counts[status] / len(meaningful)) * 100),
            )
            for status in _FUNNEL_ORDER
            if funnel_counts.get(status, 0) > 0
        ]

        # --- Score by outcome ---
        score_by_outcome = ScoreByOutcome(
            positive=_score_stats(scores_by_outcome["positive"]),
            negative=_score_stats(scores_by_outcome["negative"]),
            self_filtered=_score_stats(scores_by_outcome["self_filtered"]),
            pending=_score_stats(scores_by_outcome["pending"]),
        )

        # --- Trend over time ---
        trend = sorted(
            [
                TrendPoint(
                    period=period,
                    total=data["total"],
                    positive=data["positive"],
                    conversion_rate=(
                        round((data["positive"] / data["total"]) * 100)
                        if data["total"] > 0
                        else 0
                    ),
                )
                for period, data in trend_data.items()
            ],
            key=lambda t: t.period,
        )

        # --- Recommendations ---
        recommendations = _generate_recommendations(
            outcome_counts=outcome_counts,
            score_by_outcome=score_by_outcome,
            total=len(meaningful),
        )

        logger.info(
            "[ApplicationPatternService] compute_patterns complete user_id=%s "
            "total=%d positive=%d negative=%d recommendations=%d",
            user_id,
            len(meaningful),
            outcome_counts["positive"],
            outcome_counts["negative"],
            len(recommendations),
        )

        return ApplicationPatternsResponse(
            analysis_date=today,
            total_applications=total,
            is_sufficient_data=True,
            minimum_threshold=MIN_THRESHOLD,
            outcome_summary=outcome_summary,
            funnel=funnel,
            score_by_outcome=score_by_outcome,
            trend=trend,
            recommendations=recommendations,
        )


def _generate_recommendations(
    outcome_counts: dict[str, int],
    score_by_outcome: ScoreByOutcome,
    total: int,
) -> list[Recommendation]:
    """
    Generate actionable recommendations from observed outcome patterns.

    Adapted from the career-ops recommendation engine; aligned to
    Artemis status vocabulary and available data dimensions.
    """
    recommendations: list[Recommendation] = []
    positive = outcome_counts.get("positive", 0)
    negative = outcome_counts.get("negative", 0)

    # Conversion rate signal
    conversion_rate = round((positive / total) * 100) if total > 0 else 0

    # Low conversion with sufficient rejections
    if negative >= 3 and conversion_rate < 20:
        recommendations.append(Recommendation(
            action="Review your job targeting criteria — fewer than 1 in 5 applications are progressing",
            reasoning=(
                f"{negative} of {total} applications resulted in rejection. "
                "Focus on roles where your profile is a strong match."
            ),
            impact="high",
        ))

    # Score threshold signal: if negative outcomes have higher avg scores than positive
    neg_avg = score_by_outcome.negative.avg
    pos_avg = score_by_outcome.positive.avg
    if (
        score_by_outcome.negative.count >= 2
        and score_by_outcome.positive.count >= 1
        and neg_avg > pos_avg
    ):
        recommendations.append(Recommendation(
            action="Fit score alone may not predict outcomes — consider other factors like cover letter quality",
            reasoning=(
                f"Rejected applications averaged {neg_avg}/5 vs "
                f"{pos_avg}/5 for positive outcomes, suggesting score is not the primary differentiator."
            ),
            impact="medium",
        ))

    # Zero positive outcomes
    if positive == 0 and total >= MIN_THRESHOLD:
        recommendations.append(Recommendation(
            action="No positive outcomes yet — prioritize applications with a fit score above 3.5/5",
            reasoning=(
                f"After {total} applications, none have reached interview or offer stage. "
                "Raising your score threshold filters out lower-probability opportunities."
            ),
            impact="high",
        ))

    # High pending ratio (too many stalled applications)
    pending = outcome_counts.get("pending", 0)
    if pending > 0 and total > 0 and (pending / total) > 0.5:
        recommendations.append(Recommendation(
            action="Follow up on pending applications — more than half have no outcome yet",
            reasoning=(
                f"{pending} of {total} applications are pending a response. "
                "Proactive follow-up often improves response rates."
            ),
            impact="medium",
        ))

    return recommendations
