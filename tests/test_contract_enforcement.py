"""Tests for contract enforcement at agent stage boundaries.

Verifies that:
- Agents with stage_name + _validation_records raise DataContractViolation on bad output
- Valid output passes through without error
- Experiment agent has no contract and never validates
- Pipeline halts when a contract violation occurs at any stage
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from src.agents.base import BaseAgent
from src.contracts.base import DataContractViolation


# -- Helpers: concrete agents for testing ------------------------------------

class FakeValidatedAgent(BaseAgent):
    """Agent that validates output against a given stage contract."""

    def __init__(self, db, run_id=None, *, stage="sentiment", records=None):
        self._stage = stage
        self._records = records
        super().__init__(db, run_id)

    stage_name = None  # Set dynamically in __init_subclass__ or per-instance

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    @property
    def name(self) -> str:
        return "FakeValidatedAgent"

    def execute(self, **kwargs):
        return {"records": self._records}

    def _validation_records(self, result):
        return result.get("records")


def _make_validated_agent(db, stage, records):
    agent = FakeValidatedAgent(db, stage=stage, records=records)
    agent.stage_name = stage
    return agent


# -- Test: stage_name is set on all critical agents -------------------------

class TestStageNameSet:

    def test_ingestion_agent_has_stage_name(self):
        from src.agents.ingestion import IngestionAgent
        assert IngestionAgent.stage_name == "ingestion"

    def test_sentiment_agent_has_stage_name(self):
        from src.agents.sentiment import SentimentAgent
        assert SentimentAgent.stage_name == "sentiment"

    def test_calendar_agent_has_stage_name(self):
        from src.agents.calendar import CalendarAgent
        assert CalendarAgent.stage_name == "calendar"

    def test_features_agent_has_stage_name(self):
        from src.agents.features import FeatureAgent
        assert FeatureAgent.stage_name == "features"

    def test_prediction_agent_has_stage_name(self):
        from src.agents.prediction import PredictionAgent
        assert PredictionAgent.stage_name == "prediction"

    def test_experiment_agent_has_no_stage_name(self):
        from src.agents.experiment import ExperimentAgent
        assert ExperimentAgent.stage_name is None


# -- Test: valid output passes validation ------------------------------------

class TestValidOutputPasses:

    def test_sentiment_valid_output_succeeds(self):
        records = [{
            "ticker": "AAPL",
            "sentiment_score": 0.75,
            "confidence": 0.92,
            "source_count": 5,
            "model_used": "finbert",
            "processing_timestamp": datetime(2026, 3, 20, 15, 0),
        }]
        agent = _make_validated_agent(MagicMock(), "sentiment", records)
        result = agent.run()
        assert result["status"] == "success"

    def test_ingestion_valid_output_succeeds(self):
        records = [{
            "source": "newsapi",
            "raw_text": "Apple stock surges on earnings beat",
            "ticker_mentions": ["AAPL"],
            "published_at": datetime(2026, 3, 20, 14, 0),
            "fetched_at": datetime(2026, 3, 20, 15, 0),
            "external_id": "abc123",
            "content_hash": "a" * 64,
        }]
        agent = _make_validated_agent(MagicMock(), "ingestion", records)
        result = agent.run()
        assert result["status"] == "success"


# -- Test: invalid output raises DataContractViolation ----------------------

class TestInvalidOutputRaises:

    def test_sentiment_out_of_range_fails(self):
        records = [{
            "ticker": "AAPL",
            "sentiment_score": 1.5,  # exceeds max 1.0
            "confidence": 0.8,
            "source_count": 3,
            "model_used": "finbert",
            "processing_timestamp": datetime(2026, 3, 20, 15, 0),
        }]
        agent = _make_validated_agent(MagicMock(), "sentiment", records)
        result = agent.run()
        # DataContractViolation is caught by run() and turned into failed status
        assert result["status"] == "failed"
        assert "validation error" in result["error"].lower()

    def test_ingestion_missing_field_fails(self):
        records = [{
            "source": "newsapi",
            # raw_text missing
            "fetched_at": datetime(2026, 3, 20, 15, 0),
            "content_hash": "a" * 64,
        }]
        agent = _make_validated_agent(MagicMock(), "ingestion", records)
        result = agent.run()
        assert result["status"] == "failed"

    def test_calendar_score_out_of_bounds_fails(self):
        records = [{
            "ticker": "AAPL",
            "date": date(2026, 3, 20),
            "holiday_decay": -0.05,
            "day_of_week_effect": 0.10,
            "earnings_proximity": None,
            "month_avg_return": 0.011,
            "month_win_rate": 0.65,
            "trading_day_of_month": 15,
            "calendar_score": 1.5,  # exceeds max 1.0
        }]
        agent = _make_validated_agent(MagicMock(), "calendar", records)
        result = agent.run()
        assert result["status"] == "failed"


# -- Test: pipeline halts on contract violation ------------------------------

class TestPipelineHaltsOnContractViolation:

    @patch("src.pipeline.runner.ExperimentAgent")
    @patch("src.pipeline.runner.PredictionAgent")
    @patch("src.pipeline.runner.FeatureAgent")
    @patch("src.pipeline.runner.CalendarAgent")
    @patch("src.pipeline.runner.SentimentAgent")
    @patch("src.pipeline.runner.IngestionAgent")
    def test_pipeline_halts_when_sentiment_contract_violated(
        self, mock_ingest, mock_sent, mock_cal, mock_feat, mock_pred, mock_exp
    ):
        from src.pipeline.runner import run_full_pipeline

        mock_ingest.return_value.run.return_value = {"status": "success"}
        # Sentiment fails due to contract violation (status=failed)
        mock_sent.return_value.run.return_value = {
            "status": "failed",
            "error": "1 validation error(s) at stage 'sentiment'",
        }

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
    def test_pipeline_halts_when_ingestion_contract_violated(
        self, mock_ingest, mock_sent, mock_cal, mock_feat, mock_pred, mock_exp
    ):
        from src.pipeline.runner import run_full_pipeline

        mock_ingest.return_value.run.return_value = {
            "status": "failed",
            "error": "2 validation error(s) at stage 'ingestion'",
        }

        result = run_full_pipeline(MagicMock(), date(2026, 3, 20))

        assert result["overall_status"] == "failed"
        assert result["failed_at"] == "ingestion"
        mock_sent.return_value.run.assert_not_called()


# -- Test: experiment agent does not validate --------------------------------

class TestExperimentNoValidation:

    def test_experiment_has_no_stage_name(self):
        from src.agents.experiment import ExperimentAgent
        assert ExperimentAgent.stage_name is None

    def test_agent_without_stage_name_skips_validation(self):
        """An agent with no stage_name never calls validate_stage."""

        class NoValidationAgent(BaseAgent):
            @property
            def name(self):
                return "NoValidation"

            def execute(self, **kwargs):
                return {"data": "anything"}

        agent = NoValidationAgent(MagicMock())
        assert agent.stage_name is None
        result = agent.run()
        assert result["status"] == "success"
