"""E2E pipeline integration test (E0.M3).

Runs run_full_pipeline on a single ticker with ALL five external sources mocked
(yfinance, NewsAPI, Reddit/PRAW, CNN Fear & Greed, LLM APIs). This is the standing
regression instrument for the Sen2Nal pipeline.

Per the execution plan (docs/plans/EXECUTION_PLAN_v1.md section 9, E0.M3):
- Expected outcome: likely FAILS at the features stage (the JSON.contains defect
  on StgNewsRaw.tickers_mentioned -- a generic JSON column, not JSONB). That failure
  is a DELIVERABLE confirming E1.M4's priority; it is recorded, NOT fixed here.
- Addresses KI-009 (no E2E run ever captured) and KI-014 (keys are placeholders).

Requires PostgreSQL -- runs in CI (postgres:15 service) or locally with native PG.
Skips automatically when no database is reachable.
"""

from datetime import date
from unittest.mock import MagicMock

import pandas as pd
import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from src.agents.sentiment import SentimentAgent
from src.config import settings
from src.database.connection import Base
from src.database.models import (
    DimFearGreed,
    DimStock,
    FactExperiment,
    FactPrediction,
    FactPrice,
    FactSentiment,
    StgNewsRaw,
    StgRedditRaw,
)
from src.pipeline.runner import run_full_pipeline


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def e2e_db(test_db_engine):
    """Database session for E2E tests -- allows commits, cleans up after.

    Unlike the rollback-isolated db fixture, this creates a session directly
    from the engine so agents can call db.commit() freely. All data is deleted
    after the test to maintain isolation between tests.
    """
    Session = sessionmaker(bind=test_db_engine)
    session = Session()
    yield session
    session.close()
    with test_db_engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()


# =============================================================================
# Mock helpers
# =============================================================================


class MockResponse:
    """Minimal mock for requests.Response."""

    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def _setup_mocks(monkeypatch):
    """Mock all five external sources and set fake API keys.

    Sources mocked:
    1. yfinance -- price data
    2. NewsAPI (requests.get) -- news headlines
    3. Reddit/PRAW -- social sentiment posts
    4. CNN Fear & Greed (requests.get) -- market sentiment index
    5. LLM APIs (requests.post) -- ChatGPT, Gemini, Grok for experiment
    """
    # Mock time.sleep to avoid rate-limit delays during testing
    monkeypatch.setattr("time.sleep", lambda x: None)

    # 1. Mock yfinance -- return 2 days of price data for the target window
    mock_hist = pd.DataFrame(
        {
            "Open": [150.0, 151.0],
            "High": [152.0, 153.0],
            "Low": [149.0, 150.0],
            "Close": [151.0, 152.0],
            "Volume": [1000000, 1100000],
        },
        index=pd.DatetimeIndex(["2026-07-02", "2026-07-06"], name="Date"),
    )
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = mock_hist
    monkeypatch.setattr("yfinance.Ticker", lambda t: mock_ticker)

    # 2. Set fake API keys so all ingestion paths are exercised
    monkeypatch.setattr(settings, "newsapi_api_key", "test-newsapi-key")
    monkeypatch.setattr(settings, "reddit_client_id", "test-reddit-id")
    monkeypatch.setattr(settings, "reddit_client_secret", "test-reddit-secret")
    monkeypatch.setattr(settings, "openai_api_key", "test-openai-key")
    monkeypatch.setattr(settings, "google_api_key", "test-google-key")
    monkeypatch.setattr(settings, "xai_api_key", "test-xai-key")

    # 3. Mock requests.get for NewsAPI and CNN Fear & Greed
    def mock_requests_get(url, **kwargs):
        if "newsapi.org" in url:
            return MockResponse({
                "articles": [
                    {
                        "title": "AAPL hits record high on strong earnings",
                        "description": "Apple shares surge after Q3 beat",
                        "url": "https://example.com/aapl-record",
                        "publishedAt": "2026-07-05T10:00:00Z",
                    }
                ]
            })
        elif "dataviz.cnn.io" in url:
            return MockResponse({
                "fear_and_greed": {"score": 55, "rating": "Greed"},
                "fear_and_greed_historical": {"data": [[0, 50], [1, 55]]},
            })
        return MockResponse({}, 404)

    monkeypatch.setattr("requests.get", mock_requests_get)

    # 4. Mock praw.Reddit -- return one post mentioning $AAPL
    mock_post = MagicMock()
    mock_post.title = "AAPL to the moon!"
    mock_post.selftext = "$AAPL earnings beat expectations, price target raised"
    mock_post.id = "test_post_001"
    mock_post.score = 150
    mock_post.num_comments = 42
    mock_post.author = MagicMock()
    mock_post.created_utc = 1751800000

    mock_subreddit = MagicMock()
    mock_subreddit.hot.return_value = [mock_post]

    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value = mock_subreddit

    monkeypatch.setattr("praw.Reddit", lambda **kwargs: mock_reddit)

    # 5. Mock SentimentAgent._load_model -- skip FinBERT download, use mock VADER
    def mock_load_model(self):
        self._model = MagicMock()
        self._model_type = "vader"
        self._device = "cpu"

        def mock_polarity_scores(text):
            bullish_words = ["record", "surge", "moon", "beat", "raised", "strong"]
            bearish_words = ["crash", "drop", "fall", "miss", "weak", "sell"]
            if any(w in text.lower() for w in bullish_words):
                return {"compound": 0.7, "neu": 0.2, "pos": 0.8, "neg": 0.0}
            elif any(w in text.lower() for w in bearish_words):
                return {"compound": -0.5, "neu": 0.3, "pos": 0.0, "neg": 0.7}
            return {"compound": 0.0, "neu": 1.0, "pos": 0.0, "neg": 0.0}

        self._model.polarity_scores.side_effect = mock_polarity_scores

    monkeypatch.setattr(SentimentAgent, "_load_model", mock_load_model)

    # 6. Mock requests.post for LLM APIs (ChatGPT, Gemini, Grok)
    def mock_requests_post(url, **kwargs):
        if "openai.com" in url:
            return MockResponse({
                "choices": [{"message": {"content": (
                    "AAPL: Strong earnings beat\n"
                    "MSFT: Cloud growth\n"
                    "NVDA: AI leadership"
                )}}],
                "model": "gpt-4o",
            })
        elif "googleapis.com" in url:
            return MockResponse({
                "candidates": [{"content": {"parts": [{"text": (
                    "GOOGL: Search dominance\n"
                    "AMZN: Retail strength\n"
                    "META: Ad recovery"
                )}]}}],
            })
        elif "x.ai" in url:
            return MockResponse({
                "choices": [{"message": {"content": (
                    "TSLA: Robotaxi potential\n"
                    "JPM: Rate cut beneficiary\n"
                    "V: Payments growth"
                )}}],
                "model": "grok-3",
            })
        return MockResponse({}, 404)

    monkeypatch.setattr("requests.post", mock_requests_post)


