"""Pytest configuration and fixtures for Sen2Nal tests."""

import os
import uuid
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema
from fastapi.testclient import TestClient

from src.database.connection import Base, get_db
from src.database.models import DimCalendar, DimStock
from src.api.main import app

@pytest.fixture(scope="session")
def test_db_engine():
    """Use only an explicit local test DB and a unique fixture-owned schema."""
    explicit_url = os.environ.get("SEN2NAL_TEST_DATABASE_URL")
    if not explicit_url:
        pytest.skip("SEN2NAL_TEST_DATABASE_URL unset; PostgreSQL integration unverified")
    try:
        url = make_url(explicit_url)
        if (url.drivername not in {"postgresql", "postgresql+psycopg2"}
                or url.host not in {"localhost", "127.0.0.1", "::1"}
                or not (url.database or "").endswith("_test") or url.query):
            raise ValueError
    except (ArgumentError, ValueError):
        raise ValueError("Provide an explicit local PostgreSQL test URL ending in '_test'") from None

    with pytest.MonkeyPatch.context() as routing:
        for key in list(os.environ):
            if key.upper().startswith("PG"):
                routing.delenv(key, raising=False)
        schema = f"sen2nal_test_{uuid.uuid4().hex}"
        engine = create_engine(url, echo=False, connect_args={
            "options": f"-csearch_path={schema}",
            "hostaddr": "::1" if url.host == "::1" else "127.0.0.1",
        })
        created = False
        try:
            with engine.begin() as conn:
                conn.execute(CreateSchema(schema))
            created = True
            Base.metadata.create_all(bind=engine)
            yield engine
        finally:
            try:
                if created:
                    with engine.begin() as conn:
                        conn.execute(DropSchema(schema, cascade=True))
            finally:
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
