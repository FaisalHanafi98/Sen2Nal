"""Unit tests for AG-05 XGBoost Prediction Agent."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
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


@pytest.fixture
def prediction_run(monkeypatch):
    db = MagicMock()
    agent = PredictionAgent(db, "fixture-prediction")
    model = MagicMock()
    model.feature_importances_ = np.ones(len(FEATURE_COLS))
    model.predict_proba.return_value = np.array([[0.3, 0.7]])
    monkeypatch.setattr(agent, "_load_or_train", lambda *args, **kwargs: model)
    monkeypatch.setattr(agent, "_build_dataset", lambda tickers: (
        np.zeros((30, len(FEATURE_COLS))), np.zeros(30), [],
    ))
    signal = SimpleNamespace(nlp_score=0.2, nlp_momentum=0.1, nlp_confidence=0.5,
                             news_count=1, reddit_count=0, calendar_score=0.3,
                             month_avg_return=0.1, month_win_rate=0.4, combined_score=0.6,
                             conflict_flag=False)
    db.execute.return_value.scalar.side_effect = [2, 1, signal, None, None]
    return agent, db, model


def run_prediction(agent):
    return agent.run(target_date=date(2026, 11, 4), tickers=["AAPL"])


@pytest.mark.parametrize("probabilities", [
    [[0.8, -0.2]], [[0.6, 0.7]], [[float("nan"), 0.3]], [[0.1, 0.2, 0.7]], [],
])
def test_malformed_model_distribution_is_rejected_before_write(prediction_run, probabilities):
    agent, db, model = prediction_run
    model.predict_proba.return_value = np.array(probabilities)
    result = run_prediction(agent)
    assert result["status"] == "invalid"
    assert result["error_code"] == "data_contract_violation"
    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.rollback.assert_called_once()


def test_nonfinite_feature_contribution_is_rejected_before_write(prediction_run):
    agent, db, model = prediction_run
    model.feature_importances_[0] = float("inf")
    assert run_prediction(agent)["status"] == "invalid"
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_valid_prediction_commits_and_reports_its_mode(prediction_run):
    agent, db, _ = prediction_run
    result = run_prediction(agent)
    assert result["status"] == "success"
    assert result["records_validated"] == 1
    assert result["mode"] == "xgboost"
    assert result["disclaimer"] == "NOT FINANCIAL ADVICE"
    row = db.add.call_args.args[0]
    assert row.predicted_direction == "UP"
    assert row.predicted_score == 0.7
    db.commit.assert_called_once()


@pytest.mark.parametrize("value", [0.0, None, 1.1])
def test_fallback_preserves_zero_and_abstains_on_missing_or_invalid_input(prediction_run,
                                                                       monkeypatch, value):
    agent, db, _ = prediction_run
    monkeypatch.setattr(agent, "_build_dataset", lambda tickers: (np.array([]), np.array([]), []))
    db.execute.return_value.scalar.side_effect = [2, 1, SimpleNamespace(combined_score=value), None]
    result = run_prediction(agent)
    if value == 0:
        assert result["status"] == "success"
        row = db.add.call_args.args[0]
        assert row.predicted_score == 0
        assert row.predicted_direction == "DOWN"
        assert "fallback" in row.model_version and len(row.model_version) <= 20
        assert result["records_validated"] == 1
    elif value is None:
        assert result["status"] == "success"
        assert result["data_state"] == "empty"
        db.add.assert_not_called()
    else:
        assert result["status"] == "invalid"
        db.add.assert_not_called()
        db.commit.assert_not_called()
