> **GOVERNANCE NOTICE**: This project-level CLAUDE.md operates under the authority of the root CLAUDE.md. In case of conflict, root CLAUDE.md (Section 0.2 Override Hierarchy) prevails. This file may define project-specific constraints but may not override root governance.

---

# Sen2Nal - Stock Sentiment + Calendar Signal Analysis

## Project Overview

Sen2Nal is a 6-agent sequential ML pipeline for stock sentiment analysis combining NLP-based FinBERT scoring with calendar-based seasonal patterns to generate trading signals. Covers **Bursa Malaysia stocks** and **S&P 500 top 10**. Includes a weekly experiment comparing Sen2Nal's stock picks against LLM recommendations (ChatGPT, Gemini, Grok).

**Core Philosophy**: "Signal over certainty" - Surface measurable patterns, not predictions. Every score is decomposed transparently.

## Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Language | Python | 3.11+ |
| Package Manager | Poetry | Latest |
| API Framework | FastAPI | 0.109+ |
| Frontend | React (NightOps Terminal) | Vite + Tailwind |
| NLP Model | FinBERT | HuggingFace |
| ML Framework | XGBoost | 2.0+ |
| Database | PostgreSQL | 15+ |
| ORM | SQLAlchemy | 2.0+ |
| Migrations | Alembic | 1.13+ |
| Testing | Pytest | 158+ tests |
| Infrastructure | Docker Compose / AWS Lightsail | - |

## 6-Agent Pipeline Architecture

| Agent | ID | File | Purpose |
|-------|----|------|---------|
| Data Ingestion | AG-01 | `src/agents/ingestion.py` | Fetch from Alpha Vantage, NewsAPI, Yahoo, Reddit, Fear & Greed |
| Sentiment Analysis | AG-02 | `src/agents/sentiment.py` | FinBERT scoring with VADER fallback |
| Calendar Pattern | AG-03 | `src/agents/calendar.py` | Holiday decay e^(-n) for NYSE + Bursa, calendar effects |
| Feature Engineering | AG-04 | `src/agents/features.py` | Multi-timeframe signals, SHAP analysis |
| Prediction | AG-05 | `src/agents/prediction.py` | XGBoost with walk-forward validation (ADR-005) |
| Experiment | AG-06 | `src/agents/experiment.py` | Weekly LLM comparison (non-critical, no contract) |

**Pipeline Flow**: Ingestion → Sentiment → Calendar → Features → Prediction → Experiment

**Stage Gating**: Pipeline halts on any critical stage failure (stages 1-5). Experiment (stage 6) is non-critical.

**Data Contracts**: All 5 critical agents enforce Pydantic contracts via `_validate_output()`. Contract violations raise `DataContractViolation` and halt the pipeline.

## Project Structure

```
sen2nal/
├── src/
│   ├── agents/        # 6 pipeline agents (base.py + ingestion/sentiment/calendar/features/prediction/experiment)
│   ├── api/           # FastAPI endpoints + routers (stocks, experiments, pipeline, alerts)
│   ├── contracts/     # Pydantic data contracts per stage
│   ├── data_quality/  # Stage validator (validate_stage)
│   ├── database/      # Models, connection, migrations
│   ├── pipeline/      # Runner (orchestrator) + scheduler
│   └── config.py      # Pydantic Settings
├── tests/             # 158+ tests across 10 files
├── scripts/           # seed_calendar.py, check_setup.py, check_dependencies.py
├── frontend/          # React NightOps Terminal (Vite + Tailwind + Redux)
├── infrastructure/    # Docker, nginx, deploy scripts
├── docs/adr/          # 5 Architecture Decision Records
└── docker-compose.yml # 4 services: postgres, app, frontend, pgadmin
```

## Key Decisions (DO NOT RE-ASK)

| Decision | Outcome |
|----------|---------|
| Dashboard technology | Streamlit killed. React frontend replaces it. |
| Walk-forward vs all-data | Walk-forward strictly (ADR-005): 252-day train, 21-day test |
| Test database | PostgreSQL only. SQLite divergence is not acceptable. |
| Model persistence | joblib to Docker volume for MVP. S3 later. |
| Ticker universe | 10 tickers for MVP (`ALLOWED_TICKERS` in `src/constants.py`) |
| Holiday coverage | Both NYSE and Bursa Malaysia holidays (2024-2027) |

## Development Commands

```bash
# Install dependencies
poetry install

# Run FastAPI server
uvicorn src.api.main:app --reload --port 8000

# Run tests (requires PostgreSQL)
docker-compose up -d postgres
pytest tests/ -v --cov=src --cov-fail-under=40

# Seed calendar with holidays
poetry run python scripts/seed_calendar.py

# Run full pipeline
poetry run python -m src.pipeline.runner

# Docker development
docker-compose up -d
```

## Quality Gates

- All tests pass against PostgreSQL (not SQLite)
- Coverage >= 40% (Wave 1 target; 80% at project completion)
- Type checking passes (mypy)
- Linting passes (ruff)
- Data contracts enforced at every stage boundary
- Pipeline halts on upstream failure

## Security

- POST /pipeline/run requires `X-Api-Key` header when `PIPELINE_API_KEY` is set
- Ticker whitelist enforced at API level (`ALLOWED_TICKERS`)
- No synthetic/fake data in API responses

## Data Sources

| Source | Data Type | Rate Limit |
|--------|-----------|------------|
| Yahoo Finance (yfinance) | OHLCV prices | Fair use |
| NewsAPI | Financial news | 100/day (free) |
| Reddit (PRAW) | Social sentiment | 100/min |
| CNN Fear & Greed | Market sentiment | Hourly |

---
*Last Updated: 2026-04-02*
*Architecture: 6-Agent Pipeline v1.0*
*Tests: 158+ across 10 files*
