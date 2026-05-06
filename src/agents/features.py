"""AG-04: Feature Engineering Agent.

Combines NLP sentiment, calendar signals, and market data into feature vectors.
- Aggregates sentiment from staging tables per ticker
- Merges with calendar signal output
- Adds price-derived features (momentum, volatility)
- Z-score normalizes features
- Writes complete fact_sentiment rows
"""

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import select

from src.agents.base import BaseAgent
from src.agents.calendar import CalendarAgent
from src.agents.sentiment import aggregate_ticker_sentiment
from src.config import settings
from src.constants import SIGNAL_THRESHOLDS, SignalType
from src.database.models import (
    DimCalendar,
    DimStock,
    FactSentiment,
    StgNewsRaw,
    StgRedditRaw,
)


class FeatureAgent(BaseAgent):
    """Builds feature vectors and writes fact_sentiment rows."""

    stage_name = "features"

    @property
    def name(self) -> str:
        return "AG-04-Features"

    def execute(self, target_date: date | None = None,
                tickers: list[str] | None = None,
                calendar_signals: dict[str, dict] | None = None,
                **kwargs: Any) -> dict[str, Any]:
        target = target_date or date.today()
        from src.constants import TOP_10_TICKERS
        ticker_list = tickers or list(TOP_10_TICKERS)

        # If calendar signals weren't passed in, compute them
        if not calendar_signals:
            cal_agent = CalendarAgent(self.db, self.run_id)
            cal_result = cal_agent.execute(target_date=target, tickers=ticker_list)
            calendar_signals = cal_result.get("signals", {})

        date_id = self._get_date_id(target)
        if not date_id:
            return {"error": f"No calendar entry for {target}", "rows_written": 0}

        rows_written = 0
        for ticker in ticker_list:
            try:
                written = self._build_features(ticker, target, date_id,
                                               calendar_signals.get(ticker, {}))
                if written:
                    rows_written += 1
            except Exception as e:
                self.logger.warning(f"Feature build failed for {ticker}: {e}")

        self.db.commit()
        return {"target_date": str(target), "rows_written": rows_written}

    def _build_features(self, ticker: str, target: date, date_id: int,
                        cal_signal: dict) -> bool:
        """Build feature vector for one ticker and write to fact_sentiment."""
        stock_id = self.db.execute(
            select(DimStock.stock_id).where(DimStock.ticker == ticker)
        ).scalar()
        if not stock_id:
            return False

        # Check if already computed
        existing = self.db.execute(
            select(FactSentiment.sentiment_id).where(
                FactSentiment.stock_id == stock_id,
                FactSentiment.date_id == date_id,
            )
        ).scalar()
        if existing:
            return False

        # Aggregate NLP sentiment from staging
        nlp = self._aggregate_nlp(ticker, target)

        # Get previous day's sentiment for momentum
        prev = self._get_previous_sentiment(stock_id, date_id)

        # Calendar components
        calendar_score = cal_signal.get("calendar_score", 0.0)
        month_avg_return = cal_signal.get("month_avg_return", 0.0)
        month_win_rate = cal_signal.get("month_win_rate", 0.5)
        days_to_earnings = cal_signal.get("earnings_proximity")

        # Combined score: weighted blend of NLP + calendar, normalized to [0, 1]
        nlp_weight = float(settings.nlp_weight)
        cal_weight = float(settings.calendar_weight)
        raw_combined = nlp["nlp_score"] * nlp_weight + calendar_score * cal_weight
        combined_score = max(0.0, min(1.0, (raw_combined + 1.0) / 2.0))  # Map [-1,1] → [0,1]

        # Signal classification
        signal = _classify_signal(combined_score)

        # Confidence: blend of NLP confidence and data availability
        confidence = nlp["nlp_confidence"] * 0.7 + min(1.0, (nlp["news_count"] + nlp["reddit_count"]) / 15) * 0.3

        # Conflict detection
        conflict_flag = False
        conflict_reason = None
        nlp_direction = 1 if nlp["nlp_score"] > 0.1 else (-1 if nlp["nlp_score"] < -0.1 else 0)
        cal_direction = 1 if calendar_score > 0.1 else (-1 if calendar_score < -0.1 else 0)
        if nlp_direction != 0 and cal_direction != 0 and nlp_direction != cal_direction:
            conflict_flag = True
            conflict_reason = f"NLP={nlp['nlp_score']:.2f} vs Calendar={calendar_score:.2f}"

        # Momentum
        nlp_score_prev = prev.get("nlp_score") if prev else None
        nlp_momentum = None
        nlp_trend_days = 0
        if nlp_score_prev is not None:
            nlp_momentum = round(nlp["nlp_score"] - float(nlp_score_prev), 4)
            prev_trend = prev.get("nlp_trend_days", 0) if prev else 0
            if nlp_momentum > 0:
                nlp_trend_days = max(0, prev_trend) + 1
            elif nlp_momentum < 0:
                nlp_trend_days = min(0, prev_trend) - 1

        self.db.add(FactSentiment(
            stock_id=stock_id,
            date_id=date_id,
            nlp_score=round(nlp["nlp_score"], 4),
            nlp_score_prev=nlp_score_prev,
            nlp_momentum=nlp_momentum,
            nlp_trend_days=nlp_trend_days,
            nlp_confidence=round(nlp["nlp_confidence"], 4),
            news_score=round(nlp["news_score"], 4) if nlp["news_score"] else None,
            news_count=nlp["news_count"],
            reddit_score=round(nlp["reddit_score"], 4) if nlp["reddit_score"] else None,
            reddit_count=nlp["reddit_count"],
            calendar_score=round(calendar_score, 4),
            month_avg_return=round(month_avg_return, 4),
            month_win_rate=round(month_win_rate, 4),
            days_to_earnings=days_to_earnings,
            combined_score=round(combined_score, 4),
            signal=signal,
            confidence=round(confidence, 4),
            conflict_flag=conflict_flag,
            conflict_reason=conflict_reason,
            pipeline_run_id=self.run_id,
        ))
        self.db.flush()
        return True

    def _aggregate_nlp(self, ticker: str, target: date) -> dict[str, Any]:
        """Pull scored news/reddit for ticker and aggregate."""
        lookback = target - timedelta(days=3)

        news = self.db.execute(
            select(StgNewsRaw).where(
                StgNewsRaw.is_processed.is_(True),
                StgNewsRaw.tickers_mentioned.contains([ticker]),
                StgNewsRaw.published_at >= lookback,
            )
        ).scalars().all()

        reddit = self.db.execute(
            select(StgRedditRaw).where(
                StgRedditRaw.is_processed.is_(True),
                StgRedditRaw.tickers_mentioned.contains([ticker]),
                StgRedditRaw.created_utc >= lookback,
            )
        ).scalars().all()

        return aggregate_ticker_sentiment(
            list(news),
            list(reddit),
            datetime.combine(target, datetime.min.time()),
        )

    def _get_previous_sentiment(self, stock_id: int, date_id: int) -> dict | None:
        """Get previous day's sentiment for momentum calculation."""
        row = self.db.execute(
            select(FactSentiment).where(
                FactSentiment.stock_id == stock_id,
                FactSentiment.date_id < date_id,
            ).order_by(FactSentiment.date_id.desc()).limit(1)
        ).scalar()
        if not row:
            return None
        return {
            "nlp_score": row.nlp_score,
            "nlp_trend_days": row.nlp_trend_days,
        }

    def _get_date_id(self, target: date) -> int | None:
        return self.db.execute(
            select(DimCalendar.date_id).where(DimCalendar.date == target)
        ).scalar()


def _classify_signal(combined_score: float) -> str:
    """Map combined score [0, 1] to signal label."""
    if combined_score >= SIGNAL_THRESHOLDS[SignalType.STRONG_BUY]:
        return "STRONG_BUY"
    elif combined_score >= SIGNAL_THRESHOLDS[SignalType.BUY]:
        return "BUY"
    elif combined_score >= SIGNAL_THRESHOLDS[SignalType.HOLD]:
        return "HOLD"
    return "AVOID"
