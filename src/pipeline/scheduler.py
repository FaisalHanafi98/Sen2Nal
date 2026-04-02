"""APScheduler-based pipeline scheduler.

Runs the full pipeline daily at 6 PM ET (after market close).
Can be started standalone or integrated with the FastAPI app.
"""

import logging
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import settings

logger = logging.getLogger("sen2nal.scheduler")

_scheduler: BackgroundScheduler | None = None


def _run_scheduled_pipeline():
    """Scheduled job: run the full pipeline for today."""
    from src.database.connection import SessionLocal
    from src.pipeline.runner import run_full_pipeline

    logger.info("Scheduled pipeline run starting...")
    db = SessionLocal()
    try:
        result = run_full_pipeline(db, date.today())
        logger.info(f"Scheduled run complete: {result['overall_status']}")
    except Exception as e:
        logger.error(f"Scheduled pipeline run failed: {e}")
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    """Start the background scheduler."""
    global _scheduler

    if _scheduler and _scheduler.running:
        return _scheduler

    _scheduler = BackgroundScheduler()

    # Parse cron expression from settings (default: "0 6 * * *" = 6 AM UTC)
    cron_parts = settings.pipeline_schedule_cron.split()
    trigger = CronTrigger(
        minute=cron_parts[0] if len(cron_parts) > 0 else "0",
        hour=cron_parts[1] if len(cron_parts) > 1 else "18",
        day=cron_parts[2] if len(cron_parts) > 2 else "*",
        month=cron_parts[3] if len(cron_parts) > 3 else "*",
        day_of_week=cron_parts[4] if len(cron_parts) > 4 else "mon-fri",
    )

    _scheduler.add_job(
        _run_scheduled_pipeline,
        trigger=trigger,
        id="daily_pipeline",
        name="Sen2Nal Daily Pipeline",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info(f"Scheduler started — cron: {settings.pipeline_schedule_cron}")
    return _scheduler


def stop_scheduler():
    """Stop the background scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
