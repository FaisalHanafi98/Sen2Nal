"""
Pytest configuration and fixtures for Sen2Nal tests.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.database.connection import Base
from src.api.main import app


# =============================================================================
# Test Database
# =============================================================================


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine."""
    # Use in-memory SQLite for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a new database session for each test."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine,
    )
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()


# =============================================================================
# API Client
# =============================================================================


@pytest.fixture(scope="module")
def test_client():
    """Create a test client for FastAPI."""
    return TestClient(app)


# =============================================================================
# Sample Data
# =============================================================================


@pytest.fixture
def sample_stock_data():
    """Sample stock data for testing."""
    return {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "sector": "Technology",
        "market_cap": 2800000000000,
        "sp500_rank": 1,
    }


@pytest.fixture
def sample_sentiment_data():
    """Sample sentiment data for testing."""
    return {
        "nlp_score": 0.72,
        "calendar_score": 0.65,
        "combined_score": 0.69,
        "signal": "BUY",
        "confidence": 0.73,
    }
