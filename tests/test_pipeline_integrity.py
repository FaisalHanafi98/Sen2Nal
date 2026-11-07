"""Run truth at the orchestrator boundary, using only mocked stages/sessions."""

from datetime import date
from unittest.mock import MagicMock

import anyio.to_thread
import httpx
import pytest
from sniffio import current_async_library_cvar
from fastapi import FastAPI

from src.api.routers import pipeline as pipeline_routes
from src.database import connection
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


@pytest.fixture
def pipeline_client(monkeypatch):
    app = FastAPI()
    app.include_router(pipeline_routes.router)
    admission = MagicMock()
    worker = MagicMock()
    worker_factory = MagicMock(return_value=worker)
    app.dependency_overrides[pipeline_routes.get_db] = lambda: admission
    monkeypatch.setattr(connection, "SessionLocal", worker_factory)
    monkeypatch.setattr(pipeline_routes.settings, "pipeline_api_key", "fixture-only")

    def attach(row):
        row.id = 17
        worker.execute.return_value.scalar_one_or_none.return_value = row

    admission.add.side_effect = attach

    async def inline_thread_call(function, *args, **kwargs):
        return function(*args)

    monkeypatch.setattr(anyio.to_thread, "run_sync", inline_thread_call)

    async def request(method, path, **kwargs):
        transport = httpx.ASGITransport(app)
        response = await transport.handle_async_request(
            httpx.Request(method, f"http://testserver{path}", **kwargs)
        )
        await response.aread()
        return response

    def send(method, path, **kwargs):
        # All I/O is mocked or in-memory. Drive ASGI without a Windows wakeup socket.
        operation = request(method, path, **kwargs)
        token = current_async_library_cvar.set("asyncio")
        try:
            operation.send(None)
        except StopIteration as response:
            return response.value
        finally:
            operation.close()
            current_async_library_cvar.reset(token)
        raise AssertionError("Mocked ASGI request unexpectedly suspended")

    return send, admission, worker, worker_factory


def test_trigger_worker_and_stage_results_share_the_saved_run(pipeline_client, stages):
    send, admission, worker, _ = pipeline_client
    response = send("POST", "/api/v1/pipeline/run", headers={"X-Api-Key": "fixture-only"})
    assert response.status_code == 200
    row = admission.add.call_args.args[0]
    assert row.run_id == response.json()["run_id"]
    assert row.result_json["run_id"] == row.run_id
    assert row.result_json["target_date"] == row.target_date.isoformat()
    assert row.status == "success"
    for constructor in stages:
        constructor.assert_called_once_with(worker, row.run_id)
    assert all(value["run_id"] == row.run_id for value in row.result_json["stages"].values())
    assert {call.args[0].run_id for call in worker.add.call_args_list} == {row.id}
    worker.close.assert_called_once()


@pytest.mark.parametrize("headers", [{}, {"X-Api-Key": "wrong-fixture"}])
def test_trigger_refuses_bad_key_before_writing_or_starting_a_run(pipeline_client, stages, headers):
    send, admission, _, worker_factory = pipeline_client
    assert send("POST", "/api/v1/pipeline/run", headers=headers).status_code == 403
    admission.add.assert_not_called()
    admission.commit.assert_not_called()
    worker_factory.assert_not_called()
    stages[0].assert_not_called()


@pytest.mark.parametrize("state", [None, "success"])
def test_worker_skips_missing_or_terminal_run_rows(pipeline_client, stages, state):
    send, admission, worker, _ = pipeline_client

    def attach(row):
        row.status = state
        worker.execute.return_value.scalar_one_or_none.return_value = row if state else None

    admission.add.side_effect = attach
    assert send("POST", "/api/v1/pipeline/run", headers={"X-Api-Key": "fixture-only"}).is_success
    stages[0].assert_not_called()
    worker.add.assert_not_called()
    worker.commit.assert_not_called()
    worker.close.assert_called_once()


def test_worker_refuses_a_result_for_another_run(pipeline_client, monkeypatch):
    send, admission, worker, _ = pipeline_client
    monkeypatch.setattr(runner, "run_full_pipeline", lambda *args, **kwargs: {
        "run_id": "different-run", "overall_status": "success", "error": "private detail",
    })
    assert send("POST", "/api/v1/pipeline/run", headers={"X-Api-Key": "fixture-only"}).is_success
    row = admission.add.call_args.args[0]
    assert row.status == "failed"
    assert row.result_json["run_id"] == row.run_id
    assert "private detail" not in str(row.result_json)
    worker.rollback.assert_called_once()


def test_mismatched_stage_id_stops_the_active_run(stages):
    stages[0].return_value.run.return_value = {"status": "success", "run_id": "other-run"}
    result = runner.run_full_pipeline(MagicMock(), date(2026, 11, 4))
    assert result["failure_kind"] == "invalid"
    assert result["stages"]["ingestion"]["run_id"] == result["run_id"]
    stages[1].assert_not_called()
