"""Unit tests for AG-05 XGBoost Prediction Agent."""

from datetime import date
from unittest.mock import MagicMock
import pytest
from src.agents.prediction import FEATURE_COLS, PredictionAgent


class TestPredictionAgentBasics:
    """Test PredictionAgent configuration and basic methods."""

    def test_agent_name_and_stage(self):
        mock_db = MagicMock()
        agent = PredictionAgent(mock_db, "run_test_pred")
        assert agent.name == "AG-05-Prediction"
        assert agent.stage_name == "prediction"

    def test_feature_columns_contract(self):
        assert len(FEATURE_COLS) == 13
        assert "nlp_score" in FEATURE_COLS
        assert "calendar_score" in FEATURE_COLS
        assert "combined_score" in FEATURE_COLS

    def test_fallback_predictions_no_calendar(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar.return_value = None  # No date_id found
        agent = PredictionAgent(mock_db, "run_test_fallback")
        result = agent._fallback_predictions(date(2026, 3, 20), ["AAPL"])
        assert result["predictions_generated"] == 0
        assert result["mode"] == "fallback"
