"""Tests for AG-01 Ingestion Agent.

Tests ingestion logic with mocked external APIs (yfinance, NewsAPI, Reddit, CNN).
No real API calls are made in tests.
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

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
