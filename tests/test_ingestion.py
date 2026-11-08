"""Tests for AG-01 Ingestion Agent.

Tests ingestion logic with mocked external APIs (yfinance, NewsAPI, Reddit, CNN).
No real API calls are made in tests.
"""

import sys
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.agents import ingestion
from src.agents.ingestion import IngestionAgent, _get_stock_metadata, _parse_datetime
from src.constants import ALLOWED_TICKERS


@pytest.fixture
def agent():
    """Ingestion agent with mocked DB session."""
    db = MagicMock()
    return IngestionAgent(db=db, run_id="test_ingest_01")


# -- stage_name and basic attributes ----------------------------------------

class TestIngestionAttributes:

    def test_stage_name_set(self):
        assert IngestionAgent.stage_name == "ingestion"

    def test_agent_name(self, agent):
        assert agent.name == "AG-01-Ingestion"


# -- Ticker whitelist -------------------------------------------------------

class TestTickerWhitelist:

    def test_allowed_tickers_contains_top_10(self):
        expected = {"AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
                    "META", "TSLA", "BRK.B", "JPM", "V"}
        assert expected == ALLOWED_TICKERS

    def test_validate_tickers_filters_invalid(self):
        from src.constants import validate_tickers
        result = validate_tickers(["AAPL", "FAKE", "MSFT", "XYZ123"])
        assert result == ["AAPL", "MSFT"]

    def test_validate_tickers_empty_list(self):
        from src.constants import validate_tickers
        result = validate_tickers(["FAKE1", "FAKE2"])
        assert result == []


# -- News ingestion ---------------------------------------------------------

