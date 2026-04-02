"""Tests for pipeline state persistence (PipelineRun + PipelineLog).

Verifies that pipeline run records and log entries are correctly created,
updated, and queryable through the ORM models. Requires PostgreSQL.
"""

from datetime import date, datetime

import pytest
from sqlalchemy import select

from src.database.models import PipelineLog, PipelineRun


class TestPipelineRunCRUD:

    def test_create_pipeline_run(self, db):
        run = PipelineRun(
            run_id="test_run_001",
            target_date=date(2026, 4, 1),
            status="running",
        )
        db.add(run)
        db.flush()

        assert run.id is not None
        assert run.run_id == "test_run_001"
        assert run.status == "running"
        assert run.started_at is not None

    def test_update_run_status(self, db):
        run = PipelineRun(
            run_id="test_run_002",
            target_date=date(2026, 4, 1),
            status="running",
        )
        db.add(run)
        db.flush()

        run.status = "completed"
        run.finished_at = datetime(2026, 4, 1, 12, 30, 0)
        db.flush()

        fetched = db.execute(
            select(PipelineRun).where(PipelineRun.run_id == "test_run_002")
        ).scalar_one()
        assert fetched.status == "completed"
        assert fetched.finished_at is not None

    def test_run_id_unique_constraint(self, db):
        db.add(PipelineRun(run_id="dup_run", target_date=date(2026, 4, 1), status="running"))
        db.flush()

        db.add(PipelineRun(run_id="dup_run", target_date=date(2026, 4, 2), status="running"))
        with pytest.raises(Exception):
            db.flush()

    def test_result_json_stored(self, db):
        run = PipelineRun(
            run_id="test_run_json",
            target_date=date(2026, 4, 1),
            status="completed",
            result_json={"stages": {"ingestion": {"status": "success", "elapsed_seconds": 12.5}}},
        )
        db.add(run)
        db.flush()

        fetched = db.execute(
            select(PipelineRun).where(PipelineRun.run_id == "test_run_json")
        ).scalar_one()
        assert fetched.result_json["stages"]["ingestion"]["status"] == "success"


class TestPipelineLogCRUD:

    def test_create_log_entry(self, db):
        run = PipelineRun(run_id="log_test_run", target_date=date(2026, 4, 1), status="running")
        db.add(run)
        db.flush()

        log = PipelineLog(
            run_id=run.id,
            stage="ingestion",
            level="success",
            message="ingestion success (12.5s)",
        )
        db.add(log)
        db.flush()

        assert log.id is not None
        assert log.timestamp is not None

    def test_multiple_logs_per_run(self, db):
        run = PipelineRun(run_id="multi_log_run", target_date=date(2026, 4, 1), status="completed")
        db.add(run)
        db.flush()

        stages = ["ingestion", "sentiment", "calendar", "features", "prediction"]
        for stage in stages:
            db.add(PipelineLog(
                run_id=run.id,
                stage=stage,
                level="success",
                message=f"{stage} completed",
            ))
        db.flush()

        logs = db.execute(
            select(PipelineLog).where(PipelineLog.run_id == run.id)
        ).scalars().all()
        assert len(logs) == 5

    def test_log_relationship_from_run(self, db):
        run = PipelineRun(run_id="rel_test_run", target_date=date(2026, 4, 1), status="running")
        db.add(run)
        db.flush()

        db.add(PipelineLog(run_id=run.id, stage="ingestion", level="info", message="starting"))
        db.add(PipelineLog(run_id=run.id, stage="ingestion", level="success", message="done"))
        db.flush()

        # Access via relationship
        assert len(run.logs) == 2
        assert run.logs[0].stage == "ingestion"

    def test_error_log_entry(self, db):
        run = PipelineRun(run_id="error_run", target_date=date(2026, 4, 1), status="failed")
        db.add(run)
        db.flush()

        db.add(PipelineLog(
            run_id=run.id,
            stage="sentiment",
            level="error",
            message="FinBERT model load failed: CUDA OOM",
        ))
        db.flush()

        log = db.execute(
            select(PipelineLog).where(PipelineLog.run_id == run.id)
        ).scalar_one()
        assert log.level == "error"
        assert "CUDA OOM" in log.message

    def test_cascade_delete(self, db):
        """Logs should be deleted when their parent run is deleted."""
        run = PipelineRun(run_id="cascade_run", target_date=date(2026, 4, 1), status="completed")
        db.add(run)
        db.flush()

        db.add(PipelineLog(run_id=run.id, stage="ingestion", level="success", message="ok"))
        db.flush()

        run_id = run.id
        db.delete(run)
        db.flush()

        orphaned = db.execute(
            select(PipelineLog).where(PipelineLog.run_id == run_id)
        ).scalars().all()
        assert len(orphaned) == 0
