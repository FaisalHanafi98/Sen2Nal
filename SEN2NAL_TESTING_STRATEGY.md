# Sen2Nal: Testing Strategy

**Version:** 1.0  
**Author:** Faisal  
**Last Updated:** January 2026

---

## 1. Testing Overview

### 1.1 Testing Philosophy

Sen2Nal follows the **Testing Pyramid** approach:

```
           /\
          /  \
         / E2E \        <- Few, slow, expensive
        /--------\
       /Integration\    <- Some, moderate
      /--------------\
     /   Unit Tests   \  <- Many, fast, cheap
    /------------------\
```

### 1.2 Coverage Targets

| Layer | Target | Priority |
|-------|--------|----------|
| Unit Tests | 85%+ | P0 |
| Integration Tests | 70%+ | P0 |
| E2E Tests | Key flows | P1 |

### 1.3 Testing Tools

| Tool | Purpose |
|------|---------|
| pytest | Test framework |
| pytest-cov | Coverage reporting |
| pytest-asyncio | Async test support |
| httpx | API testing |
| factory_boy | Test data factories |
| faker | Fake data generation |

---

## 2. Unit Testing

### 2.1 What to Unit Test

| Module | Focus Areas |
|--------|-------------|
| `sentiment/` | FinBERT scoring, aggregation |
| `calendar/` | Pattern calculation, scoring |
| `features/` | Signal combination, conflict detection |
| `processing/` | Text cleaning, ticker extraction |
| `database/` | Repository methods |

### 2.2 Unit Test Examples

#### Testing FinBERT Scorer

```python
# tests/unit/test_finbert_scorer.py

import pytest
from src.sentiment.finbert_scorer import FinBERTScorer

class TestFinBERTScorer:
    
    @pytest.fixture
    def scorer(self):
        return FinBERTScorer()
    
    def test_positive_sentiment(self, scorer):
        """Test that positive news returns positive score."""
        text = "Apple reports record-breaking quarterly revenue"
        result = scorer.score_text(text)
        
        assert result["score"] > 0
        assert result["label"] == "positive"
        assert 0 <= result["confidence"] <= 1
    
    def test_negative_sentiment(self, scorer):
        """Test that negative news returns negative score."""
        text = "Company announces massive layoffs amid declining sales"
        result = scorer.score_text(text)
        
        assert result["score"] < 0
        assert result["label"] == "negative"
    
    def test_neutral_sentiment(self, scorer):
        """Test that neutral text returns near-zero score."""
        text = "The company held its annual meeting today"
        result = scorer.score_text(text)
        
        assert -0.3 < result["score"] < 0.3
    
    def test_batch_scoring(self, scorer):
        """Test batch processing returns correct count."""
        texts = [
            "Great earnings report",
            "Stock crashes on bad news",
            "Quarterly results released"
        ]
        results = scorer.score_batch(texts)
        
        assert len(results) == 3
        assert all("score" in r for r in results)
    
    def test_empty_text_handling(self, scorer):
        """Test handling of empty text."""
        with pytest.raises(ValueError):
            scorer.score_text("")
    
    def test_long_text_truncation(self, scorer):
        """Test that long text is truncated properly."""
        long_text = "word " * 1000  # Much longer than 512 tokens
        result = scorer.score_text(long_text)
        
        assert "score" in result  # Should not error
```

#### Testing Signal Combiner

```python
# tests/unit/test_signal_combiner.py

import pytest
from src.features.signal_combiner import SignalCombiner, Signal

class TestSignalCombiner:
    
    @pytest.fixture
    def combiner(self):
        return SignalCombiner(
            nlp_weight=0.6,
            calendar_weight=0.4,
            conflict_threshold=0.30
        )
    
    @pytest.mark.parametrize("nlp,cal,expected", [
        (0.8, 0.7, Signal.STRONG_BUY),
        (0.5, 0.5, Signal.HOLD),
        (-0.6, -0.4, Signal.AVOID),
        (0.6, 0.5, Signal.BUY),
    ])
    def test_signal_classification(self, combiner, nlp, cal, expected):
        """Test signal classification for various score combinations."""
        result = combiner.combine(nlp, cal)
        assert result.signal == expected
    
    def test_conflict_detection_when_scores_differ(self, combiner):
        """Test that conflict is detected when scores differ significantly."""
        result = combiner.combine(nlp_score=0.7, calendar_score=-0.5)
        
        assert result.conflict_flag == True
        assert result.conflict_reason is not None
    
    def test_no_conflict_when_scores_similar(self, combiner):
        """Test no conflict when scores are similar."""
        result = combiner.combine(nlp_score=0.5, calendar_score=0.4)
        
        assert result.conflict_flag == False
    
    def test_confidence_reduced_on_conflict(self, combiner):
        """Test that confidence is lower when there's a conflict."""
        no_conflict = combiner.combine(0.5, 0.5, nlp_confidence=0.9)
        with_conflict = combiner.combine(0.8, -0.5, nlp_confidence=0.9)
        
        assert with_conflict.confidence < no_conflict.confidence
    
    def test_combined_score_range(self, combiner):
        """Test that combined score is always in valid range."""
        for nlp in [-1, -0.5, 0, 0.5, 1]:
            for cal in [-1, -0.5, 0, 0.5, 1]:
                result = combiner.combine(nlp, cal)
                assert 0 <= result.combined_score <= 1
```

