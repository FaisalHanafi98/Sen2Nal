"""Tests for pipeline runner stage gating.

Verifies that the pipeline halts on critical stage failure and
propagates results correctly on success.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from src.pipeline.runner import run_full_pipeline


def _make_agent_cls(return_value: dict):
    """Build a fake agent class whose .run() returns the given dict."""
    agent = MagicMock()
    agent.run.return_value = return_value

    cls = MagicMock(return_value=agent)
    return cls


SUCCESS = {"status": "success"}
FAILURE = {"status": "failed", "error": "boom"}


# -- Stage gating: pipeline halts when a critical stage fails ----------------

@patch("src.pipeline.runner.ExperimentAgent")
@patch("src.pipeline.runner.PredictionAgent")
@patch("src.pipeline.runner.FeatureAgent")
@patch("src.pipeline.runner.CalendarAgent")
@patch("src.pipeline.runner.SentimentAgent")
@patch("src.pipeline.runner.IngestionAgent")
def test_pipeline_halts_on_ingestion_failure(
    mock_ingest, mock_sent, mock_cal, mock_feat, mock_pred, mock_exp
):
    mock_ingest.return_value.run.return_value = FAILURE

    result = run_full_pipeline(MagicMock(), date(2026, 3, 20))

    assert result["overall_status"] == "failed"
    assert result["failed_at"] == "ingestion"
    # Downstream agents never called
    mock_sent.return_value.run.assert_not_called()
    mock_cal.return_value.run.assert_not_called()
    mock_feat.return_value.run.assert_not_called()
    mock_pred.return_value.run.assert_not_called()
    mock_exp.return_value.run.assert_not_called()


@patch("src.pipeline.runner.ExperimentAgent")
@patch("src.pipeline.runner.PredictionAgent")
@patch("src.pipeline.runner.FeatureAgent")
@patch("src.pipeline.runner.CalendarAgent")
@patch("src.pipeline.runner.SentimentAgent")
@patch("src.pipeline.runner.IngestionAgent")
def test_pipeline_halts_on_sentiment_failure(
    mock_ingest, mock_sent, mock_cal, mock_feat, mock_pred, mock_exp
):
    mock_ingest.return_value.run.return_value = SUCCESS
    mock_sent.return_value.run.return_value = FAILURE

    result = run_full_pipeline(MagicMock(), date(2026, 3, 20))

    assert result["overall_status"] == "failed"
    assert result["failed_at"] == "sentiment"
    mock_cal.return_value.run.assert_not_called()


@patch("src.pipeline.runner.ExperimentAgent")
@patch("src.pipeline.runner.PredictionAgent")
@patch("src.pipeline.runner.FeatureAgent")
@patch("src.pipeline.runner.CalendarAgent")
@patch("src.pipeline.runner.SentimentAgent")
@patch("src.pipeline.runner.IngestionAgent")
def test_pipeline_halts_on_calendar_failure(
    mock_ingest, mock_sent, mock_cal, mock_feat, mock_pred, mock_exp
):
    mock_ingest.return_value.run.return_value = SUCCESS
    mock_sent.return_value.run.return_value = SUCCESS
    mock_cal.return_value.run.return_value = FAILURE

    result = run_full_pipeline(MagicMock(), date(2026, 3, 20))

    assert result["overall_status"] == "failed"
    assert result["failed_at"] == "calendar"
    mock_feat.return_value.run.assert_not_called()


@patch("src.pipeline.runner.ExperimentAgent")
@patch("src.pipeline.runner.PredictionAgent")
@patch("src.pipeline.runner.FeatureAgent")
@patch("src.pipeline.runner.CalendarAgent")
@patch("src.pipeline.runner.SentimentAgent")
@patch("src.pipeline.runner.IngestionAgent")
def test_pipeline_halts_on_features_failure(
    mock_ingest, mock_sent, mock_cal, mock_feat, mock_pred, mock_exp
):
    mock_ingest.return_value.run.return_value = SUCCESS
    mock_sent.return_value.run.return_value = SUCCESS
    mock_cal.return_value.run.return_value = {"status": "success", "signals": {}}
    mock_feat.return_value.run.return_value = FAILURE

    result = run_full_pipeline(MagicMock(), date(2026, 3, 20))

    assert result["overall_status"] == "failed"
    assert result["failed_at"] == "features"
    mock_pred.return_value.run.assert_not_called()


@patch("src.pipeline.runner.ExperimentAgent")
@patch("src.pipeline.runner.PredictionAgent")
@patch("src.pipeline.runner.FeatureAgent")
@patch("src.pipeline.runner.CalendarAgent")
@patch("src.pipeline.runner.SentimentAgent")
@patch("src.pipeline.runner.IngestionAgent")
def test_pipeline_halts_on_prediction_failure(
    mock_ingest, mock_sent, mock_cal, mock_feat, mock_pred, mock_exp
):
    mock_ingest.return_value.run.return_value = SUCCESS
    mock_sent.return_value.run.return_value = SUCCESS
    mock_cal.return_value.run.return_value = {"status": "success", "signals": {}}
    mock_feat.return_value.run.return_value = SUCCESS
    mock_pred.return_value.run.return_value = FAILURE

    result = run_full_pipeline(MagicMock(), date(2026, 3, 20))

    assert result["overall_status"] == "failed"
    assert result["failed_at"] == "prediction"
    mock_exp.return_value.run.assert_not_called()


# -- Experiment is non-critical: failure doesn't halt -------------------------

@patch("src.pipeline.runner.ExperimentAgent")
@patch("src.pipeline.runner.PredictionAgent")
@patch("src.pipeline.runner.FeatureAgent")
@patch("src.pipeline.runner.CalendarAgent")
@patch("src.pipeline.runner.SentimentAgent")
@patch("src.pipeline.runner.IngestionAgent")
def test_experiment_failure_does_not_halt_pipeline(
    mock_ingest, mock_sent, mock_cal, mock_feat, mock_pred, mock_exp
):
    mock_ingest.return_value.run.return_value = SUCCESS
    mock_sent.return_value.run.return_value = SUCCESS
    mock_cal.return_value.run.return_value = {"status": "success", "signals": {}}
    mock_feat.return_value.run.return_value = SUCCESS
    mock_pred.return_value.run.return_value = SUCCESS
    mock_exp.return_value.run.return_value = FAILURE

    result = run_full_pipeline(MagicMock(), date(2026, 3, 20))

    assert result["overall_status"] == "success"
    assert result["failed_stages"] == []


# -- Full success path --------------------------------------------------------

@patch("src.pipeline.runner.ExperimentAgent")
@patch("src.pipeline.runner.PredictionAgent")
@patch("src.pipeline.runner.FeatureAgent")
@patch("src.pipeline.runner.CalendarAgent")
@patch("src.pipeline.runner.SentimentAgent")
@patch("src.pipeline.runner.IngestionAgent")
def test_full_pipeline_success(
    mock_ingest, mock_sent, mock_cal, mock_feat, mock_pred, mock_exp
):
    mock_ingest.return_value.run.return_value = SUCCESS
    mock_sent.return_value.run.return_value = SUCCESS
    mock_cal.return_value.run.return_value = {"status": "success", "signals": {"AAPL": {}}}
    mock_feat.return_value.run.return_value = SUCCESS
    mock_pred.return_value.run.return_value = SUCCESS
    mock_exp.return_value.run.return_value = SUCCESS

    result = run_full_pipeline(MagicMock(), date(2026, 3, 20))

    assert result["overall_status"] == "success"
    assert result["failed_stages"] == []
    assert "run_id" in result
    assert result["target_date"] == "2026-03-20"
    assert set(result["stages"].keys()) == {
        "ingestion", "sentiment", "calendar", "features", "prediction", "experiment"
    }


# -- Result structure ---------------------------------------------------------

@patch("src.pipeline.runner.ExperimentAgent")
@patch("src.pipeline.runner.PredictionAgent")
@patch("src.pipeline.runner.FeatureAgent")
@patch("src.pipeline.runner.CalendarAgent")
@patch("src.pipeline.runner.SentimentAgent")
@patch("src.pipeline.runner.IngestionAgent")
def test_failed_result_contains_failed_stages_list(
    mock_ingest, mock_sent, mock_cal, mock_feat, mock_pred, mock_exp
):
    mock_ingest.return_value.run.return_value = FAILURE

    result = run_full_pipeline(MagicMock(), date(2026, 3, 20))

    assert "failed_stages" in result
    assert "ingestion" in result["failed_stages"]
