# Python Testing Patterns

## TDD Cycle

```bash
# Step 1: Write failing test
# Step 2: pytest tests/test_file.py::test_name -v  (confirm RED)
# Step 3: Implement minimal code
# Step 4: pytest tests/test_file.py::test_name -v  (confirm GREEN)
# Step 5: Refactor, run full suite: pytest
```

Target: 80%+ coverage. 100% on critical paths (auth, financial calculations, PDPA-sensitive).

## Fixtures

```python
import pytest
from datetime import datetime

@pytest.fixture
def sample_transaction():
    return Transaction(id="tx1", amount=150.00, currency="MYR",
                       created_at=datetime(2026, 1, 1))

@pytest.fixture
def db_session():
    session = Session(bind=engine)
    session.begin_nested()
    yield session
    session.rollback()
    session.close()

# Autouse — resets state before every test
@pytest.fixture(autouse=True)
def reset_cache(redis_client):
    redis_client.flushdb()
    yield
```

## Parametrize

```python
@pytest.mark.parametrize("amount,currency,expected_error", [
    (0, "MYR", "Amount must be positive"),
    (-100, "MYR", "Amount must be positive"),
    (100, "INVALID", "Invalid currency"),
])
def test_transaction_validation(amount, currency, expected_error):
    with pytest.raises(ValueError, match=expected_error):
        Transaction(id="tx1", amount=amount, currency=currency)
```

## Mocking

```python
from unittest.mock import patch, Mock

@patch("ringgitsense.services.bursa_api.fetch_price")
def test_get_stock_price_with_mock(mock_fetch):
    mock_fetch.return_value = {"symbol": "MAYBANK", "price": 9.50}
    result = get_stock_price("MAYBANK")
    mock_fetch.assert_called_once_with("MAYBANK")
    assert result["price"] == 9.50

@patch("ringgitsense.services.bursa_api.fetch_price")
def test_handles_api_error(mock_fetch):
    mock_fetch.side_effect = ConnectionError("API unavailable")
    with pytest.raises(StockServiceError):
        get_stock_price("MAYBANK")
```

## Async Tests (FastAPI)

```python
import pytest

@pytest.mark.asyncio
async def test_async_stock_fetch():
    result = await fetch_stock_data("MAYBANK")
    assert "price" in result

# FastAPI test client
@pytest.fixture
def client():
    app = create_app(testing=True)
    return TestClient(app)

def test_get_transaction(client, db_session):
    response = client.get("/api/transactions/tx1")
    assert response.status_code == 200
    assert response.json()["id"] == "tx1"
```

## Exception Testing

```python
def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        calculate_percentage(10, 0)

def test_custom_error_details():
    with pytest.raises(ValidationError) as exc_info:
        create_transaction(amount=-100)
    assert exc_info.value.code == "invalid_amount"
```

## Configuration

```ini
# pytest.ini
[pytest]
testpaths = tests
addopts =
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
markers =
    slow: marks tests as slow (deselect with -m "not slow")
    integration: requires external services
    unit: pure unit tests
```

```bash
# Common commands
pytest                          # Run all
pytest -m "not slow"            # Skip slow tests
pytest tests/unit/              # Unit tests only
pytest --lf                     # Last failed
pytest -x                       # Stop on first failure
pytest --cov=src --cov-report=html  # Coverage report
```

## Financial Calculation Testing (RinggitSense)

```python
# Use Decimal for financial calculations — never float
from decimal import Decimal

def test_portfolio_value():
    holdings = [
        Holding(symbol="MAYBANK", quantity=100, price=Decimal("9.50")),
        Holding(symbol="PBBANK", quantity=200, price=Decimal("4.20")),
    ]
    total = calculate_portfolio_value(holdings)
    assert total == Decimal("1790.00")  # 950 + 840

# Test financial disclaimer is present in output
def test_prediction_includes_disclaimer(client):
    response = client.get("/api/predictions/MAYBANK")
    assert "NOT FINANCIAL ADVICE" in response.json()["disclaimer"]
```
