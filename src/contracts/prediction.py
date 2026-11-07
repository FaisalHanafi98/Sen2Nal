"""Data contract for Agent 5 (Prediction) output."""

from datetime import date
from typing import Literal

from pydantic import Field, FiniteFloat

from src.contracts.base import StrictContract


class PredictionOutput(StrictContract):
    """Output schema for the Prediction Agent.

    XGBoost directional prediction with SHAP explainability.
    Direction: 1 = bullish, 0 = bearish.
    """

    ticker: str = Field(min_length=1, max_length=10)
    date: date
    direction: Literal[0, 1]
    probability: float = Field(ge=0.0, le=1.0)
    confidence: Literal["high", "medium", "low"]
    top_features: list[tuple[str, float]]
    model_version: str = Field(min_length=1)
    shap_json: dict[str, float]


class PredictionWrite(StrictContract):
    """Validated row for the existing prediction fact table."""

    stock_id: int = Field(gt=0)
    date_id: int = Field(gt=0)
    prediction_date: date
    target_date: date
    predicted_direction: Literal["UP", "DOWN", "NEUTRAL"]
    predicted_score: float = Field(ge=0, le=1)
    predicted_confidence: float = Field(ge=0, le=1)
    model_version: str = Field(min_length=1, max_length=20)
    feature_importance: dict[str, FiniteFloat]
