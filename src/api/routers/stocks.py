"""Stock and signal endpoints for the React frontend."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import Session

from src.constants import ALLOWED_TICKERS, API_PREFIX, FOOTER_DISCLAIMER
from src.database.connection import get_db
from src.database.models import (
    DimCalendar,
    DimFearGreed,
    DimStock,
    FactPrice,
    FactSentiment,
)

router = APIRouter(prefix=f"{API_PREFIX}/stocks", tags=["Stocks"])

# Cache TTL: stock data refreshes once per pipeline run (~daily)
CACHE_MAX_AGE = 300  # 5 minutes


@router.get("")
def get_stocks(
    response: Response,
    limit: int = Query(10, ge=1, le=50),
    sector: Optional[str] = None,
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = f"public, max-age={CACHE_MAX_AGE}"
    """Get stocks with latest sentiment signals — powers the main dashboard table."""
    # Subquery: latest date_id with sentiment data
    latest_date_sub = select(func.max(FactSentiment.date_id)).scalar_subquery()

    query = (
        select(DimStock, FactSentiment, FactPrice)
        .join(FactSentiment, DimStock.stock_id == FactSentiment.stock_id)
        .outerjoin(
            FactPrice,
            and_(
                DimStock.stock_id == FactPrice.stock_id,
                FactSentiment.date_id == FactPrice.date_id,
            ),
        )
        .where(FactSentiment.date_id == latest_date_sub)
    )

    if sector:
        query = query.where(DimStock.sector == sector)

    query = query.order_by(desc(FactSentiment.combined_score)).limit(limit)
    rows = db.execute(query).all()

    stocks = []
    for stock, sent, price in rows:
        stocks.append({
            "ticker": stock.ticker,
            "companyName": stock.company_name,
            "sector": stock.sector,
            "marketCap": stock.market_cap,
            "sp500Rank": stock.sp500_rank,
            "nlpScore": float(sent.nlp_score) if sent.nlp_score else 0,
            "calendarScore": float(sent.calendar_score) if sent.calendar_score else 0,
            "combinedScore": float(sent.combined_score) if sent.combined_score else 0,
            "signal": sent.signal,
            "confidence": float(sent.confidence) if sent.confidence else 0,
            "conflictFlag": bool(sent.conflict_flag),
            "newsCount": sent.news_count or 0,
            "redditCount": sent.reddit_count or 0,
            "change24h": float(price.daily_return) if price and price.daily_return else 0,
        })

    return {"stocks": stocks, "disclaimer": FOOTER_DISCLAIMER}


@router.get("/history")
def get_sentiment_history(
    ticker: str = Query(..., min_length=1, max_length=10),
    days: int = Query(30, ge=1, le=180),
    db: Session = Depends(get_db),
):
    """Get sentiment time series for a ticker — powers the timeline chart."""
    ticker = ticker.upper()
    if ticker not in ALLOWED_TICKERS:
        return {"history": [], "error": f"Ticker {ticker} not in allowed list"}

    stock_id = db.execute(
        select(DimStock.stock_id).where(DimStock.ticker == ticker)
    ).scalar()
    if not stock_id:
        return {"history": [], "error": f"Ticker {ticker} not found"}

    rows = db.execute(
        select(FactSentiment, DimCalendar)
        .join(DimCalendar, FactSentiment.date_id == DimCalendar.date_id)
        .where(FactSentiment.stock_id == stock_id)
        .order_by(desc(DimCalendar.date))
        .limit(days)
    ).all()

    history = [
        {
            "date": str(cal.date),
            "nlpScore": float(sent.nlp_score) if sent.nlp_score else 0,
            "calendarScore": float(sent.calendar_score) if sent.calendar_score else 0,
            "combinedScore": float(sent.combined_score) if sent.combined_score else 0,
            "newsCount": sent.news_count or 0,
        }
        for sent, cal in reversed(rows)
    ]

    return {"ticker": ticker.upper(), "history": history}


@router.get("/fear-greed")
def get_fear_greed(db: Session = Depends(get_db)):
    """Get latest Fear & Greed index — powers the gauge widget."""
    row = db.execute(
        select(DimFearGreed).order_by(desc(DimFearGreed.date)).limit(1)
    ).scalar()

    if not row:
        return {"score": 50, "classification": "Neutral", "prevScore": 50, "change": 0}

    return {
        "score": row.score,
        "classification": row.classification,
        "prevScore": row.prev_score or row.score,
        "change": row.score_change or 0,
    }


@router.get("/sectors")
def get_sectors(db: Session = Depends(get_db)):
    """Get sector-level sentiment aggregation."""
    latest_date_sub = select(func.max(FactSentiment.date_id)).scalar_subquery()

    rows = db.execute(
        select(
            DimStock.sector,
            func.avg(FactSentiment.combined_score).label("avg_score"),
            func.count(FactSentiment.sentiment_id).label("stock_count"),
            func.avg(FactSentiment.nlp_score).label("avg_nlp"),
            func.avg(FactSentiment.calendar_score).label("avg_calendar"),
        )
        .join(FactSentiment, DimStock.stock_id == FactSentiment.stock_id)
        .where(FactSentiment.date_id == latest_date_sub)
        .group_by(DimStock.sector)
        .order_by(desc("avg_score"))
    ).all()

    return {
        "sectors": [
            {
                "sector": r.sector,
                "avgScore": round(float(r.avg_score), 3) if r.avg_score else 0,
                "stockCount": r.stock_count,
                "avgNlp": round(float(r.avg_nlp), 3) if r.avg_nlp else 0,
                "avgCalendar": round(float(r.avg_calendar), 3) if r.avg_calendar else 0,
            }
            for r in rows
        ]
    }