#### Testing Calendar Patterns

```python
# tests/unit/test_calendar_patterns.py

import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.calendar.seasonal_patterns import CalendarPatternCalculator

class TestCalendarPatternCalculator:
    
    @pytest.fixture
    def calculator(self):
        return CalendarPatternCalculator(lookback_months=18)
    
    @pytest.fixture
    def sample_price_history(self):
        """Generate sample price history for testing."""
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=365*2),
            end=datetime.now(),
            freq='D'
        )
        prices = pd.DataFrame({
            'date': dates,
            'adj_close': 100 + pd.Series(range(len(dates))) * 0.05
        })
        return prices
    
    def test_monthly_patterns_calculated(self, calculator, sample_price_history):
        """Test that monthly patterns are calculated for all months."""
        patterns = calculator.calculate_monthly_patterns(sample_price_history)
        
        assert "current_month" in patterns
        assert "historical" in patterns
        assert len(patterns["historical"]) == 12
    
    def test_calendar_score_range(self, calculator, sample_price_history):
        """Test that calendar score is in valid range."""
        patterns = calculator.calculate_monthly_patterns(sample_price_history)
        score = calculator.calculate_calendar_score(patterns)
        
        assert -1 <= score <= 1
    
    def test_earnings_proximity_reduces_score(self, calculator, sample_price_history):
        """Test that earnings proximity affects confidence."""
        patterns = calculator.calculate_monthly_patterns(sample_price_history)
        
        score_no_earnings = calculator.calculate_calendar_score(patterns)
        score_near_earnings = calculator.calculate_calendar_score(
            patterns, 
            earnings_days_away=3
        )
        
        # Score magnitude should be reduced near earnings (more uncertain)
        assert abs(score_near_earnings) <= abs(score_no_earnings)
```

---

## 3. Integration Testing

### 3.1 What to Integration Test

| Area | Focus |
|------|-------|
| API Endpoints | Request/response, status codes |
| Database Operations | CRUD, transactions |
| Pipeline Flow | Ingest → Process → Score |
| External APIs | Mocked responses |

### 3.2 Integration Test Examples

#### Testing API Endpoints

```python
# tests/integration/test_api.py

import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.database.connection import get_db, SessionLocal
from src.database.models import Stock, Sentiment

client = TestClient(app)

class TestStocksAPI:
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Set up test data before each test."""
        db = SessionLocal()
        try:
            # Create test stock
            stock = Stock(
                ticker="TEST",
                company_name="Test Company",
                sector="Technology",
                market_cap=1000000000,
                sp500_rank=100
            )
            db.add(stock)
            db.commit()
            yield
        finally:
            db.query(Stock).filter(Stock.ticker == "TEST").delete()
            db.commit()
            db.close()
    
    def test_health_endpoint(self):
        """Test health check returns 200."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_top10_returns_10_stocks(self):
        """Test top10 endpoint returns exactly 10 stocks."""
        response = client.get("/api/v1/stocks/top10")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["stocks"]) == 10
        assert "fear_greed" in data
    
    def test_stock_detail_valid_ticker(self):
        """Test stock detail returns full data for valid ticker."""
        response = client.get("/api/v1/stocks/AAPL")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert "sentiment" in data
        assert "nlp_breakdown" in data
        assert "calendar_breakdown" in data
    
    def test_stock_detail_invalid_ticker(self):
        """Test stock detail returns 404 for invalid ticker."""
        response = client.get("/api/v1/stocks/INVALID123")
        
        assert response.status_code == 404
        assert "error" in response.json()
    
    def test_search_returns_matches(self):
        """Test search finds matching stocks."""
        response = client.get("/api/v1/stocks/search?q=apple")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) > 0
        assert any(r["ticker"] == "AAPL" for r in data["results"])
    
    def test_sectors_returns_all_sectors(self):
        """Test sectors endpoint returns aggregated data."""
        response = client.get("/api/v1/sectors")
        
        assert response.status_code == 200
        data = response.json()
        assert "sectors" in data
        assert len(data["sectors"]) == 11  # GICS sectors


class TestExperimentAPI:
    
    def test_experiment_status(self):
        """Test experiment endpoint returns status."""
        response = client.get("/api/v1/experiment")
        
        assert response.status_code == 200
        data = response.json()
        assert "current_week" in data
        assert "status" in data
```

