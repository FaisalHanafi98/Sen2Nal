"""Seed dim_calendar with trading day data.

Generates calendar rows for a date range, marking weekends, US market
holidays, Malaysian public holidays, and computing trading-day-of-month positions.

Sen2Nal covers both Bursa Malaysia and S&P 500 top 10, so both markets'
holidays are tracked. Malaysian holidays affect Bursa trading days.

Usage:
    poetry run python scripts/seed_calendar.py              # 2024-01-01 to 2027-12-31
    poetry run python scripts/seed_calendar.py 2026 2026    # single year
"""

import calendar
import sys
from datetime import date, timedelta

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _us_market_holidays(year: int) -> dict[date, str]:
    """Return US stock market holidays for a given year.

    Handles fixed and floating holidays per NYSE calendar.
    """
    holidays: dict[date, str] = {}

    # New Year's Day (Jan 1, observed Fri if Sat, Mon if Sun)
    holidays[_observed(date(year, 1, 1))] = "New Year's Day"

    # MLK Day (3rd Monday of January)
    holidays[_nth_weekday(year, 1, 0, 3)] = "Martin Luther King Jr. Day"

    # Presidents' Day (3rd Monday of February)
    holidays[_nth_weekday(year, 2, 0, 3)] = "Presidents' Day"

    # Good Friday (2 days before Easter Sunday)
    holidays[_easter(year) - timedelta(days=2)] = "Good Friday"

    # Memorial Day (last Monday of May)
    holidays[_last_weekday(year, 5, 0)] = "Memorial Day"

    # Juneteenth (Jun 19, observed)
    holidays[_observed(date(year, 6, 19))] = "Juneteenth"

    # Independence Day (Jul 4, observed)
    holidays[_observed(date(year, 7, 4))] = "Independence Day"

    # Labor Day (1st Monday of September)
    holidays[_nth_weekday(year, 9, 0, 1)] = "Labor Day"

    # Thanksgiving (4th Thursday of November)
    holidays[_nth_weekday(year, 11, 3, 4)] = "Thanksgiving Day"

    # Christmas Day (Dec 25, observed)
    holidays[_observed(date(year, 12, 25))] = "Christmas Day"

    return holidays


