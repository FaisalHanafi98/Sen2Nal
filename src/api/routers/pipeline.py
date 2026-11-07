"""Pipeline monitoring and control endpoints."""

import logging
from datetime import datetime
from typing import Any, cast

from fastapi import APIRouter, Depends, BackgroundTasks, Header, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.config import settings
from src.constants import API_PREFIX
from src.database.connection import get_db
from src.database.models import (
    FactSentiment,
    FactPrice,
    FactPrediction,
    PipelineLog,
    PipelineRun,
    StgNewsRaw,
    StgRedditRaw,
)

logger = logging.getLogger(__name__)


def verify_pipeline_key(x_api_key: str | None = Header(default=None)) -> None:
    """Reject requests without a valid API key when pipeline_api_key is configured."""
    required_key = settings.pipeline_api_key
    if required_key is None:
        return
    if x_api_key != required_key:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")

router = APIRouter(prefix=f"{API_PREFIX}/pipeline", tags=["Pipeline"])


@router.get("/status")
def get_pipeline_status(db: Session = Depends(get_db)):
    """Get pipeline stage statuses — powers the pipeline flow diagram."""
    news_total = db.execute(select(func.count(StgNewsRaw.raw_id))).scalar() or 0
    news_processed = db.execute(
        select(func.count(StgNewsRaw.raw_id)).where(StgNewsRaw.is_processed.is_(True))
    ).scalar() or 0
    reddit_total = db.execute(select(func.count(StgRedditRaw.raw_id))).scalar() or 0
    reddit_processed = db.execute(
        select(func.count(StgRedditRaw.raw_id)).where(StgRedditRaw.is_processed.is_(True))
    ).scalar() or 0
    sentiment_count = db.execute(select(func.count(FactSentiment.sentiment_id))).scalar() or 0
    price_count = db.execute(select(func.count(FactPrice.price_id))).scalar() or 0
    prediction_count = db.execute(select(func.count(FactPrediction.prediction_id))).scalar() or 0

    latest_date = db.execute(
        select(func.max(FactSentiment.created_at))
    ).scalar()

    stages = [
        {
            "stage": "Data Ingestion",
            "status": "complete" if news_total > 0 else "idle",
            "lastRun": str(latest_date) if latest_date else "",
            "duration": 0,
            "details": {"news": news_total, "reddit": reddit_total, "prices": price_count},
        },
        {
            "stage": "FinBERT NLP",
            "status": "complete" if news_processed > 0 else "idle",
            "lastRun": str(latest_date) if latest_date else "",
            "duration": 0,
            "details": {"newsProcessed": news_processed, "redditProcessed": reddit_processed},
        },
        {
            "stage": "Feature Engineering",
            "status": "complete" if sentiment_count > 0 else "idle",
            "lastRun": str(latest_date) if latest_date else "",
            "duration": 0,
            "details": {"sentimentRows": sentiment_count},
        },
        {
            "stage": "XGBoost Prediction",
            "status": "complete" if prediction_count > 0 else "idle",
            "lastRun": str(latest_date) if latest_date else "",
            "duration": 0,
            "details": {"predictions": prediction_count},
        },
        {
            "stage": "Output & Storage",
            "status": "complete" if sentiment_count > 0 else "idle",
            "lastRun": str(latest_date) if latest_date else "",
            "duration": 0,
        },
    ]

    # Pipeline-level status from DB
    latest_run = db.execute(
        select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(1)
    ).scalar_one_or_none()

    pipeline_status = "idle"
    last_run_time = None
    if latest_run:
        latest_run_record = cast(Any, latest_run)
        pipeline_status = latest_run_record.status
        last_run_time = (
            str(latest_run_record.started_at) if latest_run_record.started_at else None
        )

    return {
        "pipelineStatus": pipeline_status,
        "lastRun": last_run_time,
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