#### Testing Database Operations

```python
# tests/integration/test_database.py

import pytest
from datetime import date
from src.database.connection import SessionLocal
from src.database.repositories import StockRepository, SentimentRepository

class TestStockRepository:
    
    @pytest.fixture
    def db(self):
        db = SessionLocal()
        yield db
        db.close()
    
    @pytest.fixture
    def repo(self, db):
        return StockRepository(db)
    
    def test_get_stock_by_ticker(self, repo):
        """Test fetching stock by ticker."""
        stock = repo.get_by_ticker("AAPL")
        
        assert stock is not None
        assert stock.ticker == "AAPL"
        assert stock.company_name == "Apple Inc."
    
    def test_get_top_stocks(self, repo):
        """Test fetching top N stocks by rank."""
        stocks = repo.get_top_by_rank(10)
        
        assert len(stocks) == 10
        assert stocks[0].sp500_rank == 1
    
    def test_search_stocks(self, repo):
        """Test searching stocks."""
        results = repo.search("apple")
        
        assert len(results) > 0
        assert any(s.ticker == "AAPL" for s in results)


class TestSentimentRepository:
    
    @pytest.fixture
    def db(self):
        db = SessionLocal()
        yield db
        db.close()
    
    @pytest.fixture
    def repo(self, db):
        return SentimentRepository(db)
    
    def test_get_latest_sentiment(self, repo):
        """Test fetching latest sentiment for a stock."""
        sentiment = repo.get_latest("AAPL")
        
        assert sentiment is not None
        assert -1 <= sentiment.nlp_score <= 1
    
    def test_get_sentiment_history(self, repo):
        """Test fetching sentiment history."""
        history = repo.get_history("AAPL", days=30)
        
        assert len(history) <= 30
        assert all(h.stock.ticker == "AAPL" for h in history)
```

---

## 4. Data Quality Testing

### 4.1 Data Quality Checks

```python
# tests/data_quality/test_data_quality.py

import pytest
import pandas as pd
from src.database.connection import SessionLocal
from src.database.models import Stock, Sentiment, Price

class TestDataQuality:
    
    @pytest.fixture
    def db(self):
        db = SessionLocal()
        yield db
        db.close()
    
    def test_all_sp500_stocks_present(self, db):
        """Verify all S&P 500 stocks are in database."""
        count = db.query(Stock).filter(Stock.is_active == True).count()
        
        # S&P 500 has ~503 stocks (500 + some with multiple classes)
        assert count >= 500
        assert count <= 510
    
    def test_no_duplicate_tickers(self, db):
        """Verify no duplicate ticker symbols."""
        from sqlalchemy import func
        
        duplicates = db.query(
            Stock.ticker, 
            func.count(Stock.ticker)
        ).group_by(Stock.ticker).having(func.count(Stock.ticker) > 1).all()
        
        assert len(duplicates) == 0
    
    def test_sentiment_scores_in_range(self, db):
        """Verify all sentiment scores are in valid range."""
        invalid = db.query(Sentiment).filter(
            (Sentiment.nlp_score < -1) | 
            (Sentiment.nlp_score > 1) |
            (Sentiment.calendar_score < -1) |
            (Sentiment.calendar_score > 1)
        ).count()
        
        assert invalid == 0
    
    def test_combined_scores_in_range(self, db):
        """Verify combined scores are in 0-1 range."""
        invalid = db.query(Sentiment).filter(
            (Sentiment.combined_score < 0) | 
            (Sentiment.combined_score > 1)
        ).count()
        
        assert invalid == 0
    
    def test_no_future_dates(self, db):
        """Verify no data with future dates."""
        from datetime import date
        
        future_sentiment = db.query(Sentiment).join(
            Sentiment.date_ref
        ).filter(Sentiment.date_ref.date > date.today()).count()
        
        assert future_sentiment == 0
    
    def test_top10_stocks_have_sentiment(self, db):
        """Verify top 10 stocks have recent sentiment data."""
        from datetime import date, timedelta
        
        top10 = db.query(Stock).filter(
            Stock.sp500_rank <= 10
        ).all()
        
        for stock in top10:
            recent_sentiment = db.query(Sentiment).filter(
                Sentiment.stock_id == stock.stock_id
            ).order_by(Sentiment.date_id.desc()).first()
            
            assert recent_sentiment is not None, f"Missing sentiment for {stock.ticker}"
```

