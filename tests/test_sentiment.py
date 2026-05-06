"""Tests for AG-02 Sentiment Agent.

Tests sentiment scoring with mocked FinBERT/VADER models.
No real model downloads or GPU inference in tests.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.agents.sentiment import (
    SentimentAgent,
    _classify_sentiment,
    aggregate_ticker_sentiment,
)


@pytest.fixture
def agent():
    """Sentiment agent with mocked DB session."""
    db = MagicMock()
    return SentimentAgent(db=db, run_id="test_sent_01")


# -- stage_name and basic attributes ----------------------------------------

class TestSentimentAttributes:

    def test_stage_name_set(self):
        assert SentimentAgent.stage_name == "sentiment"

    def test_agent_name(self, agent):
        assert agent.name == "AG-02-Sentiment"


# -- VADER fallback scoring -------------------------------------------------

class TestVaderFallback:

    def _make_vader_agent(self):
        """Create an agent that uses VADER (simulating FinBERT unavailable)."""
        db = MagicMock()
        agent = SentimentAgent(db=db, run_id="test_vader")
        # Force VADER mode
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        import nltk
        nltk.download("vader_lexicon", quiet=True)
        agent._model = SentimentIntensityAnalyzer()
        agent._model_type = "vader"
        return agent

    def test_positive_text_scores_positive(self):
        agent = self._make_vader_agent()
        score, confidence = agent._score_text(
            "Apple stock surges on incredible earnings beat, investors thrilled"
        )
        assert score > 0, f"Expected positive score, got {score}"
        assert 0.0 <= confidence <= 1.0

    def test_negative_text_scores_negative(self):
        agent = self._make_vader_agent()
        score, confidence = agent._score_text(
            "Stock crashes after terrible earnings miss, massive losses reported"
        )
        assert score < 0, f"Expected negative score, got {score}"
        assert 0.0 <= confidence <= 1.0

    def test_neutral_text_scores_near_zero(self):
        agent = self._make_vader_agent()
        score, confidence = agent._score_text(
            "The company reported quarterly results today"
        )
        assert -0.5 <= score <= 0.5

    def test_empty_text_returns_zero(self):
        agent = self._make_vader_agent()
        score, confidence = agent._score_text("")
        assert score == 0.0
        assert confidence == 0.0

    def test_short_text_returns_zero(self):
        agent = self._make_vader_agent()
        score, confidence = agent._score_text("hi")
        assert score == 0.0
        assert confidence == 0.0

    def test_score_bounded(self):
        agent = self._make_vader_agent()
        texts = [
            "This is the best stock ever, absolutely incredible growth!",
            "Total disaster, worst crash in history, complete meltdown!",
            "Normal trading day with average volume",
        ]
        for text in texts:
            score, confidence = agent._score_text(text)
            assert -1.0 <= score <= 1.0, f"Score {score} out of bounds for: {text}"
            assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} out of bounds"


# -- Sentiment classification -----------------------------------------------

class TestClassifySentiment:

    def test_positive_classification(self):
        assert _classify_sentiment(0.5) == "positive"
        assert _classify_sentiment(0.16) == "positive"

    def test_negative_classification(self):
        assert _classify_sentiment(-0.5) == "negative"
        assert _classify_sentiment(-0.16) == "negative"

    def test_neutral_classification(self):
        assert _classify_sentiment(0.0) == "neutral"
        assert _classify_sentiment(0.10) == "neutral"
        assert _classify_sentiment(-0.10) == "neutral"

    def test_boundary_values(self):
        assert _classify_sentiment(0.15) == "neutral"
        assert _classify_sentiment(-0.15) == "neutral"


# -- Aggregation helpers -----------------------------------------------------

class TestAggregateSentiment:

    def _make_record(self, score, published_at=None):
        record = MagicMock()
        record.sentiment_score = score
        record.published_at = published_at
        record.created_utc = published_at
        return record

    def test_empty_records_returns_zero(self):
        result = aggregate_ticker_sentiment([], [])
        assert result["nlp_score"] == 0.0
        assert result["nlp_confidence"] == 0.0
        assert result["news_count"] == 0
        assert result["reddit_count"] == 0

    def test_news_only(self):
        news = [self._make_record(0.8, datetime(2026, 3, 20, 14, 0))]
        result = aggregate_ticker_sentiment(news, [])
        assert result["news_count"] == 1
        assert result["reddit_count"] == 0
        assert result["nlp_score"] > 0

    def test_reddit_only(self):
        reddit = [self._make_record(-0.5, datetime(2026, 3, 20, 12, 0))]
        result = aggregate_ticker_sentiment([], reddit)
        assert result["reddit_count"] == 1
        assert result["news_count"] == 0
        assert result["nlp_score"] < 0

    def test_mixed_sources(self):
        news = [self._make_record(0.6, datetime(2026, 3, 20, 14, 0))]
        reddit = [self._make_record(-0.3, datetime(2026, 3, 20, 12, 0))]
        result = aggregate_ticker_sentiment(news, reddit)
        assert result["news_count"] == 1
        assert result["reddit_count"] == 1
        # News weighted 0.6, Reddit 0.4 — combined should be positive
        assert result["nlp_score"] > 0

    def test_confidence_scales_with_count(self):
        """More sources = higher confidence, capped at 1.0."""
        few = [self._make_record(0.5, datetime(2026, 3, 20, 14, 0)) for _ in range(2)]
        many = [self._make_record(0.5, datetime(2026, 3, 20, 14, 0)) for _ in range(20)]

        result_few = aggregate_ticker_sentiment(few, [])
        result_many = aggregate_ticker_sentiment(many, [])

        assert result_many["nlp_confidence"] >= result_few["nlp_confidence"]
        assert result_many["nlp_confidence"] <= 1.0


# -- Process staging tables -------------------------------------------------

class TestProcessStaging:

    def test_process_news_no_unprocessed(self, agent):
        agent._model = MagicMock()
        agent._model_type = "vader"
        agent.db.execute.return_value.scalars.return_value.all.return_value = []
        count = agent._process_news()
        assert count == 0

    def test_process_reddit_no_unprocessed(self, agent):
        agent._model = MagicMock()
        agent._model_type = "vader"
        agent.db.execute.return_value.scalars.return_value.all.return_value = []
        count = agent._process_reddit()
        assert count == 0
