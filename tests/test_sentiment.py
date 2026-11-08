"""Tests for AG-02 Sentiment Agent.

Tests sentiment scoring with mocked models and an optional local VADER lexicon.
No real model downloads or GPU inference in tests.
"""

from datetime import datetime
from types import SimpleNamespace
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

def test_missing_vader_lexicon_skips_without_downloading(monkeypatch):
    import nltk
    from nltk.sentiment import vader

    def missing_lexicon():
        raise LookupError("Fixture lexicon unavailable")

    def unexpected_download(*args, **kwargs):
        pytest.fail("VADER tests must use a local lexicon")

    monkeypatch.setattr(vader, "SentimentIntensityAnalyzer", missing_lexicon)
    monkeypatch.setattr(nltk, "download", unexpected_download)
    with pytest.raises(pytest.skip.Exception, match="Local VADER lexicon"):
        TestVaderFallback()._make_vader_agent()


class TestVaderFallback:

    def _make_vader_agent(self):
        """Create an agent that uses VADER (simulating FinBERT unavailable)."""
        db = MagicMock()
        agent = SentimentAgent(db=db, run_id="test_vader")
        # Force VADER mode
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        try:
            agent._model = SentimentIntensityAnalyzer()
        except LookupError:
            pytest.skip("Local VADER lexicon unavailable")
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

    def test_empty_text_returns_zero(self, agent):
        score, confidence = agent._score_text("")
        assert score == 0.0
        assert confidence == 0.0

    def test_short_text_returns_zero(self, agent):
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

    @pytest.mark.parametrize("scores", [[], [(float("nan"), 0.5)], [(0.2, 1.1)], [(0.2,)]])
    def test_invalid_score_batch_leaves_news_unprocessed(self, agent, monkeypatch, scores):
        record = SimpleNamespace(headline="Synthetic news", summary="Example",
                                 is_processed=False, sentiment_score=None)
        agent._model = MagicMock()
        agent._model_type = "vader"
        news_read, empty_read = MagicMock(), MagicMock()
        news_read.scalars.return_value.all.return_value = [record]
        empty_read.scalars.return_value.all.return_value = []
        agent.db.execute.side_effect = [news_read, empty_read]
        monkeypatch.setattr(agent, "_score_batch", lambda texts: scores)

        result = agent.run()

        assert result["status"] == "invalid"
        assert result["error_code"] == "data_contract_violation"
        assert record.is_processed is False and record.sentiment_score is None
        agent.db.flush.assert_not_called()
        agent.db.commit.assert_not_called()
        agent.db.rollback.assert_called_once()

    def test_validated_scores_commit_and_report_source_counts(self, agent, monkeypatch):
        news = SimpleNamespace(headline="Synthetic news", summary="Example", is_processed=False)
        post = SimpleNamespace(title="Synthetic post", body="Example", is_processed=False)
        agent._model = MagicMock()
        agent._model_type = "vader"
        reads = [MagicMock(), MagicMock()]
        reads[0].scalars.return_value.all.return_value = [news]
        reads[1].scalars.return_value.all.return_value = [post]
        agent.db.execute.side_effect = reads
        monkeypatch.setattr(agent, "_score_batch", MagicMock(side_effect=[[(0.4, 0.8)], [(-0.6, 0.9)]]))

        result = agent.run()

        assert result["status"] == "success"
        assert (result["news_processed"], result["reddit_processed"], result["records_validated"]) == (1, 1, 2)
        assert result["data_state"] == "present"
        assert result["model_used"] == "vader"
        assert news.is_processed and news.sentiment_score == 0.4
        assert post.is_processed and post.sentiment_score == -0.6
        agent.db.commit.assert_called_once()
        agent.db.rollback.assert_not_called()

    def test_empty_selection_is_a_valid_empty_batch(self, agent, monkeypatch):
        agent._model = MagicMock()
        agent._model_type = "vader"
        agent.db.execute.return_value.scalars.return_value.all.return_value = []
        scorer = MagicMock()
        monkeypatch.setattr(agent, "_score_batch", scorer)

        result = agent.run()

        assert result["status"] == "success"
        assert result["data_state"] == "empty"
        assert result["records_validated"] == 0
        assert result["model_used"] is None
        scorer.assert_not_called()
        agent.db.flush.assert_not_called()

    def test_invalid_reddit_scores_roll_back_pending_news_work(self, agent, monkeypatch):
        news = SimpleNamespace(headline="Synthetic news", summary="Example")
        post = SimpleNamespace(title="Synthetic post", body="Example", is_processed=False)
        agent._model = MagicMock()
        agent._model_type = "vader"
        reads = [MagicMock(), MagicMock()]
        reads[0].scalars.return_value.all.return_value = [news]
        reads[1].scalars.return_value.all.return_value = [post]
        agent.db.execute.side_effect = reads
        monkeypatch.setattr(agent, "_score_batch", MagicMock(side_effect=[[(0.4, 0.8)], []]))

        assert agent.run()["status"] == "invalid"
        assert post.is_processed is False
        agent.db.flush.assert_called_once()
        agent.db.commit.assert_not_called()
        agent.db.rollback.assert_called_once()
