"""Data contract for Agent 1 (Data Ingestion) output."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, HttpUrl, NaiveDatetime

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


TickerMention = Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9.-]{0,9}$")]


class NewsWrite(StrictContract):
    """Validated fields for a staged NewsAPI article."""

    source: Literal["newsapi"]
    external_id: str | None = Field(max_length=100)
    headline: str = Field(min_length=1)
    summary: str | None = Field(max_length=500)
    url: HttpUrl | None
    published_at: NaiveDatetime | None
    tickers_mentioned: list[TickerMention] = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    is_processed: Literal[False]
    is_duplicate: Literal[False]


class RedditWrite(StrictContract):
    """Validated fields for a staged Reddit submission."""

    subreddit: str = Field(min_length=1, max_length=50)
    post_id: str = Field(min_length=1, max_length=20)
    post_type: Literal["submission"]
    title: str | None = Field(max_length=500)
    body: str | None = Field(max_length=2000)
    author: str | None = Field(max_length=50)
    score: int = Field(ge=-(2**31), le=2**31 - 1)
    num_comments: int = Field(ge=0, le=2**31 - 1)
    created_utc: NaiveDatetime
    tickers_mentioned: list[TickerMention] = Field(min_length=1)
    is_processed: Literal[False]
