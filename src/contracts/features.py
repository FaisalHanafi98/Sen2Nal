"""Data contract for Agent 4 (Feature Engineering) output."""

from datetime import date, datetime

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
