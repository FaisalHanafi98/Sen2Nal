"""Data contract for Agent 2 (Sentiment Analysis) output."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from src.contracts.base import StrictContract


class SentimentScore(StrictContract):
    """Validated score and provenance for one article or post."""

    sentiment_score: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    model_used: Literal["finbert", "vader"]
    processing_timestamp: datetime


class SentimentOutput(SentimentScore):
    """Ticker-level sentiment output with the number of contributing sources."""

    ticker: str = Field(min_length=1, max_length=10)
    source_count: int = Field(ge=0)
