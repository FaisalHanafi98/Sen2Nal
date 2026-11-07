"""Data contract for Agent 4 (Feature Engineering) output."""

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import Field

from src.contracts.base import StrictContract


class FeatureOutput(StrictContract):
    """Output schema for the Feature Engineering Agent.

    Combined feature vector from sentiment, calendar, and market signals.
    Every feature is named for SHAP explainability.
    """

    ticker: str = Field(min_length=1, max_length=10)
    date: date
    feature_vector: dict[str, float]
    feature_timestamp: datetime
    data_completeness: float = Field(ge=0.0, le=1.0)
    shap_values: dict[str, float] = Field(default_factory=dict)


SignedScore = Annotated[float, Field(ge=-1.0, le=1.0)]
UnitScore = Annotated[float, Field(ge=0.0, le=1.0)]


class FeatureWrite(StrictContract):
    """Feature record written to the daily sentiment fact table."""

    stock_id: int = Field(gt=0)
    date_id: int = Field(gt=0)
    nlp_score: SignedScore
    nlp_score_prev: SignedScore | None
    nlp_momentum: float | None = Field(ge=-2.0, le=2.0)
    nlp_trend_days: int
    nlp_confidence: UnitScore
    news_score: SignedScore | None
    news_count: int = Field(ge=0)
    reddit_score: SignedScore | None
    reddit_count: int = Field(ge=0)
    calendar_score: SignedScore
    month_avg_return: SignedScore
    month_win_rate: UnitScore
    days_to_earnings: int | None = Field(ge=0)
    combined_score: UnitScore
    signal: Literal["STRONG_BUY", "BUY", "HOLD", "AVOID"]
    confidence: UnitScore
    conflict_flag: bool
    conflict_reason: str | None
    pipeline_run_id: str = Field(min_length=1, max_length=50)
