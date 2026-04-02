"""AG-03: Calendar Signal Agent.

Computes calendar-based trading signals:
- Holiday decay: e^(-n) where n = trading days from nearest US holiday
- Day-of-week effects: Monday high volatility, Friday low volume
- Earnings proximity: amplified sentiment within 7 days of earnings
- Month seasonality: historical monthly return patterns
"""

import calendar as cal_mod
import math
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.agents.base import BaseAgent
from src.database.models import DimCalendar, DimStock


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Return the nth occurrence of a weekday in a month (1-indexed)."""
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    last_day = date(year, month, cal_mod.monthrange(year, month)[1])
    offset = (last_day.weekday() - weekday) % 7
    return last_day - timedelta(days=offset)


def _easter(year: int) -> date:
    """Easter Sunday via Anonymous Gregorian algorithm."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def _observed(d: date) -> date:
    """Shift weekend holidays to nearest weekday (NYSE convention)."""
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def us_market_holidays(year: int) -> list[date]:
    """NYSE market holidays for a given year, with floating dates computed correctly."""
    return [
        _observed(date(year, 1, 1)),           # New Year's Day
        _nth_weekday(year, 1, 0, 3),           # MLK Day
        _nth_weekday(year, 2, 0, 3),           # Presidents' Day
        _easter(year) - timedelta(days=2),     # Good Friday
        _last_weekday(year, 5, 0),             # Memorial Day
        _observed(date(year, 6, 19)),          # Juneteenth
        _observed(date(year, 7, 4)),           # Independence Day
        _nth_weekday(year, 9, 0, 1),           # Labor Day
        _nth_weekday(year, 11, 3, 4),          # Thanksgiving
        _observed(date(year, 12, 25)),         # Christmas
    ]

# Day-of-week effect coefficients (Monday=0 .. Friday=4)
# Research: Monday tends negative, Friday tends positive
DOW_EFFECTS = {0: -0.15, 1: 0.05, 2: 0.02, 3: 0.08, 4: 0.10}

# Monthly seasonality (avg historical S&P 500 return by month)
MONTH_SEASONALITY = {
    1: 0.012, 2: -0.001, 3: 0.011, 4: 0.015, 5: 0.003,
    6: 0.007, 7: 0.010, 8: -0.005, 9: -0.012, 10: 0.008,
    11: 0.015, 12: 0.013,
}

# Monthly win rate (% of years the month was positive)
MONTH_WIN_RATES = {
    1: 0.58, 2: 0.53, 3: 0.65, 4: 0.70, 5: 0.60,
    6: 0.55, 7: 0.62, 8: 0.55, 9: 0.45, 10: 0.60,
    11: 0.68, 12: 0.72,
}


class CalendarAgent(BaseAgent):
    """Computes calendar-based signals for each ticker on a given date."""

    stage_name = "calendar"

    @property
    def name(self) -> str:
        return "AG-03-Calendar"

    def execute(self, target_date: date | None = None,
                tickers: list[str] | None = None, **kwargs: Any) -> dict[str, Any]:
        target = target_date or date.today()
        from src.constants import TOP_10_TICKERS
        ticker_list = tickers or list(TOP_10_TICKERS)

        results: dict[str, dict[str, Any]] = {}
        for ticker in ticker_list:
            results[ticker] = self._compute_signal(ticker, target)

        return {"target_date": str(target), "signals": results, "tickers_computed": len(results)}

    def _validation_records(self, result: dict[str, Any]) -> list[dict[str, Any]] | None:
        signals = result.get("signals", {})
        target_date = result.get("target_date")
        if not signals or not target_date:
            return None
        records = []
        for ticker, signal in signals.items():
            records.append({"ticker": ticker, "date": target_date, **signal})
        return records

    def _compute_signal(self, ticker: str, target: date) -> dict[str, Any]:
        """Compute calendar signal components for a single ticker/date."""
        holiday_decay = self._holiday_decay(target)
        dow_effect = self._day_of_week_effect(target)
        earnings_prox = self._earnings_proximity(ticker, target)
        month_return = MONTH_SEASONALITY.get(target.month, 0.0)
        month_win = MONTH_WIN_RATES.get(target.month, 0.5)
        trading_dom = self._trading_day_of_month(target)

        # Composite calendar score: weighted combination [-1, 1]
        earnings_factor = 1.0
        if earnings_prox is not None and earnings_prox <= 7:
            earnings_factor = 1.3  # Amplify near earnings

        raw_score = (
            holiday_decay * 0.25
            + dow_effect * 0.20
            + (month_return * 10) * 0.30  # Scale monthly return to ~[-0.12, 0.15]
            + (month_win - 0.5) * 0.25  # Center win rate around 0
        ) * earnings_factor

        calendar_score = max(-1.0, min(1.0, raw_score))

        return {
            "holiday_decay": round(holiday_decay, 4),
            "day_of_week_effect": round(dow_effect, 4),
            "earnings_proximity": earnings_prox,
            "month_avg_return": round(month_return, 4),
            "month_win_rate": round(month_win, 4),
            "trading_day_of_month": trading_dom,
            "calendar_score": round(calendar_score, 4),
        }

    def _holiday_decay(self, target: date) -> float:
        """Compute holiday decay: e^(-n) where n = trading days to nearest holiday."""
        min_distance = 999

        for y in [target.year - 1, target.year, target.year + 1]:
            for holiday in us_market_holidays(y):
                delta = abs((target - holiday).days)
                trading_days = max(1, int(delta * 5 / 7))
                min_distance = min(min_distance, trading_days)

        if min_distance <= 1:
            return -0.3
        return round(-0.3 * math.exp(-(min_distance - 1)), 4)

    def _day_of_week_effect(self, target: date) -> float:
        """Day-of-week effect. Weekend returns 0."""
        dow = target.weekday()
        return DOW_EFFECTS.get(dow, 0.0)

    def _earnings_proximity(self, ticker: str, target: date) -> int | None:
        """Days until next earnings. Returns None if unknown (>30 days)."""
        # In production, this would query an earnings calendar API.
        # For now, approximate with quarterly dates (mid-month of Q end +1)
        q_months = [1, 4, 7, 10]  # Approximate earnings months
        for m in q_months:
            for y in [target.year, target.year + 1]:
                try:
                    earnings_date = date(y, m, 15)
                except ValueError:
                    continue
                delta = (earnings_date - target).days
                if 0 <= delta <= 30:
                    return delta
        return None

    def _trading_day_of_month(self, target: date) -> int:
        """Approximate trading day of month (weekdays only)."""
        count = 0
        d = date(target.year, target.month, 1)
        while d <= target:
            if d.weekday() < 5:
                count += 1
            d += timedelta(days=1)
        return count
