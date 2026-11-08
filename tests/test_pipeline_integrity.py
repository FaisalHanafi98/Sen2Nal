"""Run truth at the orchestrator boundary, using only mocked stages/sessions."""

from datetime import date, datetime
from types import SimpleNamespace
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


@pytest.mark.parametrize("tickers", [[], ["FIXTURE_UNKNOWN"]])
def test_explicit_request_with_no_allowed_tickers_never_runs_a_stage(stages, tickers):
    result = runner.run_full_pipeline(MagicMock(), date(2026, 11, 4), tickers=tickers)
    assert result["overall_status"] == "failed"
    assert result["failed_at"] == "validation"
    assert result["stages"] == {}
    for constructor in stages:
        constructor.assert_not_called()


def test_runner_preserves_first_seen_order_of_distinct_allowed_tickers(stages):
    day = date(2026, 11, 4)
    result = runner.run_full_pipeline(
        MagicMock(), day, tickers=["MSFT", "FIXTURE_UNKNOWN", "AAPL", "MSFT"],
    )
    assert result["overall_status"] == "success"
    stages[0].return_value.run.assert_called_once_with(target_date=day, tickers=["MSFT", "AAPL"])


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


def status_row(status, stages=None, *, report_id="saved-run"):
    day = date(2026, 11, 4)
    return SimpleNamespace(
        run_id="saved-run", target_date=day, status=status,
        started_at=datetime(2026, 11, 4, 13),
        finished_at=datetime(2026, 11, 4, 13, 1) if status != "running" else None,
        result_json={"run_id": report_id, "target_date": day.isoformat(),
                     "overall_status": status, "stages": stages} if stages is not None else None,
    )


def test_status_reports_the_failed_run_even_with_historical_fact_rows(pipeline_client):
    send, db, _, _ = pipeline_client
    db.execute.return_value.scalar.return_value = 77
    db.execute.return_value.scalar_one_or_none.return_value = status_row("failed", {
        "ingestion": {"status": "partial", "elapsed_seconds": 1.2, "run_id": "saved-run",
                      "error": "private input detail"},
    })
    response = send("GET", "/api/v1/pipeline/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["runId"] == "saved-run"
    assert payload["pipelineStatus"] == "failed"
    stages = {stage["stage"]: stage for stage in payload["stages"]}
    assert stages["Data Ingestion"]["status"] == "error"
    assert stages["Data Ingestion"]["outcome"] == "partial"
    assert all(stage["status"] == "idle" for name, stage in stages.items()
               if name != "Data Ingestion")
    assert "private input detail" not in response.text
    db.execute.assert_called_once()


def test_legacy_success_with_an_unrelated_result_stays_unverified(pipeline_client):
    send, db, _, _ = pipeline_client
    db.execute.return_value.scalar.return_value = 77
    db.execute.return_value.scalar_one_or_none.return_value = status_row(
        "success", {}, report_id="different-run",
    )
    payload = send("GET", "/api/v1/pipeline/status").json()
    assert payload["pipelineStatus"] == "unverified"
    assert payload["recordedStatus"] == "success"
    assert all(stage["status"] == "idle" for stage in payload["stages"])


def test_status_retains_zero_counts_for_a_correlated_completed_stage(pipeline_client):
    send, db, _, _ = pipeline_client
    results = {name: {"status": "success", "run_id": "saved-run", "elapsed_seconds": 0.1}
               for name in STAGES[:5]}
    results["ingestion"]["news_ingested"] = 0
    db.execute.return_value.scalar.return_value = 77
    db.execute.return_value.scalar_one_or_none.return_value = status_row("success", results)
    payload = send("GET", "/api/v1/pipeline/status").json()
    assert payload["pipelineStatus"] == "success"
    stages = {stage["stage"]: stage for stage in payload["stages"]}
    assert stages["Data Ingestion"]["details"] == {"news": 0}
    assert stages["Calendar Patterns"]["status"] == "complete"
    assert stages["Output & Storage"]["status"] == "complete"


def test_status_for_active_run_avoids_guessing_which_stage_is_running(pipeline_client):
    send, db, _, _ = pipeline_client
    db.execute.return_value.scalar.return_value = 77
    db.execute.return_value.scalar_one_or_none.return_value = status_row("running")
    payload = send("GET", "/api/v1/pipeline/status").json()
    assert payload["pipelineStatus"] == "running"
    assert all(stage["status"] == "idle" for stage in payload["stages"])


def test_status_can_request_one_run_and_rejects_invalid_ids(pipeline_client):
    send, db, _, _ = pipeline_client
    db.execute.return_value.scalar.return_value = 0
    db.execute.return_value.scalar_one_or_none.return_value = None
    assert send("GET", "/api/v1/pipeline/status", params={"run_id": "invalid/id"}).status_code == 422
    db.execute.assert_not_called()
    assert send("GET", "/api/v1/pipeline/status", params={"run_id": "missing"}).status_code == 404
    assert "missing" in db.execute.call_args.args[0].compile().params.values()


@pytest.mark.parametrize("override", [
    {"run_id": "another-run"}, {"elapsed_seconds": "unknown"},
    {"elapsed_seconds": float("inf")}, {"error": "private detail"},
])
def test_inconsistent_stage_report_cannot_certify_saved_success(pipeline_client, override):
    send, db, _, _ = pipeline_client
    reports = {name: {"status": "success", "run_id": "saved-run", "elapsed_seconds": 0.2}
               for name in STAGES[:5]}
    reports["prediction"].update(override)
    db.execute.return_value.scalar_one_or_none.return_value = status_row("success", reports)
    payload = send("GET", "/api/v1/pipeline/status", params={"run_id": "saved-run"}).json()
    assert payload["runId"] == "saved-run"
    assert payload["pipelineStatus"] == "unverified"
    assert payload["stages"][-2]["status"] == "idle"
    assert payload["stages"][-1]["status"] == "idle"


@pytest.mark.parametrize("params", [{"run_id": "invalid/id"}, {"limit": 0}, {"limit": 101}])
def test_logs_reject_invalid_query_before_reading_db(pipeline_client, params):
    send, db, _, _ = pipeline_client
    assert send("GET", "/api/v1/pipeline/logs", params=params).status_code == 422
    db.execute.assert_not_called()


def test_logs_filter_by_run_and_withhold_legacy_exception_text(pipeline_client):
    send, db, _, _ = pipeline_client
    timestamp = datetime(2026, 11, 4, 13)
    db.execute.return_value.all.return_value = [
        (SimpleNamespace(timestamp=timestamp, stage="ingestion", level="success",
                         message="ingestion success (0.2s)"), "saved-run"),
        (SimpleNamespace(timestamp=timestamp, stage="system", level="error",
                         message="Pipeline failed: synthetic private detail"), "saved-run"),
    ]
    response = send("GET", "/api/v1/pipeline/logs", params={"run_id": "saved-run", "limit": 2})
    assert response.status_code == 200
    logs = response.json()["logs"]
    assert [log["runId"] for log in logs] == ["saved-run", "saved-run"]
    assert logs[0]["message"] == "ingestion success (0.2s)"
    assert logs[1]["message"] == "Log details unavailable"
    assert "synthetic private detail" not in response.text
    statement = db.execute.call_args.args[0]
    assert set(statement.compile().params.values()) == {"saved-run", 2}
