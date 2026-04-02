"""Experiment tracking endpoints — AI vs AI comparison."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from src.constants import API_PREFIX, EXPERIMENT_DISCLAIMER
from src.database.connection import get_db
from src.database.models import FactExperiment

router = APIRouter(prefix=f"{API_PREFIX}/experiments", tags=["Experiments"])


@router.get("")
def get_experiments(
    year: int | None = None,
    db: Session = Depends(get_db),
):
    """Get all experiment weeks with results — powers the experiment table and chart."""
    from datetime import date as date_type
    target_year = year or date_type.today().year

    rows = db.execute(
        select(FactExperiment)
        .where(FactExperiment.year == target_year)
        .order_by(FactExperiment.week_number, FactExperiment.method)
    ).scalars().all()

    weeks: dict[int, list] = {}
    for exp in rows:
        if exp.week_number not in weeks:
            weeks[exp.week_number] = []

        stocks = []
        for i in range(1, 4):
            ticker = getattr(exp, f"stock_{i}_ticker")
            entry = getattr(exp, f"stock_{i}_entry")
            exit_p = getattr(exp, f"stock_{i}_exit")
            ret = getattr(exp, f"stock_{i}_return")
            stocks.append({
                "ticker": ticker,
                "entryPrice": float(entry) if entry else None,
                "exitPrice": float(exit_p) if exit_p else None,
                "return": float(ret) if ret else None,
            })

        weeks[exp.week_number].append({
            "weekNumber": exp.week_number,
            "method": exp.method,
            "stocks": stocks,
            "weeklyReturn": float(exp.weekly_return) if exp.weekly_return else None,
            "isWinner": bool(exp.is_winner),
        })

    # Flatten to list for frontend
    result = []
    for week_num in sorted(weeks.keys()):
        result.extend(weeks[week_num])

    return {"experiments": result, "disclaimer": EXPERIMENT_DISCLAIMER}


@router.get("/summary")
def get_experiment_summary(db: Session = Depends(get_db)):
    """Get cumulative performance by method — powers the AI vs AI chart."""
    rows = db.execute(
        select(
            FactExperiment.method,
            func.count(FactExperiment.experiment_id).label("weeks"),
            func.sum(FactExperiment.weekly_return).label("total_return"),
            func.avg(FactExperiment.weekly_return).label("avg_return"),
            func.sum(
                func.cast(FactExperiment.is_winner, type_=func.literal(1).type)
            ).label("wins"),
        )
        .where(FactExperiment.weekly_return.isnot(None))
        .group_by(FactExperiment.method)
        .order_by(desc("total_return"))
    ).all()

    return {
        "methods": [
            {
                "method": r.method,
                "weeks": r.weeks,
                "totalReturn": round(float(r.total_return or 0), 4),
                "avgReturn": round(float(r.avg_return or 0), 4),
                "wins": int(r.wins or 0),
            }
            for r in rows
        ]
    }
