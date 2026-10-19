"""Unit tests for AG-06 Experiment Tracker Agent."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from src.agents.experiment import ExperimentAgent, _calc_return


class TestCalcReturn:
    """Test return calculation logic."""

    def test_positive_return(self):
        entry = Decimal("100.00")
        exit_price = 110.0
        assert _calc_return(entry, exit_price) == 0.10

    def test_negative_return(self):
        entry = Decimal("100.00")
        exit_price = 90.0
        assert _calc_return(entry, exit_price) == -0.10

    def test_zero_or_none_entry_handled_safely(self):
        assert _calc_return(None, 100.0) == 0.0
        assert _calc_return(Decimal("0.0"), 100.0) == 0.0


class TestParseLLMPicks:
    """Test ticker extraction from LLM text responses."""

    def test_extracts_dollar_prefixed_tickers(self):
        mock_db = MagicMock()
        agent = ExperimentAgent(mock_db, "run_test_parse")
        text = "Based on analysis, my top 3 picks are $NVDA, $AAPL, and $MSFT for strong growth."
        picks = agent._parse_llm_picks(text)
        assert len(picks) == 3
        assert "NVDA" in picks
        assert "AAPL" in picks
        assert "MSFT" in picks

    def test_filters_common_words(self):
        mock_db = MagicMock()
        agent = ExperimentAgent(mock_db, "run_test_parse")
        text = "THE market is bullish. I pick TSLA and GOOG NOW."
        picks = agent._parse_llm_picks(text)
        assert "THE" not in picks
        assert "NOW" not in picks
        assert "TSLA" in picks
        assert "GOOG" in picks


class TestExperimentAgentRouting:
    """Test day-of-week action routing in ExperimentAgent."""

    def test_agent_name(self):
        mock_db = MagicMock()
        agent = ExperimentAgent(mock_db, "run_test_name")
        assert agent.name == "AG-06-Experiment"

    def test_midweek_action_none(self):
        mock_db = MagicMock()
        agent = ExperimentAgent(mock_db, "run_test_midweek")
        wednesday = date(2026, 3, 25)  # 2026-03-25 is Wednesday (weekday 2)
        assert wednesday.weekday() == 2
        result = agent.execute(target_date=wednesday)
        assert result["action"] == "none"
        assert "message" in result
