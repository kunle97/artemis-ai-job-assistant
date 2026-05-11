"""
Application analytics schemas.

Pydantic response models for the GET /applications/patterns endpoint.
"""

from pydantic import BaseModel


class OutcomeSummary(BaseModel):
    """Breakdown of application outcomes by classification."""

    total: int
    positive: int
    negative: int
    self_filtered: int
    pending: int


class ScoreStats(BaseModel):
    """Descriptive statistics for a score group."""

    avg: float
    min: float
    max: float
    count: int


class ScoreByOutcome(BaseModel):
    """Score statistics grouped by application outcome."""

    positive: ScoreStats
    negative: ScoreStats
    self_filtered: ScoreStats
    pending: ScoreStats


class FunnelEntry(BaseModel):
    """A single stage in the application funnel."""

    status: str
    count: int
    percentage: int


class TrendPoint(BaseModel):
    """Aggregated application volume and conversion for a time period."""

    period: str
    total: int
    positive: int
    conversion_rate: int


class Recommendation(BaseModel):
    """An actionable recommendation derived from observed patterns."""

    action: str
    reasoning: str
    impact: str


class ApplicationPatternsResponse(BaseModel):
    """
    Full analytics payload returned by GET /applications/patterns.

    When ``is_sufficient_data`` is False, all analysis fields are None and
    ``insufficient_data_message`` explains how many more applications are needed.
    """

    analysis_date: str
    total_applications: int
    is_sufficient_data: bool
    minimum_threshold: int
    insufficient_data_message: str | None = None
    outcome_summary: OutcomeSummary | None = None
    funnel: list[FunnelEntry] | None = None
    score_by_outcome: ScoreByOutcome | None = None
    trend: list[TrendPoint] | None = None
    recommendations: list[Recommendation] | None = None
