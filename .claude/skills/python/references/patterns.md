# Python Development Patterns

## Core Principles

### Readability Counts
```python
# Good: Clear and readable
def get_active_users(users: list[User]) -> list[User]:
    return [user for user in users if user.is_active]

# Bad: Clever but confusing
def get_active_users(u): return [x for x in u if x.a]
```

### Type Hints (always)
```python
from typing import Optional

def process_user(user_id: str, data: dict[str, Any], active: bool = True) -> Optional[User]:
    if not active:
        return None
    return User(user_id, data)

# Python 3.9+ — use built-in types directly
def process_items(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}
```

## Error Handling

```python
# Specific exceptions with chaining
def load_config(path: str) -> Config:
    try:
        with open(path) as f:
            return Config.from_json(f.read())
    except FileNotFoundError as e:
        raise ConfigError(f"Config file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in config: {path}") from e

# Custom exception hierarchy
class AppError(Exception): pass
class ValidationError(AppError): pass
class NotFoundError(AppError): pass
```

## Data Classes

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Transaction:
    id: str
    amount: float
    currency: str
    created_at: datetime = field(default_factory=datetime.now)
    is_reconciled: bool = False

    def __post_init__(self):
        if self.amount <= 0:
            raise ValueError(f"Amount must be positive: {self.amount}")
```

## Context Managers

```python
@contextmanager
def db_transaction(session):
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
```

## Generators for Large Data

```python
# Good: Generator — lazy evaluation
def read_transactions(path: str) -> Iterator[Transaction]:
    with open(path) as f:
        for line in f:
            yield Transaction.from_csv(line.strip())

# Bad: Loads everything into memory
def read_transactions(path: str) -> list[Transaction]:
    with open(path) as f:
        return [Transaction.from_csv(line) for line in f]
```

## Async for FastAPI (RinggitSense)

```python
import asyncio
import aiohttp

async def fetch_stock_data(symbol: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.example.com/stocks/{symbol}") as response:
            return await response.json()

async def fetch_all_stocks(symbols: list[str]) -> dict[str, dict]:
    tasks = [fetch_stock_data(s) for s in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return dict(zip(symbols, results))
```

## Anti-Patterns to Avoid

```python
# BAD: Mutable default argument
def append_to(item, items=[]):   # Bug: shared across calls
    items.append(item)
    return items

# GOOD
def append_to(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items

# BAD: Bare except (swallows all errors)
try:
    operation()
except:
    pass

# GOOD
try:
    operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")

# BAD: Comparing with ==
if value == None: ...
if type(obj) == list: ...

# GOOD
if value is None: ...
if isinstance(obj, list): ...
```

## Tooling

```bash
black .                         # Format
isort .                         # Sort imports
ruff check .                    # Lint
mypy .                          # Type check
pytest --cov=mypackage          # Tests with coverage
bandit -r .                     # Security scan
pip-audit                       # Dependency vulnerabilities
```
