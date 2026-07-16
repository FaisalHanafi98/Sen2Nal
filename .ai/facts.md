Six-agent sequential ML pipeline: FinBERT sentiment (VADER fallback) + calendar
seasonality → XGBoost trading signals. Bursa Malaysia stocks + S&P 500 top 10.
Philosophy: "signal over certainty" — surface measurable patterns, decompose
every score transparently. Every prediction output carries **NOT FINANCIAL
ADVICE**.

### Pipeline (src/agents/, sequential, stage-gated)

AG-01 ingestion → AG-02 sentiment → AG-03 calendar → AG-04 features →
AG-05 prediction → AG-06 experiment (weekly LLM comparison; non-critical).
Stages 1–5 are critical: any failure halts the pipeline. All critical agents
enforce Pydantic contracts via `_validate_output()`; violations raise
`DataContractViolation`.

### Decided — do not re-ask

- Streamlit is dead; the frontend is React (Vite + Tailwind, "NightOps Terminal").
- Walk-forward validation strictly (ADR-005): 252-day train, 21-day test.
- Tests run against PostgreSQL only; SQLite divergence unacceptable.
- Model persistence: joblib to Docker volume for MVP; S3 later.
- Ticker universe: 10 MVP tickers in `ALLOWED_TICKERS` (src/constants.py).
- Holidays: both NYSE and Bursa, 2024–2027.

### Commands

`poetry install` · `uvicorn src.api.main:app --reload --port 8000` ·
`docker-compose up -d postgres` then `pytest tests/ -v --cov=src
--cov-fail-under=40` · `poetry run python scripts/seed_calendar.py` ·
`poetry run python -m src.pipeline.runner`

### Gates and security

Coverage ≥40% (Wave 1; 80% end target) · mypy and ruff clean · contracts
enforced at every stage boundary. `POST /pipeline/run` requires `X-Api-Key`
when `PIPELINE_API_KEY` is set; ticker whitelist enforced at the API; never
return synthetic data from API responses.

### External data limits

NewsAPI 100/day · Reddit 100/min · yfinance fair use · CNN Fear & Greed hourly.
ADRs live in `docs/adr/`.
