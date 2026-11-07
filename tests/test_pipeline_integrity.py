"""Run truth at the orchestrator boundary, using only mocked stages/sessions."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from src.pipeline import runner


STAGES = ("ingestion", "sentiment", "calendar", "features", "prediction", "experiment")
AGENTS = ("IngestionAgent", "SentimentAgent", "CalendarAgent", "FeatureAgent",
          "PredictionAgent", "ExperimentAgent")


@pytest.fixture
def stages(monkeypatch):
    constructors = []
    for name in AGENTS:
        constructor = MagicMock()
        constructor.return_value.run.return_value = {"status": "success", "signals": {}}
        monkeypatch.setattr(runner, name, constructor)
        constructors.append(constructor)
    return constructors


@pytest.mark.parametrize("index", range(5))
def test_partial_critical_stage_never_advances(index, stages):
    stages[index].return_value.run.return_value = {"status": "partial"}
    result = runner.run_full_pipeline(MagicMock(), date(2026, 11, 4))
    assert result["overall_status"] == "failed"
    assert result["failed_at"] == STAGES[index]
    assert result["failure_kind"] == "partial"
    assert tuple(result["stages"]) == STAGES[:index + 1]
    for downstream in stages[index + 1:]:
        downstream.assert_not_called()


@pytest.mark.parametrize("index", range(5))
@pytest.mark.parametrize("payload", [None, [], {}, {"status": "unknown"},
                                     {"status": []}, {"status": "success", "error": "failure"}])
def test_malformed_critical_result_is_invalid_and_stops(index, payload, stages):
    stages[index].return_value.run.return_value = payload
    db = MagicMock()
    result = runner.run_full_pipeline(db, date(2026, 11, 4))
    assert result["overall_status"] == "failed"
    assert result["failed_at"] == STAGES[index]
    assert result["failure_kind"] == "invalid"
    assert result["stages"][STAGES[index]]["status"] == "invalid"
    db.rollback.assert_called()
    for downstream in stages[index + 1:]:
        downstream.assert_not_called()


def test_unexpected_stage_exception_has_a_bounded_failure_result(stages):
    stages[2].side_effect = RuntimeError("synthetic private exception detail")
    db = MagicMock()
    result = runner.run_full_pipeline(db, date(2026, 11, 4))
    assert result["overall_status"] == "failed"
    assert result["failed_at"] == "calendar"
    assert result["failure_kind"] == "failed"
    assert result["stages"]["calendar"]["error_code"] == "stage_exception"
    assert "synthetic private exception detail" not in str(result)
    db.rollback.assert_called()
    stages[3].assert_not_called()


def test_optional_experiment_exception_does_not_fail_valid_critical_stages(stages):
    stages[5].return_value.run.side_effect = RuntimeError("synthetic optional failure")
    result = runner.run_full_pipeline(MagicMock(), date(2026, 11, 4))
    assert result["overall_status"] == "success"
    assert result["non_critical_failures"] == ["experiment"]
    assert result["stages"]["experiment"]["status"] == "failed"


@pytest.mark.parametrize("elapsed", [-1, float("nan"), float("inf"), "bad", True,
                                    pytest.param(10 ** 400, id="overflowing-integer")])
def test_invalid_stage_duration_cannot_poison_the_run_result(elapsed, stages):
    stages[0].return_value.run.return_value = {"status": "success", "elapsed_seconds": elapsed}
    result = runner.run_full_pipeline(MagicMock(), date(2026, 11, 4))
    assert result["overall_status"] == "failed"
    assert result["failure_kind"] == "invalid"
    assert result["stages"]["ingestion"]["error_code"] == "invalid_stage_elapsed"
    stages[1].assert_not_called()


def test_explicit_success_with_empty_records_is_not_a_malformed_envelope(stages):
    stages[0].return_value.run.return_value = {
        "status": "success", "records": [], "elapsed_seconds": 0,
    }
    result = runner.run_full_pipeline(MagicMock(), date(2026, 11, 4))
    assert result["overall_status"] == "success"
    assert result["non_critical_failures"] == []
    assert result["stages"]["ingestion"]["elapsed_seconds"] == 0.0
