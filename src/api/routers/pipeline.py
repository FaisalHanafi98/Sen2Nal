"""Pipeline monitoring and control endpoints."""

from datetime import datetime
from typing import Any

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
        select(func.count(StgNewsRaw.raw_id)).where(StgNewsRaw.is_processed == True)
    ).scalar() or 0
    reddit_total = db.execute(select(func.count(StgRedditRaw.raw_id))).scalar() or 0
    reddit_processed = db.execute(
        select(func.count(StgRedditRaw.raw_id)).where(StgRedditRaw.is_processed == True)
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
        pipeline_status = latest_run.status
        last_run_time = str(latest_run.started_at) if latest_run.started_at else None

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
    from src.pipeline.runner import run_full_pipeline
    import uuid

    run_id = f"pipeline_{uuid.uuid4().hex[:8]}"

    pipeline_run = PipelineRun(
        run_id=run_id,
        target_date=datetime.utcnow().date(),
        status="running",
    )
    db.add(pipeline_run)
    db.commit()

    background_tasks.add_task(_run_pipeline_background, run_id)

    return {"status": "started", "run_id": run_id, "message": "Pipeline run started in background"}


async def _run_pipeline_background(run_id: str):
    """Background task wrapper for pipeline execution."""
    from src.pipeline.runner import run_full_pipeline
    from src.database.connection import SessionLocal

    db = SessionLocal()
    try:
        result = run_full_pipeline(db)

        # Update pipeline run record
        pipeline_run = db.execute(
            select(PipelineRun).where(PipelineRun.run_id == run_id)
        ).scalar_one_or_none()

        if pipeline_run:
            pipeline_run.status = result.get("overall_status", "unknown")
            pipeline_run.finished_at = datetime.utcnow()
            pipeline_run.result_json = result

            # Write stage results as log entries
            for stage_name, stage_data in result.get("stages", {}).items():
                status = stage_data.get("status", "unknown")
                elapsed = stage_data.get("elapsed_seconds", 0)
                level = "success" if status == "success" else "error"
                db.add(PipelineLog(
                    run_id=pipeline_run.id,
                    stage=stage_name,
                    level=level,
                    message=f"{stage_name} {status} ({elapsed:.1f}s)",
                ))

            db.commit()
    except Exception as e:
        pipeline_run = db.execute(
            select(PipelineRun).where(PipelineRun.run_id == run_id)
        ).scalar_one_or_none()
        if pipeline_run:
            pipeline_run.status = "failed"
            pipeline_run.finished_at = datetime.utcnow()
            pipeline_run.result_json = {"error": str(e)}
            db.add(PipelineLog(
                run_id=pipeline_run.id,
                stage="system",
                level="error",
                message=f"Pipeline crashed: {e}",
            ))
            db.commit()
    finally:
        db.close()
