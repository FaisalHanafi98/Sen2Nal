"""Tests for the calendar seed script.

Verifies US and Malaysian holiday computation and calendar row generation.
"""

from datetime import date


from scripts.seed_calendar import (
    _malaysian_public_holidays,
    _us_market_holidays,
    build_calendar_rows,
)


# -- US holidays -------------------------------------------------------------

class TestUSHolidays:

    def test_returns_10_holidays(self):
        holidays = _us_market_holidays(2026)
        assert len(holidays) == 10

    def test_new_years_day(self):
        holidays = _us_market_holidays(2026)
        assert date(2026, 1, 1) in holidays

    def test_christmas_observed(self):
        holidays = _us_market_holidays(2026)
        assert date(2026, 12, 25) in holidays

    def test_thanksgiving_is_thursday(self):
        holidays = _us_market_holidays(2026)
        thanksgiving_dates = [d for d, n in holidays.items() if "Thanksgiving" in n]
        assert len(thanksgiving_dates) == 1
        assert thanksgiving_dates[0].weekday() == 3  # Thursday


# -- Malaysian holidays ------------------------------------------------------

class TestMalaysianHolidays:

    def test_2026_has_holidays(self):
        holidays = _malaysian_public_holidays(2026)
        assert len(holidays) >= 15  # Fixed + Islamic

    def test_merdeka_day(self):
        holidays = _malaysian_public_holidays(2026)
        assert date(2026, 8, 31) in holidays
        assert "Merdeka" in holidays[date(2026, 8, 31)]

    def test_hari_raya_aidilfitri_2026(self):
        holidays = _malaysian_public_holidays(2026)
        assert date(2026, 3, 20) in holidays
        assert "Hari Raya Aidilfitri" in holidays[date(2026, 3, 20)]

    def test_chinese_new_year_2026(self):
        holidays = _malaysian_public_holidays(2026)
        assert date(2026, 2, 17) in holidays
        assert "Chinese New Year" in holidays[date(2026, 2, 17)]

    def test_deepavali_2026(self):
        holidays = _malaysian_public_holidays(2026)
        assert date(2026, 11, 8) in holidays
        assert "Deepavali" in holidays[date(2026, 11, 8)]

    def test_malaysia_day(self):
        holidays = _malaysian_public_holidays(2026)
        assert date(2026, 9, 16) in holidays
        assert "Malaysia Day" in holidays[date(2026, 9, 16)]

    def test_unknown_year_returns_fixed_only(self):
        holidays = _malaysian_public_holidays(2030)
        # Fixed holidays should still be present
        assert date(2030, 8, 31) in holidays
        assert date(2030, 9, 16) in holidays
        # Islamic holidays not available for 2030
        assert len(holidays) == 7  # Only fixed-date holidays


# -- Calendar row generation -------------------------------------------------

class TestBuildCalendarRows:

    def test_row_count_matches_date_range(self):
        rows = build_calendar_rows(date(2026, 1, 1), date(2026, 1, 31))
        assert len(rows) == 31

    def test_weekends_not_trading(self):
        rows = build_calendar_rows(date(2026, 3, 21), date(2026, 3, 22))
        for r in rows:
            assert r["is_trading_day"] is False
            assert r["is_weekend"] is True

    def test_us_holiday_not_trading(self):
        # July 4, 2026 is Saturday -> observed July 3 (Friday)
        rows = build_calendar_rows(date(2026, 7, 3), date(2026, 7, 3))
        assert rows[0]["is_us_holiday"] is True
        assert rows[0]["is_trading_day"] is False

    def test_malaysian_holiday_recorded_in_name(self):
        rows = build_calendar_rows(date(2026, 3, 20), date(2026, 3, 20))
        assert "Hari Raya Aidilfitri" in rows[0]["holiday_name"]

    def test_trading_day_of_month_computed(self):
        rows = build_calendar_rows(date(2026, 3, 1), date(2026, 3, 31))
        trading_rows = [r for r in rows if r["is_trading_day"]]
        assert all(r["trading_day_of_month"] is not None for r in trading_rows)
        # First trading day should be 1
        assert trading_rows[0]["trading_day_of_month"] == 1

    def test_non_trading_day_has_null_trading_day_of_month(self):
        rows = build_calendar_rows(date(2026, 3, 21), date(2026, 3, 21))
        assert rows[0]["trading_day_of_month"] is None

    def test_row_has_all_required_fields(self):
        rows = build_calendar_rows(date(2026, 4, 1), date(2026, 4, 1))
        r = rows[0]
        required = [
            "date", "day_of_week", "day_of_week_name", "day_of_month",
            "week_of_year", "month", "month_name", "quarter", "year",
            "is_weekend", "is_trading_day", "is_month_start", "is_month_end",
            "is_quarter_start", "is_quarter_end", "is_year_start", "is_year_end",
            "is_us_holiday", "holiday_name", "trading_days_in_month",
            "trading_day_of_month",
        ]
        for field in required:
            assert field in r, f"Missing field: {field}"
