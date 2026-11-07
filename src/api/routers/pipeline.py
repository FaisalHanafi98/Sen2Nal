"""Pipeline monitoring and control endpoints."""

import logging
import math
from datetime import datetime
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, BackgroundTasks, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import settings
from src.constants import API_PREFIX
from src.database.connection import get_db
from src.database.models import PipelineLog, PipelineRun

logger = logging.getLogger(__name__)


def verify_pipeline_key(x_api_key: str | None = Header(default=None)) -> None:
    """Reject requests without a valid API key when pipeline_api_key is configured."""
    required_key = settings.pipeline_api_key
    if required_key is None:
        return
    if x_api_key != required_key:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")

router = APIRouter(prefix=f"{API_PREFIX}/pipeline", tags=["Pipeline"])

_STAGE_VIEWS = (
    ("ingestion", "Data Ingestion", {
        "news": "news_ingested", "reddit": "reddit_ingested", "prices": "prices_ingested",
    }),
    ("sentiment", "FinBERT NLP", {"newsProcessed": "news_processed",
                                  "redditProcessed": "reddit_processed"}),
    ("calendar", "Calendar Patterns", {"tickersComputed": "tickers_computed"}),
    ("features", "Feature Engineering", {"sentimentRows": "rows_written"}),
    ("prediction", "XGBoost Prediction", {"predictions": "predictions_generated"}),
)

RunIdFilter = Annotated[str | None, Query(pattern=r"^[A-Za-z0-9_-]{1,50}$")]


def _reported_duration(value: object) -> float | None:
    if not isinstance(value, (float, int)) or isinstance(value, bool):
        return None
    try:
        seconds = float(value)
    except OverflowError:
        return None
    return seconds if math.isfinite(seconds) and seconds >= 0 else None


def _stage_view(label: str, report: object, run_id: str | None,
                last_run: str | None, counters: dict[str, str]) -> dict[str, Any]:
    view: dict[str, Any] = {"stage": label, "status": "idle", "lastRun": "",
                            "duration": 0, "outcome": "unreported"}
    if not isinstance(report, dict) or report.get("run_id") != run_id:
        return view
    outcome = report.get("status")
    duration = _reported_duration(report.get("elapsed_seconds"))
    if outcome not in ("success", "failed", "invalid", "partial") or duration is None:
        return view
    if outcome == "success" and report.get("error") not in (None, ""):
        return view
    view.update(status="complete" if outcome == "success" else "error",
                lastRun=last_run or "", duration=duration, outcome=outcome)
    if outcome == "success":
        details = {}
        for name, source in counters.items():
            count = report.get(source)
            if isinstance(count, int) and not isinstance(count, bool) and count >= 0:
                details[name] = count
        view["details"] = details
    return view


@router.get("/status")
def get_pipeline_status(run_id: RunIdFilter = None, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Project stage outcomes from one saved run and its correlated report."""
    query = select(PipelineRun)
    if run_id is None:
        query = query.order_by(PipelineRun.started_at.desc().nulls_last(), PipelineRun.id.desc()).limit(1)
    else:
        query = query.where(PipelineRun.run_id == run_id)
    record = cast(Any, db.execute(query).scalar_one_or_none())
    if record is None and run_id is not None:
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    selected_id = record.run_id if record is not None else None
    last_run = record.started_at.isoformat() if record is not None and record.started_at else None
    target_date = record.target_date.isoformat() if record is not None else None
    recorded_status = record.status if record is not None else "idle"
    report = record.result_json if record is not None else None
    reports: dict[str, Any] = {}
    if (record is not None and record.finished_at is not None
            and recorded_status in ("success", "failed") and isinstance(report, dict)
            and report.get("run_id") == selected_id and report.get("target_date") == target_date
            and report.get("overall_status") == recorded_status
            and isinstance(report.get("stages"), dict)):
        reports = report["stages"]
    stages = [_stage_view(label, reports.get(key), selected_id, last_run, counters)
              for key, label, counters in _STAGE_VIEWS]
    complete = recorded_status == "success" and all(stage["status"] == "complete" for stage in stages)
    if complete or recorded_status in ("idle", "running", "failed"):
        pipeline_status = recorded_status
    else:
        pipeline_status = "unverified"
    stages.append({"stage": "Output & Storage", "status": "complete" if complete else "idle",
                   "lastRun": (last_run or "") if complete else "", "duration": 0,
                   "outcome": "success" if complete else "unreported"})
    return {
        "pipelineStatus": pipeline_status,
        "recordedStatus": recorded_status,
        "runId": selected_id,
        "targetDate": target_date,
        "lastRun": last_run,
        "stages": stages,
    }


@router.get("/logs")
def get_pipeline_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent pipeline log entries from the database."""
    logs = db.execute(
        select(PipelineLog)
        .join(PipelineRun)
        .order_by(PipelineLog.timestamp.desc())
        .limit(limit)
    ).scalars().all()

    if not logs:
        return {"logs": []}

    return {"logs": [
        {
            "timestamp": log.timestamp.isoformat() if log.timestamp else "",
            "stage": log.stage,
            "message": log.message,
            "level": log.level,
        }
        for log in logs
    ]}


@router.post("/run", dependencies=[Depends(verify_pipeline_key)])
def trigger_pipeline(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger a full pipeline run in the background."""
    import uuid

    run_id = f"pipeline_{uuid.uuid4().hex}"

    pipeline_run = PipelineRun(
        run_id=run_id,
        target_date=datetime.utcnow().date(),
        status="running",
    )
    db.add(pipeline_run)
    db.commit()

    background_tasks.add_task(_run_pipeline_background, run_id)

    return {"status": "started", "run_id": run_id, "message": "Pipeline run started in background"}


async def _run_pipeline_background(run_id: str) -> None:
    """Background task wrapper for pipeline execution."""
    from src.pipeline.runner import run_full_pipeline
    from src.database.connection import SessionLocal

    db = SessionLocal()
    query = select(PipelineRun).where(PipelineRun.run_id == run_id)
    try:
        record = cast(Any, db.execute(query).scalar_one_or_none())
        if record is None or record.status != "running":
            return

        target = record.target_date
        result = run_full_pipeline(db, target_date=target, run_id=run_id)
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
    except Exception:
        db.rollback()
        logger.error("Pipeline worker failed for run %s", run_id)
        record = cast(Any, db.execute(query).scalar_one_or_none())
        if record is None or record.status != "running":
            return
        record.status = "failed"
        record.finished_at = datetime.utcnow()
        record.result_json = {
            "run_id": run_id,
            "target_date": record.target_date.isoformat(),
            "overall_status": "failed",
            "error_code": "pipeline_worker_failed",
            "stages": {},
        }
        db.add(PipelineLog(run_id=record.id, stage="system", level="error",
                           message="Pipeline worker failed"))
        db.commit()
    finally:
        db.close()