class TestNewsIngestion:

    @patch("src.agents.ingestion.requests.get")
    @patch("src.agents.ingestion.settings")
    def test_ingest_news_stores_articles(self, mock_settings, mock_get, agent):
        mock_settings.newsapi_api_key = "test-key"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "articles": [
                {
                    "title": "Apple beats earnings expectations",
                    "description": "Strong Q4 results",
                    "url": "https://example.com/article",
                    "publishedAt": "2026-03-20T14:00:00Z",
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Mock DB queries to avoid duplicate check
        agent.db.execute.return_value.scalar.return_value = None

        count = agent._ingest_news(["AAPL"], date(2026, 3, 20))

        assert count == 1
        agent.db.add.assert_called_once()
        agent.db.flush.assert_called_once()

    @patch("src.agents.ingestion.settings")
    def test_ingest_news_skips_without_api_key(self, mock_settings, agent):
        mock_settings.newsapi_api_key = None
        count = agent._ingest_news(["AAPL"], date(2026, 3, 20))
        assert count == 0

    @patch("src.agents.ingestion.requests.get")
    @patch("src.agents.ingestion.settings")
    def test_ingest_news_handles_api_failure(self, mock_settings, mock_get, agent):
        mock_settings.newsapi_api_key = "test-key"
        mock_get.side_effect = Exception("API timeout")

        count = agent._ingest_news(["AAPL"], date(2026, 3, 20))
        assert count == 0


# -- Reddit ingestion -------------------------------------------------------

class TestRedditIngestion:

    @patch("src.agents.ingestion.settings")
    def test_ingest_reddit_skips_without_credentials(self, mock_settings, agent):
        mock_settings.reddit_client_id = None
        mock_settings.reddit_client_secret = None
        count = agent._ingest_reddit(["AAPL"])
        assert count == 0


# -- Fear & Greed -----------------------------------------------------------

class TestFearGreed:

    @patch("src.agents.ingestion.requests.get")
    def test_ingest_fear_greed_handles_failure(self, mock_get, agent):
        mock_get.side_effect = Exception("Network error")
        result = agent._ingest_fear_greed(date(2026, 3, 20))
        assert result is None


# -- Helpers -----------------------------------------------------------------

class TestHelpers:

    def test_parse_datetime_valid(self):
        result = _parse_datetime("2026-03-20T14:00:00Z")
        assert isinstance(result, datetime)
        assert result.year == 2026

    def test_parse_datetime_none(self):
        assert _parse_datetime(None) is None

    def test_parse_datetime_invalid(self):
        assert _parse_datetime("not-a-date") is None

    def test_get_stock_metadata_known_tickers(self):
        result = _get_stock_metadata(["AAPL", "MSFT"])
        assert "AAPL" in result
        assert result["AAPL"]["company_name"] == "Apple Inc."
        assert result["MSFT"]["sector"] == "Technology"

    def test_source_time_is_normalised_and_ambiguous_time_stays_unknown(self):
        assert _parse_datetime("2026-03-20T14:00:00+02:00") == datetime(2026, 3, 20, 12)
        assert _parse_datetime("2026-03-20T14:00:00") is None


@pytest.fixture
def text_ingestion(agent, monkeypatch):
    monkeypatch.setattr(agent, "_ensure_stocks", MagicMock())
    monkeypatch.setattr(agent, "_ensure_calendar", MagicMock())
    monkeypatch.setattr(agent, "_ingest_prices", lambda *args: 0)
    monkeypatch.setattr(agent, "_ingest_fear_greed", lambda *args: None)
    monkeypatch.setattr(ingestion.settings, "newsapi_api_key", "fixture-only")
    monkeypatch.setattr(ingestion.settings, "reddit_client_id", None)
    monkeypatch.setattr(ingestion.settings, "reddit_client_secret", None)
    monkeypatch.setattr(ingestion.time, "sleep", lambda *args: None)
    agent.db.execute.return_value.scalar.return_value = None
    return agent


@pytest.mark.parametrize("articles", [
    {}, [{"title": 17}], [{"title": "Synthetic news", "description": 12}],
    [{"title": "Synthetic news", "url": "javascript:bad"}],
])
def test_invalid_news_payload_aborts_before_commit(text_ingestion, monkeypatch, articles):
    response = MagicMock()
    response.json.return_value = {"articles": articles}
    monkeypatch.setattr(ingestion.requests, "get", MagicMock(return_value=response))
    result = text_ingestion.run(target_date=date(2026, 11, 4), tickers=["AAPL"])
    assert result["status"] == "invalid"
    assert result["error_code"] == "data_contract_violation"
    text_ingestion.db.add.assert_not_called()
    text_ingestion.db.commit.assert_not_called()
    text_ingestion.db.rollback.assert_called_once()


def test_missing_news_url_and_time_are_stored_as_unknown(text_ingestion, monkeypatch):
    response = MagicMock()
    response.json.return_value = {"articles": [{"title": "Synthetic news", "url": None}]}
    monkeypatch.setattr(ingestion.requests, "get", MagicMock(return_value=response))
    result = text_ingestion.run(target_date=date(2026, 11, 4), tickers=["AAPL"])
    assert result["status"] == "success" and result["news_ingested"] == 1
    record = text_ingestion.db.add.call_args.args[0]
    assert record.url is None and record.external_id is None and record.published_at is None
    text_ingestion.db.commit.assert_called_once()


def test_later_invalid_news_record_rolls_back_pending_writes(text_ingestion, monkeypatch):
    response = MagicMock()
    response.json.return_value = {"articles": [{"title": "Synthetic news"}, {"title": 17}]}
    monkeypatch.setattr(ingestion.requests, "get", MagicMock(return_value=response))
    result = text_ingestion.run(target_date=date(2026, 11, 4), tickers=["AAPL"])
    assert result["status"] == "invalid"
    text_ingestion.db.add.assert_called_once()
    text_ingestion.db.commit.assert_not_called()
    text_ingestion.db.rollback.assert_called_once()


def test_invalid_reddit_record_cannot_be_committed(text_ingestion, monkeypatch):
    monkeypatch.setattr(ingestion.settings, "newsapi_api_key", None)
    monkeypatch.setattr(ingestion.settings, "reddit_client_id", "fixture-only")
    monkeypatch.setattr(ingestion.settings, "reddit_client_secret", "fixture-only")
    client = MagicMock()
    client.subreddit.return_value.hot.return_value = [SimpleNamespace(
        title="$AAPL synthetic post", selftext="Example", id="fixture", author=None,
        score=1, num_comments=-1, created_utc=1_770_000_000,
    )]
    monkeypatch.setitem(sys.modules, "praw", SimpleNamespace(Reddit=lambda **kwargs: client))
    result = text_ingestion.run(target_date=date(2026, 11, 4), tickers=["AAPL"])
    assert result["status"] == "invalid"
    text_ingestion.db.add.assert_not_called()
    text_ingestion.db.commit.assert_not_called()
    text_ingestion.db.rollback.assert_called_once()


@pytest.fixture
def market_ingestion(agent, monkeypatch):
    monkeypatch.setattr(agent, "_ensure_stocks", MagicMock())
    monkeypatch.setattr(agent, "_ensure_calendar", MagicMock())
    monkeypatch.setattr(agent, "_get_stock_id", lambda ticker: 1)
    monkeypatch.setattr(agent, "_get_or_create_date_id", lambda day: day.day)
    monkeypatch.setattr(agent, "_ingest_news", lambda *args: 0)
    monkeypatch.setattr(agent, "_ingest_reddit", lambda *args: 0)
    monkeypatch.setattr(ingestion.time, "sleep", lambda *args: None)
    agent.db.execute.return_value.scalar.return_value = None
    return agent


def _stub_history(monkeypatch, rows):
    frame = pd.DataFrame(rows, index=pd.date_range("2026-11-02", periods=len(rows)))
    stock = SimpleNamespace(history=lambda **kwargs: frame)
    monkeypatch.setitem(sys.modules, "yfinance", SimpleNamespace(Ticker=lambda ticker: stock))


PRICE_BAR = {"Open": 10.0, "High": 11.0, "Low": 9.0, "Close": 10.0, "Volume": 0}


@pytest.mark.parametrize("invalid_fields", [
    {"Close": float("nan")}, {"High": 9.5}, {"Volume": -1}, {"Volume": 0.5}, {"Open": "10"},
])
def test_invalid_price_bar_rolls_back_earlier_bar(market_ingestion, monkeypatch, invalid_fields):
    monkeypatch.setattr(market_ingestion, "_ingest_fear_greed", lambda *args: None)
    _stub_history(monkeypatch, [PRICE_BAR, {**PRICE_BAR, **invalid_fields}])
    result = market_ingestion.run(target_date=date(2026, 11, 4), tickers=["AAPL"])
    assert result["status"] == "invalid"
    market_ingestion.db.add.assert_called_once()
    market_ingestion.db.commit.assert_not_called()
    market_ingestion.db.rollback.assert_called_once()


def test_price_write_retains_observed_zero_return_and_volume(market_ingestion, monkeypatch):
    monkeypatch.setattr(market_ingestion, "_ingest_fear_greed", lambda *args: None)
    _stub_history(monkeypatch, [PRICE_BAR, PRICE_BAR])
    result = market_ingestion.run(target_date=date(2026, 11, 4), tickers=["AAPL"])
    assert result["status"] == "success" and result["prices_ingested"] == 2
    first, second = [call.args[0] for call in market_ingestion.db.add.call_args_list]
    assert first.daily_return is None
    assert second.daily_return == 0.0 and second.volume == 0
    assert [type(second.daily_return), type(second.volume), type(second.close)] == [float, int, float]


@pytest.mark.parametrize("score_data", [
    {}, {"score": 100.9, "rating": "extreme greed"}, {"score": True, "rating": "fear"},
    {"score": float("inf"), "rating": "greed"}, {"score": 50},
])
def test_invalid_fear_greed_score_cannot_be_committed(market_ingestion, monkeypatch, score_data):
    _stub_history(monkeypatch, [PRICE_BAR])
    response = MagicMock()
    response.json.return_value = {"fear_and_greed": score_data}
    monkeypatch.setattr(ingestion.requests, "get", MagicMock(return_value=response))
    result = market_ingestion.run(target_date=date(2026, 11, 4), tickers=["AAPL"])
    assert result["status"] == "invalid"
    market_ingestion.db.add.assert_called_once()
    market_ingestion.db.commit.assert_not_called()
    market_ingestion.db.rollback.assert_called_once()


@pytest.mark.parametrize("history", [[[0, 0], [1, 1]], [{"x": 0, "y": 0}, {"x": 1, "y": 1}]])
def test_fear_greed_keeps_a_zero_previous_score(market_ingestion, monkeypatch, history):
    monkeypatch.setattr(market_ingestion, "_ingest_prices", lambda *args: 0)
    response = MagicMock()
    response.json.return_value = {
        "fear_and_greed": {"score": 1, "rating": "extreme fear"},
        "fear_and_greed_historical": {"data": history},
    }
    monkeypatch.setattr(ingestion.requests, "get", MagicMock(return_value=response))
    result = market_ingestion.run(target_date=date(2026, 11, 4), tickers=["AAPL"])
    assert result["status"] == "success"
    assert result["fear_greed"] == {"score": 1, "classification": "extreme fear"}
    record = market_ingestion.db.add.call_args.args[0]
    assert record.prev_score == 0 and record.score_change == 1
