"""Pytest configuration and fixtures for Sen2Nal tests."""

import os
from datetime import date

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.database.connection import Base, get_db
from src.database.models import DimCalendar, DimStock
from src.api.main import app

TEST_DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://sen2nal_user:sen2nal_password@localhost:5432/sen2nal_test",
)


@pytest.fixture(scope="session")
def test_db_engine():
    """PostgreSQL engine for tests — matches production behavior."""
    engine = create_engine(TEST_DB_URL, echo=False)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        pytest.skip("PostgreSQL test database not available")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db(test_db_engine):
    """Per-test session with automatic rollback."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    """FastAPI test client wired to the test DB session."""

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def seed_stock(db):
    """Insert a test stock and return it."""
    stock = DimStock(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        market_cap=3_450_000_000_000,
        sp500_rank=1,
        is_active=True,
    )
    db.add(stock)
    db.flush()
    return stock


@pytest.fixture
def seed_calendar(db):
    """Insert a test calendar date and return it."""
    target = date(2026, 3, 20)
    cal = DimCalendar(
        date=target,
        day_of_week=target.weekday(),
        day_of_week_name="Friday",
        day_of_month=20,
        week_of_year=12,
        month=3,
        month_name="March",
        quarter=1,
        year=2026,
        is_weekend=False,
        is_trading_day=True,
        is_month_start=False,
        is_month_end=False,
        is_quarter_start=False,
        is_quarter_end=False,
        is_year_start=False,
        is_year_end=False,
        is_us_holiday=False,
    )
    db.add(cal)
    db.flush()
    return cal
