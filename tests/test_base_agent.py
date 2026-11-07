"""Tests for BaseAgent run() wrapper behavior."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.agents.base import BaseAgent


class ConcreteAgent(BaseAgent):
    """Test agent that returns a fixed result."""

    def __init__(self, db, run_id=None, *, result=None, error=None):
        super().__init__(db, run_id)
        self._result = result or {"data": "ok"}
        self._error = error

    @property
    def name(self) -> str:
        return "TestAgent"

    def execute(self, **kwargs):
        if self._error:
            raise self._error
        return self._result


class ValidatingAgent(ConcreteAgent):
    """Agent with validation wired."""

    stage_name = "sentiment"

    def _validation_records(self, result):
        return result.get("records")


class TestRunWrapper:

    def test_success_wraps_result(self):
        agent = ConcreteAgent(MagicMock(), "run_1", result={"count": 5})
        result = agent.run()
        assert result["status"] == "success"
        assert result["agent"] == "TestAgent"
        assert result["run_id"] == "run_1"
        assert result["count"] == 5
        assert "elapsed_seconds" in result

    def test_failure_catches_exception_without_exposing_its_message(self, caplog):
        agent = ConcreteAgent(MagicMock(), "run_2", error=RuntimeError("boom"))
        result = agent.run()
        assert result["status"] == "failed"
        assert result["error_code"] == "stage_exception"
        assert "boom" not in str(result)
        assert "boom" not in caplog.text
        assert result["agent"] == "TestAgent"

    @pytest.mark.parametrize("payload", [
        {"status": "success"}, {"agent": "other"}, {"run_id": "another-run"},
        {"elapsed_seconds": 0}, {"error_code": "forged"}, ["malformed"],
    ])
    def test_execute_cannot_supply_runner_metadata(self, payload):
        db = MagicMock()
        result = ConcreteAgent(db, "owned-run", result=payload).run()
        assert result["status"] == "invalid"
        assert result["error_code"] == "invalid_stage_payload"
        assert result["run_id"] == "owned-run"
        assert result["agent"] == "TestAgent"
        db.rollback.assert_called_once()

    def test_execution_error_payload_is_a_failure(self, caplog):
        db = MagicMock()
        result = ConcreteAgent(db, result={"error": "private input detail", "count": 0}).run()
        assert result["status"] == "failed"
        assert result["error_code"] == "stage_execution_error"
        assert "private input detail" not in str(result)
        assert "private input detail" not in caplog.text
        db.rollback.assert_called_once()

    def test_failure_rolls_back_session(self):
        db = MagicMock()
        agent = ConcreteAgent(db, error=ValueError("bad"))
        agent.run()
        db.rollback.assert_called_once()

    def test_generates_run_id_if_not_provided(self):
        agent = ConcreteAgent(MagicMock())
        assert agent.run_id.startswith("run_")


class TestValidationHook:

    def test_validation_runs_when_configured(self):
        agent = ValidatingAgent(
            MagicMock(),
            result={
                "records": [
                    {
                        "ticker": "AAPL",
                        "sentiment_score": 0.5,
                        "confidence": 0.8,
                        "source_count": 3,
                        "model_used": "finbert",
                        "processing_timestamp": datetime(2026, 3, 20, 15, 0, 0),
                    }
                ]
            },
        )
        result = agent.run()
        assert result["status"] == "success"

    def test_validation_skipped_when_no_records(self):
        agent = ValidatingAgent(MagicMock(), result={"records": None})
        result = agent.run()
        assert result["status"] == "success"

    def test_no_validation_without_stage_name(self):
        agent = ConcreteAgent(MagicMock())
        assert agent.stage_name is None
        result = agent.run()
        assert result["status"] == "success"
