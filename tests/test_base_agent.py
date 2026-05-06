"""Tests for BaseAgent run() wrapper behavior."""

from datetime import datetime
from unittest.mock import MagicMock

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

    def test_failure_catches_exception(self):
        agent = ConcreteAgent(MagicMock(), "run_2", error=RuntimeError("boom"))
        result = agent.run()
        assert result["status"] == "failed"
        assert result["error"] == "boom"
        assert result["agent"] == "TestAgent"

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
