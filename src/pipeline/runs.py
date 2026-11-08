"""Admission and result storage shared by pipeline entry points."""

import logging
import uuid
from collections.abc import Callable
from datetime import date, datetime
from typing import Any, cast

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from src.database.models import PipelineLog, PipelineRun

logger = logging.getLogger(__name__)

_ADMISSION_LOCK = select(func.pg_try_advisory_xact_lock(
    func.hashtext(func.current_schema()), func.hashtext("sen2nal.pipeline.admission"),
))


class PipelineRunBusy(RuntimeError):
    """Another admission transaction or saved run is active."""


def admit_pipeline_run(db: Session, target_date: date) -> str:
    """Save one active run under the schema's PostgreSQL admission lock."""
    # Read the latest committed active row after acquiring the lock.
    db.connection(execution_options={"isolation_level": "READ COMMITTED"})
    if db.execute(_ADMISSION_LOCK).scalar_one() is not True:
        db.rollback()
        raise PipelineRunBusy("Another pipeline run is being admitted")
    active = db.execute(
        select(PipelineRun.id).where(PipelineRun.status.in_(("queued", "running"))).limit(1)
    ).scalar_one_or_none()
    if active is not None:
        db.rollback()
        raise PipelineRunBusy("A pipeline run is already active")

    run_id = f"pipeline_{uuid.uuid4().hex}"
    db.add(PipelineRun(run_id=run_id, target_date=target_date, status="queued"))
    db.commit()
    return run_id


def execute_saved_run(
    db: Session, run_id: str, run: Callable[..., dict[str, Any]],
) -> dict[str, Any] | None:
    """Claim a queued job and persist its correlated terminal outcomes."""
    claim = (
        update(PipelineRun)
        .where(PipelineRun.run_id == run_id, PipelineRun.status == "queued")
        .values(status="running")
        .returning(PipelineRun)
    )
    record = cast(Any, db.execute(claim).scalar_one_or_none())
    if record is None:
        db.rollback()
        return None

    target = record.target_date
    db.commit()
    query = select(PipelineRun).where(PipelineRun.run_id == run_id)
    try:
        result = run(db, target_date=target, run_id=run_id)
        if (result.get("run_id") != run_id or result.get("target_date") != target.isoformat()
                or result.get("overall_status") not in ("success", "failed")):
            raise ValueError("Pipeline result did not match the saved run")

        record.status = result["overall_status"]
        record.finished_at = datetime.utcnow()
        record.result_json = result
        for stage_name, stage_data in result["stages"].items():
            status = stage_data["status"]
            elapsed = stage_data["elapsed_seconds"]
            db.add(PipelineLog(
                run_id=record.id,
                stage=stage_name,
                level="success" if status == "success" else "error",
                message=f"{stage_name} {status} ({elapsed:.1f}s)",
            ))
        db.commit()
        return result
    except Exception:
        db.rollback()
        logger.error("Pipeline worker failed for run %s", run_id)
        record = cast(Any, db.execute(query).scalar_one_or_none())
        if record is None or record.status != "running":
            return None
        record.status = "failed"
        record.finished_at = datetime.utcnow()
        failed = {
            "run_id": run_id,
            "target_date": record.target_date.isoformat(),
            "overall_status": "failed",
            "error_code": "pipeline_worker_failed",
            "stages": {},
        }
        record.result_json = failed
        db.add(PipelineLog(run_id=record.id, stage="system", level="error",
                           message="Pipeline worker failed"))
        db.commit()
        return failed
