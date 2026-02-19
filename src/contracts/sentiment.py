"""Data contract for Agent 2 (Sentiment Analysis) output."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from src.contracts.base import StrictContract


class SentimentOutput(StrictContract):
    """Output schema for the Sentiment Analysis Agent.

    Represents a scored article/post with sentiment classification.
    Score range: -1.0 (bearish) to +1.0 (bullish).
    """

    ticker: str = Field(min_length=1, max_length=10)
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    source_count: int = Field(ge=0)
    model_used: Literal["finbert", "vader"]
    processing_timestamp: datetime
