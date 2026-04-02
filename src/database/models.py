"""
SQLAlchemy ORM models for Sen2Nal database schema.

Schema follows star design:
- Dimension tables (dim_*): Reference data
- Fact tables (fact_*): Transactional/metrics data
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import BIGINT, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database.connection import Base


# =============================================================================
# DIMENSION TABLES
# =============================================================================


class DimStock(Base):
    """S&P 500 stock master data."""

    __tablename__ = "dim_stocks"

    stock_id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, unique=True, index=True)
    company_name = Column(String(255), nullable=False)
    sector = Column(String(100), nullable=False, index=True)
    industry = Column(String(100))
    market_cap = Column(BIGINT)  # In USD
    sp500_rank = Column(Integer, index=True)  # 1-500 by market cap
    cik = Column(String(20))  # SEC identifier
    isin = Column(String(20))  # International identifier
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    sentiments = relationship("FactSentiment", back_populates="stock")
    prices = relationship("FactPrice", back_populates="stock")
    predictions = relationship("FactPrediction", back_populates="stock")

    def __repr__(self) -> str:
        return f"<DimStock(ticker='{self.ticker}', company='{self.company_name}')>"


class DimCalendar(Base):
    """Date dimension for time-based analysis."""

    __tablename__ = "dim_calendar"

    date_id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    day_of_week_name = Column(String(10), nullable=False)
    day_of_month = Column(Integer, nullable=False)
    week_of_year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    month_name = Column(String(10), nullable=False)
    quarter = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    is_weekend = Column(Boolean, nullable=False)
    is_trading_day = Column(Boolean, nullable=False, index=True)
    is_month_start = Column(Boolean, nullable=False)
    is_month_end = Column(Boolean, nullable=False)
    is_quarter_start = Column(Boolean, nullable=False)
    is_quarter_end = Column(Boolean, nullable=False)
    is_year_start = Column(Boolean, nullable=False)
    is_year_end = Column(Boolean, nullable=False)
    is_us_holiday = Column(Boolean, default=False)
    holiday_name = Column(String(50))
    trading_days_in_month = Column(Integer)
    trading_day_of_month = Column(Integer)

    # Relationships
    sentiments = relationship("FactSentiment", back_populates="calendar")
    prices = relationship("FactPrice", back_populates="calendar")
    fear_greed = relationship("DimFearGreed", back_populates="calendar")

    __table_args__ = (Index("idx_dim_calendar_year_month", "year", "month"),)

    def __repr__(self) -> str:
        return f"<DimCalendar(date='{self.date}')>"


class DimFearGreed(Base):
    """Daily market-wide Fear & Greed index."""

    __tablename__ = "dim_fear_greed"

    fg_id = Column(Integer, primary_key=True, autoincrement=True)
    date_id = Column(Integer, ForeignKey("dim_calendar.date_id"), nullable=False)
    date = Column(Date, nullable=False, unique=True, index=True)
    score = Column(Integer, CheckConstraint("score >= 0 AND score <= 100"), nullable=False)
    classification = Column(String(20), nullable=False)  # Extreme Fear, Fear, etc.
    prev_score = Column(Integer)
    score_change = Column(Integer)

    # Component scores (if available)
    market_momentum = Column(Integer)
    stock_price_strength = Column(Integer)
    stock_price_breadth = Column(Integer)
    put_call_ratio = Column(Numeric(5, 3))
    market_volatility = Column(Numeric(5, 2))
    safe_haven_demand = Column(Integer)
    junk_bond_demand = Column(Integer)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    calendar = relationship("DimCalendar", back_populates="fear_greed")

    def __repr__(self) -> str:
        return f"<DimFearGreed(date='{self.date}', score={self.score})>"


# =============================================================================
# FACT TABLES
# =============================================================================


class FactSentiment(Base):
    """Daily sentiment scores per stock (main analytical table)."""

    __tablename__ = "fact_sentiment"

    sentiment_id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("dim_stocks.stock_id"), nullable=False)
    date_id = Column(Integer, ForeignKey("dim_calendar.date_id"), nullable=False)

    # NLP Sentiment Scores
    nlp_score = Column(Numeric(5, 4), nullable=False)  # -1.0 to 1.0
    nlp_score_prev = Column(Numeric(5, 4))  # Previous day score
    nlp_momentum = Column(Numeric(5, 4))  # Change from previous day
    nlp_trend_days = Column(Integer, default=0)  # Consecutive days same direction
    nlp_confidence = Column(Numeric(4, 3))  # 0 to 1

    # Source Breakdown
    news_score = Column(Numeric(5, 4))
    news_count = Column(Integer, default=0)
    reddit_score = Column(Numeric(5, 4))
    reddit_count = Column(Integer, default=0)

    # Calendar Pattern Score
    calendar_score = Column(Numeric(5, 4), nullable=False)  # -1.0 to 1.0
    month_avg_return = Column(Numeric(6, 3))  # Historical month avg %
    month_win_rate = Column(Numeric(4, 3))  # 0 to 1
    days_to_earnings = Column(Integer)  # NULL if unknown

    # Combined Signal
    combined_score = Column(Numeric(4, 3), nullable=False)  # 0 to 1 (normalized)
    signal = Column(String(20), nullable=False, index=True)  # STRONG_BUY, BUY, HOLD, AVOID
    confidence = Column(Numeric(4, 3), nullable=False)  # 0 to 1

    # Conflict Detection
    conflict_flag = Column(Boolean, default=False)
    conflict_reason = Column(Text)

    # Topics/Keywords (JSON array)
    topics = Column(JSONB)  # ["iPhone", "AI", "earnings"]

    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    pipeline_run_id = Column(String(50))  # For debugging

    # Relationships
    stock = relationship("DimStock", back_populates="sentiments")
    calendar = relationship("DimCalendar", back_populates="sentiments")

    __table_args__ = (
        UniqueConstraint("stock_id", "date_id", name="uq_sentiment_stock_date"),
        Index("idx_fact_sentiment_stock_date", "stock_id", "date_id"),
        Index("idx_fact_sentiment_date", "date_id"),
        Index("idx_fact_sentiment_combined", "combined_score"),
        Index(
            "idx_fact_sentiment_conflict",
            "conflict_flag",
            postgresql_where=Column("conflict_flag") == True,
        ),
    )

    def __repr__(self) -> str:
        return f"<FactSentiment(stock_id={self.stock_id}, combined={self.combined_score})>"


class FactPrice(Base):
    """Daily OHLCV price data."""

    __tablename__ = "fact_prices"

    price_id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("dim_stocks.stock_id"), nullable=False)
    date_id = Column(Integer, ForeignKey("dim_calendar.date_id"), nullable=False)
    date = Column(Date, nullable=False)

    # OHLCV Data
    open = Column(Numeric(12, 4), nullable=False)
    high = Column(Numeric(12, 4), nullable=False)
    low = Column(Numeric(12, 4), nullable=False)
    close = Column(Numeric(12, 4), nullable=False)
    adj_close = Column(Numeric(12, 4), nullable=False)
    volume = Column(BIGINT, nullable=False)

    # Calculated Fields
    daily_return = Column(Numeric(8, 5))  # (close - prev_close) / prev_close
    intraday_range = Column(Numeric(8, 5))  # (high - low) / open

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    stock = relationship("DimStock", back_populates="prices")
    calendar = relationship("DimCalendar", back_populates="prices")

    __table_args__ = (
        UniqueConstraint("stock_id", "date_id", name="uq_price_stock_date"),
        Index("idx_fact_prices_stock_date", "stock_id", "date_id"),
        Index("idx_fact_prices_date", "date_id"),
    )

    def __repr__(self) -> str:
        return f"<FactPrice(stock_id={self.stock_id}, date='{self.date}', close={self.close})>"


class FactPrediction(Base):
    """Model predictions for backtesting and evaluation."""

    __tablename__ = "fact_predictions"

    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("dim_stocks.stock_id"), nullable=False)
    date_id = Column(Integer, ForeignKey("dim_calendar.date_id"), nullable=False)
    prediction_date = Column(Date, nullable=False)  # When prediction was made
    target_date = Column(Date, nullable=False)  # Date being predicted

    # Prediction
    predicted_direction = Column(String(10), nullable=False)  # UP, DOWN, NEUTRAL
    predicted_score = Column(Numeric(4, 3), nullable=False)  # 0 to 1
    predicted_confidence = Column(Numeric(4, 3), nullable=False)

    # Actual Outcome (filled after target_date)
    actual_direction = Column(String(10))
    actual_return = Column(Numeric(8, 5))
    prediction_correct = Column(Boolean)

    # Model Info
    model_version = Column(String(20), nullable=False)
    feature_importance = Column(JSONB)  # Top features for this prediction

    created_at = Column(DateTime, server_default=func.now())
    evaluated_at = Column(DateTime)

    # Relationships
    stock = relationship("DimStock", back_populates="predictions")

    __table_args__ = (
        UniqueConstraint(
            "stock_id", "prediction_date", "target_date", name="uq_pred_stock_dates"
        ),
        Index("idx_fact_predictions_stock_date", "stock_id", "prediction_date"),
        Index(
            "idx_fact_predictions_evaluation",
            "target_date",
            postgresql_where=Column("actual_direction").is_(None),
        ),
    )

    def __repr__(self) -> str:
        return f"<FactPrediction(stock_id={self.stock_id}, direction={self.predicted_direction})>"


class FactExperiment(Base):
    """Sen2Nal vs LLM weekly experiment tracking."""

    __tablename__ = "fact_experiment"

    experiment_id = Column(Integer, primary_key=True, autoincrement=True)
    week_number = Column(Integer, nullable=False)  # 1-52
    year = Column(Integer, nullable=False)
    method = Column(String(20), nullable=False)  # SEN2NAL, CHATGPT, GEMINI, GROK

    # Monday Entry
    entry_date = Column(Date, nullable=False)
    stock_1_ticker = Column(String(10), nullable=False)
    stock_1_score = Column(Numeric(4, 3))  # NULL for LLMs
    stock_1_entry = Column(Numeric(12, 4))  # Monday open price
    stock_1_reasoning = Column(Text)  # LLM reasoning text

    stock_2_ticker = Column(String(10), nullable=False)
    stock_2_score = Column(Numeric(4, 3))
    stock_2_entry = Column(Numeric(12, 4))
    stock_2_reasoning = Column(Text)

    stock_3_ticker = Column(String(10), nullable=False)
    stock_3_score = Column(Numeric(4, 3))
    stock_3_entry = Column(Numeric(12, 4))
    stock_3_reasoning = Column(Text)

    # Friday Exit (filled end of week)
    exit_date = Column(Date)
    stock_1_exit = Column(Numeric(12, 4))  # Friday close price
    stock_2_exit = Column(Numeric(12, 4))
    stock_3_exit = Column(Numeric(12, 4))

    # Performance
    stock_1_return = Column(Numeric(8, 5))  # (exit - entry) / entry
    stock_2_return = Column(Numeric(8, 5))
    stock_3_return = Column(Numeric(8, 5))
    weekly_return = Column(Numeric(8, 5))  # Average of 3 stocks

    # Winner Flag
    is_winner = Column(Boolean, default=False, index=True)

    # LLM Details
    llm_prompt = Column(Text)  # Prompt used
    llm_response = Column(Text)  # Raw response
    llm_model_version = Column(String(50))  # e.g., 'gpt-4-0125-preview'

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("year", "week_number", "method", name="uq_exp_year_week_method"),
        Index("idx_fact_experiment_week", "year", "week_number"),
        Index("idx_fact_experiment_method", "method"),
    )

    def __repr__(self) -> str:
        return f"<FactExperiment(week={self.week_number}, method={self.method})>"


# =============================================================================
# STAGING TABLES
# =============================================================================


class StgNewsRaw(Base):
    """Raw news articles before processing."""

    __tablename__ = "stg_news_raw"

    raw_id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)  # alpha_vantage, newsapi, yahoo
    external_id = Column(String(100))  # Source's article ID
    headline = Column(Text, nullable=False)
    summary = Column(Text)
    url = Column(Text)
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, server_default=func.now())

    # Processing Status
    is_processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime)

    # Extracted Data (filled during processing)
    tickers_mentioned = Column(JSON)  # Array of tickers found
    sentiment_score = Column(Numeric(5, 4))
    sentiment_label = Column(String(20))

    # Deduplication
    content_hash = Column(String(64), index=True)  # SHA256 of headline
    is_duplicate = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_news_source_external"),
        Index(
            "idx_stg_news_unprocessed",
            "is_processed",
            "fetched_at",
            postgresql_where=Column("is_processed") == False,
        ),
    )


class StgRedditRaw(Base):
    """Raw Reddit posts before processing."""

    __tablename__ = "stg_reddit_raw"

    raw_id = Column(Integer, primary_key=True, autoincrement=True)
    subreddit = Column(String(50), nullable=False)  # stocks, wallstreetbets
    post_id = Column(String(20), nullable=False)
    post_type = Column(String(20), nullable=False)  # submission, comment
    title = Column(Text)
    body = Column(Text)
    author = Column(String(50))
    score = Column(Integer)  # Reddit upvotes
    num_comments = Column(Integer)
    created_utc = Column(DateTime)
    fetched_at = Column(DateTime, server_default=func.now())

    # Processing Status
    is_processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime)

    # Extracted Data
    tickers_mentioned = Column(JSON)
    sentiment_score = Column(Numeric(5, 4))
    sentiment_label = Column(String(20))

    __table_args__ = (
        UniqueConstraint("subreddit", "post_id", name="uq_reddit_subreddit_post"),
        Index(
            "idx_stg_reddit_unprocessed",
            "is_processed",
            "fetched_at",
            postgresql_where=Column("is_processed") == False,
        ),
    )


# =============================================================================
# Pipeline Tracking
# =============================================================================


class PipelineRun(Base):
    """Tracks pipeline execution state and results."""

    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(50), nullable=False, unique=True, index=True)
    target_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="running")
    started_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime)
    result_json = Column(JSON)

    logs = relationship("PipelineLog", back_populates="run", order_by="PipelineLog.timestamp")


class PipelineLog(Base):
    """Individual log entries from pipeline runs."""

    __tablename__ = "pipeline_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    stage = Column(String(30), nullable=False)
    level = Column(String(10), nullable=False, default="info")
    message = Column(Text, nullable=False)

    run = relationship("PipelineRun", back_populates="logs")
