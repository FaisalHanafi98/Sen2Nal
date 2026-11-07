"""Unit tests for AG-04 Feature Engineering Agent."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.agents.features import FeatureAgent, _classify_signal
from src.constants import SIGNAL_THRESHOLDS, SignalType


class TestClassifySignal:
    """Test signal classification mapping."""

    def test_strong_buy_classification(self):
        threshold = SIGNAL_THRESHOLDS[SignalType.STRONG_BUY]
        assert _classify_signal(threshold) == "STRONG_BUY"
        assert _classify_signal(1.0) == "STRONG_BUY"

    def test_buy_classification(self):
        buy_thresh = SIGNAL_THRESHOLDS[SignalType.BUY]
        strong_thresh = SIGNAL_THRESHOLDS[SignalType.STRONG_BUY]
        score = (buy_thresh + strong_thresh) / 2.0
        assert _classify_signal(score) == "BUY"

    def test_hold_classification(self):
        hold_thresh = SIGNAL_THRESHOLDS[SignalType.HOLD]
        buy_thresh = SIGNAL_THRESHOLDS[SignalType.BUY]
        score = (hold_thresh + buy_thresh) / 2.0
        assert _classify_signal(score) == "HOLD"

    def test_avoid_classification(self):
        hold_thresh = SIGNAL_THRESHOLDS[SignalType.HOLD]
        assert _classify_signal(hold_thresh - 0.05) == "AVOID"
        assert _classify_signal(0.0) == "AVOID"


class TestFeatureAgentBasics:
    """Test basic FeatureAgent properties and instantiation."""

    def test_agent_name_and_stage(self):
        mock_db = MagicMock()
        agent = FeatureAgent(mock_db, "run_test_1")
        assert agent.name == "AG-04-Features"
        assert agent.stage_name == "features"

    def test_execute_empty_calendar_returns_error(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar.return_value = None  # No date_id found
        agent = FeatureAgent(mock_db, "run_test_2")
        future_date = date(2099, 1, 1)
        result = agent.execute(target_date=future_date, tickers=["AAPL"], calendar_signals={"AAPL": {}})
        assert "error" in result
        assert result.get("rows_written") == 0


@pytest.fixture
def feature_run(monkeypatch):
    db = MagicMock()
    agent = FeatureAgent(db, "fixture-feature-run")
    source = {"nlp_score": 0.25, "nlp_confidence": 0.5, "news_score": 0.0,
              "news_count": 1, "reddit_score": None, "reddit_count": 0}
    monkeypatch.setattr(agent, "_get_date_id", lambda target: 2)
    monkeypatch.setattr(agent, "_aggregate_nlp", lambda ticker, target: source)
    monkeypatch.setattr(agent, "_get_previous_sentiment", lambda stock, day: {
        "nlp_score": Decimal("0.1000"), "nlp_trend_days": 0,
    })
    db.execute.return_value.scalar.side_effect = [1, None]
    return agent, db, source


def run_one_feature(agent):
    return agent.run(target_date=date(2026, 11, 4), tickers=["AAPL"],
                     calendar_signals={"AAPL": {"calendar_score": 0.2}})


@pytest.mark.parametrize("bad_input", [
    {"nlp_score": float("nan")}, {"news_count": -1}, {"nlp_confidence": float("inf")},
])
def test_feature_contract_rejects_invalid_records_before_write(feature_run, bad_input):
    agent, db, source = feature_run
    source.update(bad_input)
    result = run_one_feature(agent)
    assert result["status"] == "invalid"
    assert result["error_code"] == "data_contract_violation"
    db.add.assert_not_called()
    db.flush.assert_not_called()
    db.commit.assert_not_called()
    db.rollback.assert_called_once()


def test_feature_write_preserves_observed_zero_and_counts_it(feature_run):
    agent, db, _ = feature_run
    result = run_one_feature(agent)
    assert result["status"] == "success"
    assert result["records_validated"] == 1
    assert result["data_state"] == "present"
    row = db.add.call_args.args[0]
    assert row.news_score == 0
    assert row.reddit_score is None
    assert row.nlp_score_prev == Decimal("0.1000")
    assert row.pipeline_run_id == "fixture-feature-run"
    db.commit.assert_called_once()


def test_feature_stage_rolls_back_pending_work_on_later_ticker_failure(feature_run, monkeypatch):
    agent, db, _ = feature_run
    write = agent._build_features

    def build(ticker, *args):
        if ticker == "MSFT":
            raise RuntimeError("private synthetic failure")
        return write(ticker, *args)

    monkeypatch.setattr(agent, "_build_features", build)
    result = agent.run(target_date=date(2026, 11, 4), tickers=["AAPL", "MSFT"],
                       calendar_signals={"AAPL": {"calendar_score": 0.2}, "MSFT": {}})
    assert result["status"] == "failed"
    assert "private synthetic failure" not in str(result)
    db.flush.assert_called_once()
    db.commit.assert_not_called()
    db.rollback.assert_called_once()


def test_existing_feature_row_produces_valid_empty_write_batch(feature_run):
    agent, db, _ = feature_run
    db.execute.return_value.scalar.side_effect = [1, 3]
    result = run_one_feature(agent)
    assert result["status"] == "success"
    assert result["data_state"] == "empty"
    assert result["records_validated"] == 0
    db.add.assert_not_called()
