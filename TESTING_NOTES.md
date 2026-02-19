# Testing Notes — Phase 5.5.2 Smoke Test Findings

**Date**: 2026-02-19
**Python**: 3.14.2 (local), 3.11 (Docker/CI target)

## Smoke Test Results

| Test | Result | Notes |
|------|--------|-------|
| Environment Variables | PASS | 3 optional API keys = placeholder warnings |
| PostgreSQL Connection | FAIL | Docker Desktop not running (infrastructure, not code) |
| FinBERT Model Load | PASS | 17.6s load, 0.13s inference, pos=0.94 for bullish headline |
| Python 3.14 Compat | PASS | torch, transformers, xgboost, sqlalchemy all import clean |

## Key Observations

1. **Poetry venv was disconnected** — `poetry env info --path` pointed to system Python. Fixed with `poetry env use python`. CI and Docker should pin virtualenvs explicitly.

2. **Windows cp1252 encoding** — Unicode symbols (checkmark, warning) crash on Windows console. Smoke test switched to ASCII `[OK]`/`[WARN]`/`[FAIL]`. All scripts must use ASCII-safe output.

3. **FinBERT cold start = 17.6s** — First load downloads ~400MB. Subsequent loads use cache (~4s). Production should pre-warm or cache the model.

4. **No python-dotenv in system Python** — Smoke test uses manual .env parser. Not an issue when running via `poetry run`.

## Components Needing Test Fixtures

| Component | Fixture Needed |
|-----------|---------------|
| FinBERT inference | Deterministic input/output pairs with tolerance (±0.05) |
| PostgreSQL CRUD | Transaction-rollback per test, separate test schema |
| Data contracts | Valid/invalid record fixtures for each Pydantic model |
| Calendar patterns | Frozen dates (known holidays, earnings dates) |
| Feature engineering | Pre-computed feature vectors for snapshot testing |

## Suggested Test Categories for Phase 5.5.3

1. **Contract validation tests** — Valid and invalid data through each Pydantic contract
2. **Database model tests** — SQLAlchemy models against in-memory SQLite (conftest.py fixtures exist)
3. **API endpoint tests** — FastAPI TestClient for health check and future routes
4. **Smoke test as CI step** — Run `scripts/smoke_test.py` in CI with PostgreSQL service

## Python 3.14 Compatibility

No issues found. All core packages (torch, transformers, xgboost, sqlalchemy) import without errors or deprecation warnings on Python 3.14.2.
