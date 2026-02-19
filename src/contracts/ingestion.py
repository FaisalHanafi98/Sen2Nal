"""Data contract for Agent 1 (Data Ingestion) output."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from src.contracts.base import StrictContract


class IngestionOutput(StrictContract):
    """Output schema for the Data Ingestion Agent.

    Represents a single fetched news article or social media post
    before sentiment processing.
    """

    source: Literal["alpha_vantage", "newsapi", "reddit", "yahoo", "finviz"]
    raw_text: str = Field(min_length=1)
    ticker_mentions: list[str] = Field(default_factory=list)
    published_at: datetime | None = None
    fetched_at: datetime
    external_id: str | None = None
    content_hash: str = Field(min_length=64, max_length=64)