---

## 5. Mocking External Services

### 5.1 Mock Fixtures

```python
# tests/fixtures/mocks.py

import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_alpha_vantage():
    """Mock Alpha Vantage API responses."""
    mock_response = {
        "feed": [
            {
                "title": "Apple beats earnings expectations",
                "summary": "Apple reported strong quarterly results...",
                "ticker_sentiment": [
                    {"ticker": "AAPL", "ticker_sentiment_score": 0.8}
                ],
                "time_published": "20260102T060000"
            }
        ]
    }
    
    with patch('src.ingestion.news_client.requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200
        yield mock_get

@pytest.fixture
def mock_reddit():
    """Mock Reddit PRAW responses."""
    mock_submission = Mock()
    mock_submission.title = "AAPL is looking bullish"
    mock_submission.selftext = "Based on recent earnings..."
    mock_submission.score = 100
    mock_submission.created_utc = 1704182400
    
    with patch('praw.Reddit') as mock_reddit:
        mock_reddit.return_value.subreddit.return_value.hot.return_value = [
            mock_submission
        ]
        yield mock_reddit

@pytest.fixture
def mock_yfinance():
    """Mock yfinance responses."""
    import pandas as pd
    
    mock_df = pd.DataFrame({
        'Open': [175.0, 176.0, 177.0],
        'High': [178.0, 179.0, 180.0],
        'Low': [174.0, 175.0, 176.0],
        'Close': [177.0, 178.0, 179.0],
        'Adj Close': [177.0, 178.0, 179.0],
        'Volume': [1000000, 1100000, 1200000]
    }, index=pd.date_range('2026-01-01', periods=3))
    
    with patch('yfinance.Ticker') as mock_ticker:
        mock_ticker.return_value.history.return_value = mock_df
        yield mock_ticker
```

---

## 6. Test Configuration

### 6.1 pytest Configuration

```ini
# pytest.ini

[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    external: Tests that require external services
filterwarnings =
    ignore::DeprecationWarning
```

### 6.2 conftest.py

```python
# tests/conftest.py

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base
from src.database.connection import get_db
from src.api.main import app

# Use test database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://sen2nal:sen2nal_test@localhost:5432/sen2nal_test"
)

@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(engine):
    """Create a new database session for each test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def client(db_session):
    """Create test client with dependency override."""
    from fastapi.testclient import TestClient
    
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()
```

---

## 7. Running Tests

### 7.1 Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_sentiment.py

# Run specific test class
pytest tests/unit/test_sentiment.py::TestFinBERTScorer

# Run specific test function
pytest tests/unit/test_sentiment.py::TestFinBERTScorer::test_positive_sentiment

# Run by marker
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Generate JUnit XML report (for CI)
pytest --junitxml=reports/junit.xml
```

### 7.2 Makefile Commands

```makefile
# Makefile

.PHONY: test test-unit test-integration test-coverage

test:
	pytest

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term
	@echo "Coverage report: htmlcov/index.html"

test-ci:
	pytest --junitxml=reports/junit.xml --cov=src --cov-report=xml
```

---

## 8. CI/CD Integration

### 8.1 GitHub Actions

```yaml
# .github/workflows/test.yml

name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: sen2nal
          POSTGRES_PASSWORD: sen2nal_test
          POSTGRES_DB: sen2nal_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        env:
          TEST_DATABASE_URL: postgresql://sen2nal:sen2nal_test@localhost:5432/sen2nal_test
        run: |
          pytest --junitxml=reports/junit.xml --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

## 9. Test Checklist

### Before Merging

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Coverage >= 80%
- [ ] No new linting errors
- [ ] Data quality tests pass
- [ ] API contract tests pass

### Before Release

- [ ] Full test suite passes
- [ ] Performance tests pass
- [ ] Manual smoke tests complete
- [ ] Documentation updated
