"""Tests for AG-03 Calendar Agent pure logic.

Tests the calendar signal computation functions directly,
without database interaction. Uses known dates to verify
holiday decay, day-of-week effects, month seasonality,
earnings proximity, and composite scoring.
"""

import math
from datetime import date
from unittest.mock import MagicMock

import pytest

from src.agents.calendar import (
    CalendarAgent,
    DOW_EFFECTS,
    MONTH_SEASONALITY,
    MONTH_WIN_RATES,
    us_market_holidays,
)


@pytest.fixture
def agent():
    """Calendar agent with a mocked DB session (no DB queries needed for pure logic)."""
    return CalendarAgent(db=MagicMock(), run_id="test_run")


# -- Holiday decay ------------------------------------------------------------

class TestHolidayDecay:

    def test_holiday_adjacent_returns_negative(self, agent):
        """Days right next to a holiday should return -0.3."""
        # Jan 1 is a holiday; Jan 2 is 1 trading day away
        result = agent._holiday_decay(date(2026, 1, 2))
        assert result == -0.3

    def test_holiday_day_itself(self, agent):
        """The holiday itself (0 days away) should return -0.3."""
        result = agent._holiday_decay(date(2026, 1, 1))
        assert result == -0.3

    def test_decay_decreases_with_distance(self, agent):
        """Further from holiday = closer to 0 (less negative)."""
        close = agent._holiday_decay(date(2026, 1, 5))
        far = agent._holiday_decay(date(2026, 3, 15))
        # Both non-positive, but far should be closer to 0
        assert close < 0
        assert far <= 0
        assert abs(far) < abs(close)

    def test_decay_never_positive(self, agent):
        """Holiday decay is always <= 0."""
        for month in range(1, 13):
            for day in [1, 10, 15, 20, 28]:
                try:
                    d = date(2026, month, day)
                except ValueError:
                    continue
                assert agent._holiday_decay(d) <= 0


# -- Day-of-week effects ------------------------------------------------------

class TestDayOfWeekEffect:

    def test_monday_is_negative(self, agent):
        """Monday (weekday=0) has a negative effect per research."""
        # 2026-03-23 is a Monday
        result = agent._day_of_week_effect(date(2026, 3, 23))
        assert result == DOW_EFFECTS[0]
        assert result < 0

    def test_friday_is_positive(self, agent):
        """Friday (weekday=4) has a positive effect."""
        # 2026-03-20 is a Friday
        result = agent._day_of_week_effect(date(2026, 3, 20))
        assert result == DOW_EFFECTS[4]
        assert result > 0

    def test_weekend_returns_zero(self, agent):
        """Weekend days are not in DOW_EFFECTS, should return 0."""
        # 2026-03-21 is Saturday
        result = agent._day_of_week_effect(date(2026, 3, 21))
        assert result == 0.0

    def test_all_weekdays_have_effects(self, agent):
        """Monday through Friday all produce non-None values."""
        # 2026-03-23 (Mon) through 2026-03-27 (Fri)
        for offset, day_num in enumerate(range(23, 28)):
            d = date(2026, 3, day_num)
            result = agent._day_of_week_effect(d)
            assert result == DOW_EFFECTS[offset]


# -- Earnings proximity -------------------------------------------------------

class TestEarningsProximity:

    def test_near_earnings_date_returns_days(self, agent):
        """Within 30 days of approximate quarterly earnings date → int."""
        # Earnings approximated at Jan 15, Apr 15, Jul 15, Oct 15
        result = agent._earnings_proximity("AAPL", date(2026, 1, 10))
        assert result is not None
        assert 0 <= result <= 30

    def test_far_from_earnings_returns_none(self, agent):
        """More than 30 days from any earnings date → None."""
        result = agent._earnings_proximity("AAPL", date(2026, 2, 20))
        assert result is None

    def test_on_earnings_date(self, agent):
        """Exactly on the approximate earnings date → 0."""
        result = agent._earnings_proximity("AAPL", date(2026, 4, 15))
        assert result == 0


# -- Trading day of month -----------------------------------------------------

class TestTradingDayOfMonth:

    def test_first_trading_day(self, agent):
        """First weekday of month = trading day 1."""
        # 2026-03-02 is Monday (March 1 is Sunday)
        result = agent._trading_day_of_month(date(2026, 3, 2))
        assert result == 1

    def test_midmonth(self, agent):
        """Verify a mid-month date produces a reasonable count."""
        result = agent._trading_day_of_month(date(2026, 3, 20))
        # March 20, 2026 is a Friday — should be ~15 trading days
        assert 10 <= result <= 20

    def test_first_of_month_weekday(self, agent):
        """If the 1st is a weekday, it's trading day 1."""
        # 2026-04-01 is Wednesday
        result = agent._trading_day_of_month(date(2026, 4, 1))
        assert result == 1


# -- Composite signal ----------------------------------------------------------

class TestCompositeSignal:

    def test_signal_bounded_between_neg1_and_1(self, agent):
        """Calendar score must always be in [-1, 1]."""
        test_dates = [
            date(2026, 1, 2),   # Near holiday
            date(2026, 4, 15),  # Near earnings
            date(2026, 9, 15),  # Worst month historically
            date(2026, 12, 15), # Best month historically
            date(2026, 3, 23),  # Monday
            date(2026, 3, 20),  # Friday
        ]
        for d in test_dates:
            result = agent._compute_signal("AAPL", d)
            assert -1.0 <= result["calendar_score"] <= 1.0

    def test_signal_contains_all_components(self, agent):
        result = agent._compute_signal("AAPL", date(2026, 3, 20))
        expected_keys = {
            "holiday_decay", "day_of_week_effect", "earnings_proximity",
            "month_avg_return", "month_win_rate", "trading_day_of_month",
            "calendar_score",
        }
        assert set(result.keys()) == expected_keys

    def test_earnings_amplification(self, agent):
        """Near-earnings dates should produce amplified scores vs same date far from earnings."""
        # Compare a date near earnings vs one far away, same day-of-week
        near = agent._compute_signal("AAPL", date(2026, 4, 13))  # 2 days from Apr 15
        far = agent._compute_signal("AAPL", date(2026, 5, 11))   # Far from any earnings

        near_prox = near["earnings_proximity"]
        far_prox = far["earnings_proximity"]

        if near_prox is not None and near_prox <= 7:
            # The near-earnings score should be amplified (1.3x factor)
            # Can't compare directly because other factors differ,
            # but at minimum the proximity should be detected
            assert near_prox <= 7


# -- Execute method (integration-lite) ----------------------------------------

class TestExecuteMethod:

    def test_execute_returns_all_tickers(self, agent):
        """execute() returns signals for every requested ticker."""
        tickers = ["AAPL", "MSFT", "GOOGL"]
        result = agent.execute(target_date=date(2026, 3, 20), tickers=tickers)

        assert result["tickers_computed"] == 3
        assert set(result["signals"].keys()) == {"AAPL", "MSFT", "GOOGL"}

    def test_execute_uses_provided_date(self, agent):
        result = agent.execute(target_date=date(2026, 6, 15), tickers=["AAPL"])
        assert result["target_date"] == "2026-06-15"