def _observed(d: date) -> date:
    """Shift weekend holidays to the nearest weekday (NYSE convention)."""
    if d.weekday() == 5:  # Saturday → Friday
        return d - timedelta(days=1)
    if d.weekday() == 6:  # Sunday → Monday
        return d + timedelta(days=1)
    return d


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Return the nth occurrence of a weekday in a month (1-indexed)."""
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    """Return the last occurrence of a weekday in a month."""
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    offset = (last_day.weekday() - weekday) % 7
    return last_day - timedelta(days=offset)


def _easter(year: int) -> date:
    """Compute Easter Sunday using the Anonymous Gregorian algorithm."""
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


def _malaysian_public_holidays(year: int) -> dict[date, str]:
    """Return Malaysian public holidays for a given year.

    Includes both fixed-date and Islamic calendar holidays.
    Islamic holidays are approximate (shift ~11 days/year) and are
    hardcoded for 2024-2027. For years outside this range, fixed-date
    holidays are still returned.
    """
    holidays: dict[date, str] = {}

    # --- Fixed-date holidays ---
    holidays[date(year, 1, 1)] = "New Year's Day (MY)"
    holidays[date(year, 2, 1)] = "Federal Territory Day (MY)"
    holidays[date(year, 5, 1)] = "Labour Day (MY)"
    holidays[date(year, 6, 3)] = "Yang di-Pertuan Agong Birthday (MY)"
    holidays[date(year, 8, 31)] = "Merdeka Day (MY)"
    holidays[date(year, 9, 16)] = "Malaysia Day (MY)"
    holidays[date(year, 12, 25)] = "Christmas Day (MY)"

    # --- Islamic calendar holidays (approximate, varies by year) ---
    # These dates shift ~11 days earlier each Gregorian year.
    # Sourced from Malaysian government gazette for 2024-2027.
    islamic_holidays: dict[int, list[tuple[date, str]]] = {
        2024: [
            (date(2024, 2, 10), "Chinese New Year Day 1"),
            (date(2024, 2, 11), "Chinese New Year Day 2"),
            (date(2024, 3, 28), "Nuzul Al-Quran"),
            (date(2024, 3, 29), "Nuzul Al-Quran (replacement)"),
            (date(2024, 4, 10), "Hari Raya Aidilfitri Day 1"),
            (date(2024, 4, 11), "Hari Raya Aidilfitri Day 2"),
            (date(2024, 5, 22), "Vesak Day"),
            (date(2024, 6, 17), "Hari Raya Haji Day 1"),
            (date(2024, 6, 18), "Hari Raya Haji Day 2"),
            (date(2024, 7, 8), "Awal Muharram"),
            (date(2024, 9, 16), "Maulidur Rasul"),
            (date(2024, 11, 1), "Deepavali"),
        ],
        2025: [
            (date(2025, 1, 29), "Chinese New Year Day 1"),
            (date(2025, 1, 30), "Chinese New Year Day 2"),
            (date(2025, 3, 17), "Nuzul Al-Quran"),
            (date(2025, 3, 30), "Hari Raya Aidilfitri Day 1"),
            (date(2025, 3, 31), "Hari Raya Aidilfitri Day 2"),
            (date(2025, 5, 12), "Vesak Day"),
            (date(2025, 6, 6), "Hari Raya Haji Day 1"),
            (date(2025, 6, 7), "Hari Raya Haji Day 2"),
            (date(2025, 6, 27), "Awal Muharram"),
            (date(2025, 9, 5), "Maulidur Rasul"),
            (date(2025, 10, 20), "Deepavali"),
        ],
        2026: [
            (date(2026, 2, 17), "Chinese New Year Day 1"),
            (date(2026, 2, 18), "Chinese New Year Day 2"),
            (date(2026, 3, 6), "Nuzul Al-Quran"),
            (date(2026, 3, 20), "Hari Raya Aidilfitri Day 1"),
            (date(2026, 3, 21), "Hari Raya Aidilfitri Day 2"),
            (date(2026, 5, 1), "Vesak Day"),
            (date(2026, 5, 27), "Hari Raya Haji Day 1"),
            (date(2026, 5, 28), "Hari Raya Haji Day 2"),
            (date(2026, 6, 17), "Awal Muharram"),
            (date(2026, 8, 26), "Maulidur Rasul"),
            (date(2026, 11, 8), "Deepavali"),
        ],
        2027: [
            (date(2027, 2, 6), "Chinese New Year Day 1"),
            (date(2027, 2, 7), "Chinese New Year Day 2"),
            (date(2027, 2, 24), "Nuzul Al-Quran"),
            (date(2027, 3, 10), "Hari Raya Aidilfitri Day 1"),
            (date(2027, 3, 11), "Hari Raya Aidilfitri Day 2"),
            (date(2027, 5, 20), "Vesak Day"),
            (date(2027, 5, 17), "Hari Raya Haji Day 1"),
            (date(2027, 5, 18), "Hari Raya Haji Day 2"),
            (date(2027, 6, 7), "Awal Muharram"),
            (date(2027, 8, 16), "Maulidur Rasul"),
            (date(2027, 10, 29), "Deepavali"),
        ],
    }

    if year in islamic_holidays:
        for d, name in islamic_holidays[year]:
            holidays[d] = name

    return holidays


def build_calendar_rows(start: date, end: date) -> list[dict]:
    """Generate DimCalendar-compatible dicts for a date range."""
    rows: list[dict] = []
    us_holidays_by_year: dict[int, dict[date, str]] = {}
    my_holidays_by_year: dict[int, dict[date, str]] = {}

    d = start
    while d <= end:
        yr = d.year
        if yr not in us_holidays_by_year:
            us_holidays_by_year[yr] = _us_market_holidays(yr)
            my_holidays_by_year[yr] = _malaysian_public_holidays(yr)

        is_weekend = d.weekday() >= 5
        us_holiday = us_holidays_by_year[yr].get(d)
        my_holiday = my_holidays_by_year[yr].get(d)
        is_us_holiday = us_holiday is not None
        # Combine holiday names (a date can be both US and MY holiday)
        holiday_names = [h for h in [us_holiday, my_holiday] if h]
        holiday_name = " / ".join(holiday_names) if holiday_names else None
        # NYSE trading day: not weekend, not US holiday
        is_trading = not is_weekend and not is_us_holiday

        _, last_dom = calendar.monthrange(yr, d.month)

        rows.append({
            "date": d,
            "day_of_week": d.weekday(),
            "day_of_week_name": DAY_NAMES[d.weekday()],
            "day_of_month": d.day,
            "week_of_year": d.isocalendar()[1],
            "month": d.month,
            "month_name": MONTH_NAMES[d.month],
            "quarter": (d.month - 1) // 3 + 1,
            "year": yr,
            "is_weekend": is_weekend,
            "is_trading_day": is_trading,
            "is_month_start": d.day == 1,
            "is_month_end": d.day == last_dom,
            "is_quarter_start": d.month in (1, 4, 7, 10) and d.day == 1,
            "is_quarter_end": d.month in (3, 6, 9, 12) and d.day == last_dom,
            "is_year_start": d.month == 1 and d.day == 1,
            "is_year_end": d.month == 12 and d.day == last_dom,
            "is_us_holiday": is_us_holiday,
            "holiday_name": holiday_name,
        })

        d += timedelta(days=1)

    # Second pass: compute trading_day_of_month and trading_days_in_month
    from collections import defaultdict
    monthly_trading: dict[tuple[int, int], int] = defaultdict(int)
    for r in rows:
        if r["is_trading_day"]:
            monthly_trading[(r["year"], r["month"])] += 1

    trading_counter: dict[tuple[int, int], int] = defaultdict(int)
    for r in rows:
        key = (r["year"], r["month"])
        r["trading_days_in_month"] = monthly_trading[key]
        if r["is_trading_day"]:
            trading_counter[key] += 1
            r["trading_day_of_month"] = trading_counter[key]
        else:
            r["trading_day_of_month"] = None

    return rows


def seed(start_year: int = 2024, end_year: int = 2027) -> int:
    """Insert calendar rows into dim_calendar, skipping existing dates."""
    from sqlalchemy import select

    from src.database.connection import SessionLocal
    from src.database.models import DimCalendar

    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    rows = build_calendar_rows(start, end)

    db = SessionLocal()
    try:
        existing = {
            r[0] for r in db.execute(select(DimCalendar.date)).fetchall()
        }

        new_rows = [r for r in rows if r["date"] not in existing]
        if not new_rows:
            print(f"All {len(rows)} dates already exist. Nothing to insert.")
            return 0

        for r in new_rows:
            db.add(DimCalendar(**r))

        db.commit()
        print(f"Inserted {len(new_rows)} calendar rows ({start} to {end}).")
        return len(new_rows)
    finally:
        db.close()


if __name__ == "__main__":
    start_yr = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    end_yr = int(sys.argv[2]) if len(sys.argv) > 2 else 2027
    seed(start_yr, end_yr)
