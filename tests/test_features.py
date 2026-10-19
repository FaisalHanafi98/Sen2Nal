"""Unit tests for AG-04 Feature Engineering Agent."""

from datetime import date
from unittest.mock import MagicMock
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