# =============================================================================
# E2E Test
# =============================================================================


@pytest.mark.e2e
def test_e2e_pipeline_single_ticker_all_sources_mocked(e2e_db, monkeypatch):
    """E2E pipeline run on one ticker with all five external sources mocked.

    This is the standing regression instrument for the Sen2Nal pipeline (E0.M3).
    It exercises all 6 agent stages against a real PostgreSQL database with
    mocked external APIs:
    - yfinance (prices)
    - NewsAPI (news headlines)
    - Reddit/PRAW (social sentiment)
    - CNN Fear & Greed (market sentiment)
    - LLM APIs (ChatGPT, Gemini, Grok -- for the experiment)

    Expected outcome per the execution plan:
    - Stages 1-3 (ingestion, sentiment, calendar) should succeed.
    - Stage 4 (features) may FAIL due to the JSON.contains defect on
      StgNewsRaw.tickers_mentioned (a generic JSON column, not JSONB).
      This failure is a DELIVERABLE confirming E1.M4's priority -- it is
      recorded here, NOT fixed (change control C3).
    - If features succeeds, stages 5-6 (prediction, experiment) should also
      succeed, and fact tables should have row counts > 0.

    The test PASSES in both cases (features success or features failure)
    because it documents the current state of the pipeline.

    Addresses KI-009 (no E2E run ever captured) and KI-014 (API keys are
    placeholders -- mocks make them unnecessary).

    Requires PostgreSQL -- runs in CI or with native PG. Skips without a DB.
    """
    _setup_mocks(monkeypatch)

    target = date(2026, 7, 6)  # Monday -- triggers experiment entry path
    ticker = "AAPL"

    result = run_full_pipeline(e2e_db, target_date=target, tickers=[ticker])

    # --- Verify result structure ---
    assert "run_id" in result, "Pipeline result should have a run_id"
    assert "stages" in result, "Pipeline result should have stages dict"
    assert result["target_date"] == "2026-07-06"

    # --- Stage 1: Ingestion ---
    assert result["stages"]["ingestion"]["status"] == "success", (
        f"Ingestion should succeed with mocked external sources, got: "
        f"{result['stages']['ingestion'].get('error', 'no error')}"
    )
    assert result["stages"]["ingestion"]["prices_ingested"] > 0, \
        "At least one price record should be ingested"
    assert result["stages"]["ingestion"]["news_ingested"] > 0, \
        "At least one news article should be ingested"
    assert result["stages"]["ingestion"]["reddit_ingested"] > 0, \
        "At least one Reddit post should be ingested"
    assert result["stages"]["ingestion"]["fear_greed"] is not None, \
        "Fear & Greed data should be ingested"

    # Verify staging and dimension tables have data
    news_records = e2e_db.execute(select(StgNewsRaw)).scalars().all()
    assert len(news_records) > 0, "stg_news_raw should have records"

    reddit_records = e2e_db.execute(select(StgRedditRaw)).scalars().all()
    assert len(reddit_records) > 0, "stg_reddit_raw should have records"

    stocks = e2e_db.execute(select(DimStock).where(DimStock.ticker == ticker)).scalars().all()
    assert len(stocks) == 1, f"dim_stocks should have the test ticker {ticker}"

    prices = e2e_db.execute(select(FactPrice)).scalars().all()
    assert len(prices) > 0, "fact_prices should have price records"

    fg = e2e_db.execute(select(DimFearGreed)).scalars().all()
    assert len(fg) > 0, "dim_fear_greed should have F&G data"

    # --- Stage 2: Sentiment ---
    assert result["stages"]["sentiment"]["status"] == "success", (
        f"Sentiment should succeed with mock model, got: "
        f"{result['stages']['sentiment'].get('error', 'no error')}"
    )
    assert result["stages"]["sentiment"]["news_processed"] > 0, \
        "At least one news article should be processed"
    assert result["stages"]["sentiment"]["reddit_processed"] > 0, \
        "At least one Reddit post should be processed"

    # Verify staging records were marked as processed
    processed_news = e2e_db.execute(
        select(StgNewsRaw).where(StgNewsRaw.is_processed.is_(True))
    ).scalars().all()
    assert len(processed_news) > 0, "News records should be marked as processed"

    processed_reddit = e2e_db.execute(
        select(StgRedditRaw).where(StgRedditRaw.is_processed.is_(True))
    ).scalars().all()
    assert len(processed_reddit) > 0, "Reddit records should be marked as processed"

    # --- Stage 3: Calendar ---
    assert result["stages"]["calendar"]["status"] == "success", \
        "Calendar should succeed (pure computation, no external calls)"
    assert ticker in result["stages"]["calendar"]["signals"], \
        "Calendar signal should include the target ticker"

    # --- Stage 4: Features (may fail -- JSON.contains defect) ---
    features_status = result["stages"]["features"]["status"]

    if features_status == "failed":
        # Expected outcome: JSON.contains defect on generic JSON column.
        # This is a DELIVERABLE confirming E1.M4's priority -- recorded, not fixed.
        # The pipeline should halt here; downstream stages should not run.
        assert result["overall_status"] == "failed", \
            "Pipeline should be marked as failed when features fails"
        assert result["failed_at"] == "features", \
            "Pipeline should report features as the failure point"
        assert "prediction" not in result["stages"], \
            "Pipeline should halt at features -- prediction should not run"
        assert "experiment" not in result["stages"], \
            "Pipeline should halt at features -- experiment should not run"

        # fact_sentiment should have 0 rows (features never wrote any)
        sent_records = e2e_db.execute(select(FactSentiment)).scalars().all()
        assert len(sent_records) == 0, \
            "Features failed -- no fact_sentiment rows should exist"

    elif features_status == "success":
        # Features succeeded -- verify downstream stages and fact tables
        assert result["stages"]["features"]["rows_written"] > 0, \
            "Features should have written fact_sentiment rows"

        sent_records = e2e_db.execute(select(FactSentiment)).scalars().all()
        assert len(sent_records) > 0, "fact_sentiment should have records"

        # --- Stage 5: Prediction ---
        assert result["stages"]["prediction"]["status"] == "success", (
            f"Prediction should succeed after features, got: "
            f"{result['stages']['prediction'].get('error', 'no error')}"
        )

        pred_records = e2e_db.execute(select(FactPrediction)).scalars().all()
        assert len(pred_records) > 0, "fact_predictions should have records"

        # --- Stage 6: Experiment (Monday entry path) ---
        assert result["stages"]["experiment"]["status"] == "success", (
            f"Experiment should succeed on Monday with mocked LLMs, got: "
            f"{result['stages']['experiment'].get('error', 'no error')}"
        )

        exp_records = e2e_db.execute(select(FactExperiment)).scalars().all()
        assert len(exp_records) > 0, "fact_experiment should have records"

        assert result["overall_status"] == "success", \
            "Pipeline should be marked as success when all stages pass"

    # --- Final structural assertions (both outcomes) ---
    assert result["overall_status"] in ("success", "failed"), \
        "Pipeline result should have a valid overall_status"
    assert "failed_stages" in result, \
        "Pipeline result should always include failed_stages list"
