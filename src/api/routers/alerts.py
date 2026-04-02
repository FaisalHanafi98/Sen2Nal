"""Alert endpoints — conflict detection and signal changes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from src.constants import API_PREFIX
from src.database.connection import get_db
from src.database.models import DimStock, FactSentiment

router = APIRouter(prefix=f"{API_PREFIX}/alerts", tags=["Alerts"])


@router.get("")
def get_alerts(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    """Get active alerts — conflicts, strong signals, momentum shifts."""
    alerts = []

    # 1. Conflict alerts (NLP and calendar disagree)
    conflicts = db.execute(
        select(FactSentiment, DimStock)
        .join(DimStock, FactSentiment.stock_id == DimStock.stock_id)
        .where(FactSentiment.conflict_flag == True)
        .order_by(desc(FactSentiment.date_id))
        .limit(10)
    ).all()

    for sent, stock in conflicts:
        alerts.append({
            "type": "conflict",
            "severity": "warning",
            "ticker": stock.ticker,
            "message": f"Signal conflict: {sent.conflict_reason}",
            "score": float(sent.combined_score) if sent.combined_score else 0,
        })

    # 2. Strong buy signals
    strong_buys = db.execute(
        select(FactSentiment, DimStock)
        .join(DimStock, FactSentiment.stock_id == DimStock.stock_id)
        .where(FactSentiment.signal == "STRONG_BUY")
        .order_by(desc(FactSentiment.date_id))
        .limit(5)
    ).all()

    for sent, stock in strong_buys:
        alerts.append({
            "type": "strong_signal",
            "severity": "info",
            "ticker": stock.ticker,
            "message": f"Strong buy signal (score: {float(sent.combined_score):.2f})",
            "score": float(sent.combined_score) if sent.combined_score else 0,
        })

    # 3. Avoid signals
    avoids = db.execute(
        select(FactSentiment, DimStock)
        .join(DimStock, FactSentiment.stock_id == DimStock.stock_id)
        .where(FactSentiment.signal == "AVOID")
        .order_by(desc(FactSentiment.date_id))
        .limit(5)
    ).all()

    for sent, stock in avoids:
        alerts.append({
            "type": "avoid_signal",
            "severity": "error",
            "ticker": stock.ticker,
            "message": f"Avoid signal (score: {float(sent.combined_score):.2f})",
            "score": float(sent.combined_score) if sent.combined_score else 0,
        })

    # 4. Momentum shifts (trend_days flipped sign)
    momentum = db.execute(
        select(FactSentiment, DimStock)
        .join(DimStock, FactSentiment.stock_id == DimStock.stock_id)
        .where(FactSentiment.nlp_trend_days == 1)  # Just turned positive
        .order_by(desc(FactSentiment.date_id))
        .limit(5)
    ).all()

    for sent, stock in momentum:
        alerts.append({
            "type": "momentum_shift",
            "severity": "info",
            "ticker": stock.ticker,
            "message": f"Sentiment momentum turned positive",
            "score": float(sent.nlp_score) if sent.nlp_score else 0,
        })

    return {"alerts": alerts[:limit]}
