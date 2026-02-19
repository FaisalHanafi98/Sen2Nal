"""Data contract for Agent 3 (Calendar Pattern) output."""

from datetime import date

from pydantic import Field

from src.contracts.base import StrictContract


class CalendarOutput(StrictContract):
    """Output schema for the Calendar Pattern Agent.

    Temporal features for a specific stock on a specific date.
    Holiday decay uses e^(-n) formula where n = trading days from holiday.
    """

    ticker: str = Field(min_length=1, max_length=10)
    date: date
    holiday_decay: float = Field(ge=0.0, le=1.0)
    day_of_week_effect: float = Field(ge=-1.0, le=1.0)
    earnings_proximity: int | None = Field(default=None, ge=0)
    trading_day_of_month: int = Field(ge=1, le=23)
    calendar_score: float = Field(ge=-1.0, le=1.0)
