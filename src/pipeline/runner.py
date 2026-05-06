"""Pipeline orchestrator — runs all agents in sequence.

Pipeline flow:
  AG-01 Ingestion → AG-02 Sentiment → AG-03 Calendar → AG-04 Features
  → AG-05 Prediction → AG-06 Experiment

Can be triggered via:
- API endpoint: POST /api/v1/pipeline/run
- CLI: python -m src.pipeline.runner
- Scheduler: APScheduler cron job (6 PM ET daily)
"""

import logging
import uuid
from datetime import date
from typing import Any, cast

from sqlalchemy.orm import Session

from src.agents.ingestion import IngestionAgent
from src.agents.sentiment import SentimentAgent
from src.agents.calendar import CalendarAgent
from src.agents.features import FeatureAgent
from src.agents.prediction import PredictionAgent
from src.agents.experiment import ExperimentAgent

logger = logging.getLogger("sen2nal.pipeline")


def run_full_pipeline(
    db: Session,
    target_date: date | None = None,
    tickers: list[str] | None = None,
) -> dict[str, Any]:
    """Execute the complete Sen2Nal pipeline.

    Args:
        db: SQLAlchemy session
        target_date: Date to process (default: today)
        tickers: List of ticker symbols (default: TOP_10)

    Returns:
        Dict with results from each agent stage
    """
    run_id = f"pipeline_{uuid.uuid4().hex[:8]}"
    target = target_date or date.today()

    if tickers:
        from src.constants import validate_tickers
        tickers = validate_tickers(tickers)
        if not tickers:
            return {"run_id": run_id, "target_date": str(target),
                    "overall_status": "failed", "failed_at": "validation",
                    "failed_stages": ["validation"], "stages": {},
                    "error": "No valid tickers after whitelist filtering"}

    logger.info(f"[{run_id}] Starting full pipeline for {target}")

    results: dict[str, Any] = {"run_id": run_id, "target_date": str(target), "stages": {}}

    def _run_stage(name: str, agent_cls: type, **kwargs: Any) -> dict[str, Any]:
        agent = agent_cls(db, run_id)
        result = agent.run(**kwargs)
        results["stages"][name] = result
        return cast(dict[str, Any], result)

    def _halt(failed_stage: str) -> dict[str, Any]:
        results["overall_status"] = "failed"
        results["failed_at"] = failed_stage
        results["failed_stages"] = [failed_stage]
        logger.error(f"[{run_id}] Pipeline halted at {failed_stage}")
        return cast(dict[str, Any], results)

    # Stage 1: Ingestion — upstream data source, must succeed
    ingestion_result = _run_stage("ingestion", IngestionAgent,
                                  target_date=target, tickers=tickers)
    if ingestion_result.get("status") == "failed":
        return _halt("ingestion")

    # Stage 2: Sentiment scoring — processes staging tables from Stage 1
    sentiment_result = _run_stage("sentiment", SentimentAgent)
    if sentiment_result.get("status") == "failed":
        return _halt("sentiment")

    # Stage 3: Calendar signals — independent of ingestion, but must succeed for Stage 4
    cal_result = _run_stage("calendar", CalendarAgent,
                            target_date=target, tickers=tickers)
    if cal_result.get("status") == "failed":
        return _halt("calendar")

    # Stage 4: Feature engineering — combines sentiment + calendar into fact_sentiment
    calendar_signals = cal_result.get("signals", {})
    features_result = _run_stage("features", FeatureAgent,
                                 target_date=target, tickers=tickers,
                                 calendar_signals=calendar_signals)
    if features_result.get("status") == "failed":
        return _halt("features")

    # Stage 5: XGBoost prediction — reads fact_sentiment, writes fact_predictions
    prediction_result = _run_stage("prediction", PredictionAgent,
                                   target_date=target, tickers=tickers)
    if prediction_result.get("status") == "failed":
        return _halt("prediction")

    # Stage 6: Experiment tracking (Monday/Friday only) — non-critical, failure logged but doesn't halt
    _run_stage("experiment", ExperimentAgent, target_date=target)

    # All critical stages passed
    results["overall_status"] = "success"
    results["failed_stages"] = []

    logger.info(f"[{run_id}] Pipeline complete — all stages passed")
    return results


def run_pipeline_async(db: Session, target_date: date | None = None) -> dict[str, Any]:
    """Wrapper for background task execution."""
    return run_full_pipeline(db, target_date)


# =============================================================================
# CLI entry point
# =============================================================================

if __name__ == "__main__":
    import sys
    from datetime import date as date_cls

    from src.config import setup_logging
    from src.database.connection import SessionLocal

    setup_logging()

    target = date_cls.today()
    if len(sys.argv) > 1:
        target = date_cls.fromisoformat(sys.argv[1])

    db = SessionLocal()
    try:
        result = run_full_pipeline(db, target)
        print(f"\nPipeline result: {result['overall_status']}")
        for stage, data in result["stages"].items():
            status = data.get("status", "unknown")
            elapsed = data.get("elapsed_seconds", 0)
            print(f"  {stage}: {status} ({elapsed:.1f}s)")
    finally:
        db.close()
