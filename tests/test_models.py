"""Tests for SQLAlchemy ORM models.

Verifies model creation, constraints, and foreign key relationships
against a real PostgreSQL database (via conftest fixtures).
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from src.database.models import (
    DimCalendar,
    DimFearGreed,
    DimStock,
    FactExperiment,
    FactPrediction,
    FactPrice,
    FactSentiment,
    StgNewsRaw,
    StgRedditRaw,
)


# -- DimStock ----------------------------------------------------------------

class TestDimStock:

    def test_create_stock(self, db):
        stock = DimStock(
            ticker="TEST",
            company_name="Test Corp",
            sector="Technology",
            is_active=True,
        )
        db.add(stock)
        db.flush()
        assert stock.stock_id is not None
        assert stock.ticker == "TEST"

    def test_stock_ticker_unique(self, db):
        db.add(DimStock(ticker="DUP", company_name="First", sector="Tech"))
        db.flush()
        db.add(DimStock(ticker="DUP", company_name="Second", sector="Tech"))
        with pytest.raises(Exception):  # IntegrityError
            db.flush()

    def test_stock_repr(self, db):
        stock = DimStock(ticker="REPR", company_name="Repr Corp", sector="Tech")
        assert "REPR" in repr(stock)

    def test_seed_stock_fixture(self, seed_stock):
        assert seed_stock.ticker == "AAPL"
        assert seed_stock.stock_id is not None


# -- DimCalendar -------------------------------------------------------------

class TestDimCalendar:

    def test_create_calendar(self, db):
        cal = DimCalendar(
            date=date(2026, 4, 1),
            day_of_week=2,
            day_of_week_name="Wednesday",
            day_of_month=1,
            week_of_year=14,
            month=4,
            month_name="April",
            quarter=2,
            year=2026,
            is_weekend=False,
            is_trading_day=True,
            is_month_start=True,
            is_month_end=False,
            is_quarter_start=True,
            is_quarter_end=False,
            is_year_start=False,
            is_year_end=False,
        )
        db.add(cal)
        db.flush()
        assert cal.date_id is not None
        assert cal.is_trading_day is True

    def test_calendar_date_unique(self, db):
        for i in range(2):
            db.add(DimCalendar(
                date=date(2026, 1, 1),
                day_of_week=3, day_of_week_name="Thursday",
                day_of_month=1, week_of_year=1, month=1,
                month_name="January", quarter=1, year=2026,
                is_weekend=False, is_trading_day=True,
                is_month_start=True, is_month_end=False,
                is_quarter_start=True, is_quarter_end=False,
                is_year_start=True, is_year_end=False,
            ))
        with pytest.raises(Exception):
            db.flush()

    def test_seed_calendar_fixture(self, seed_calendar):
        assert seed_calendar.date == date(2026, 3, 20)
        assert seed_calendar.date_id is not None


# -- FactPrice ---------------------------------------------------------------

class TestFactPrice:

    def test_create_price(self, db, seed_stock, seed_calendar):
        price = FactPrice(
            stock_id=seed_stock.stock_id,
            date_id=seed_calendar.date_id,
            date=date(2026, 3, 20),
            open=Decimal("175.0000"),
            high=Decimal("178.5000"),
            low=Decimal("174.2000"),
            close=Decimal("177.8000"),
            adj_close=Decimal("177.8000"),
            volume=85_000_000,
            daily_return=Decimal("0.01200"),
        )
        db.add(price)
        db.flush()
        assert price.price_id is not None

    def test_price_foreign_key_to_stock(self, db, seed_stock, seed_calendar):
        price = FactPrice(
            stock_id=seed_stock.stock_id,
            date_id=seed_calendar.date_id,
            date=date(2026, 3, 20),
            open=Decimal("175.0000"),
            high=Decimal("178.5000"),
            low=Decimal("174.2000"),
            close=Decimal("177.8000"),
            adj_close=Decimal("177.8000"),
            volume=85_000_000,
        )
        db.add(price)
        db.flush()
        assert price.stock_id == seed_stock.stock_id


# -- FactSentiment -----------------------------------------------------------

class TestFactSentiment:

    def test_create_sentiment(self, db, seed_stock, seed_calendar):
        sent = FactSentiment(
            stock_id=seed_stock.stock_id,
            date_id=seed_calendar.date_id,
            nlp_score=Decimal("0.6500"),
            calendar_score=Decimal("0.1200"),
            combined_score=Decimal("0.550"),
            signal="BUY",
            confidence=Decimal("0.780"),
            news_count=5,
            reddit_count=3,
        )
        db.add(sent)
        db.flush()
        assert sent.sentiment_id is not None
        assert sent.signal == "BUY"

    def test_sentiment_unique_stock_date(self, db, seed_stock, seed_calendar):
        for _ in range(2):
            db.add(FactSentiment(
                stock_id=seed_stock.stock_id,
                date_id=seed_calendar.date_id,
                nlp_score=Decimal("0.5000"),
                calendar_score=Decimal("0.1000"),
                combined_score=Decimal("0.500"),
                signal="HOLD",
                confidence=Decimal("0.600"),
            ))
        with pytest.raises(Exception):
            db.flush()


# -- FactPrediction ----------------------------------------------------------

class TestFactPrediction:

    def test_create_prediction(self, db, seed_stock, seed_calendar):
        pred = FactPrediction(
            stock_id=seed_stock.stock_id,
            date_id=seed_calendar.date_id,
            prediction_date=date(2026, 3, 20),
            target_date=date(2026, 3, 27),
            predicted_direction="UP",
            predicted_score=Decimal("0.720"),
            predicted_confidence=Decimal("0.680"),
            model_version="xgb-v1.0",
        )
        db.add(pred)
        db.flush()
        assert pred.prediction_id is not None
        assert pred.predicted_direction == "UP"


# -- Staging tables ----------------------------------------------------------

class TestStagingTables:

    def test_create_news_raw(self, db):
        news = StgNewsRaw(
            source="newsapi",
            headline="Apple stock surges",
            content_hash="a" * 64,
            is_processed=False,
            is_duplicate=False,
        )
        db.add(news)
        db.flush()
        assert news.raw_id is not None

    def test_create_reddit_raw(self, db):
        reddit = StgRedditRaw(
            subreddit="stocks",
            post_id="abc123",
            post_type="submission",
            title="AAPL to the moon",
            is_processed=False,
        )
        db.add(reddit)
        db.flush()
        assert reddit.raw_id is not None
