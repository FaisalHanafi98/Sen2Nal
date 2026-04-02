> **GOVERNANCE NOTICE**: This project-level CLAUDE.md operates under the authority of the root CLAUDE.md. In case of conflict, root CLAUDE.md (Section 0.2 Override Hierarchy) prevails. This file may define project-specific constraints but may not override root governance.

---

# Sen2Nal - Stock Sentiment + Calendar Signal Analysis

## Project Overview

Sen2Nal is a stock sentiment analysis platform combining NLP-based sentiment scoring with calendar-based seasonal patterns to generate trading signals. Includes a live experiment comparing Sen2Nal's stock picks against LLM recommendations (ChatGPT, Gemini, Grok).

**Core Philosophy**: "Signal over certainty" - Surface measurable patterns, not predictions. Every score is decomposed transparently.

## Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Language | Python | 3.11+ |
| Package Manager | Poetry | Latest |
| API Framework | FastAPI | 0.109+ |
| Dashboard | Streamlit | 1.30+ |
| NLP Model | FinBERT | HuggingFace |
| ML Framework | XGBoost | 2.0+ |
| Database | PostgreSQL | 15+ |
| ORM | SQLAlchemy | 2.0+ |
| Migrations | Alembic | 1.13+ |
| Visualization | Plotly | 5.18+ |
| Testing | Pytest | Latest |
| Infrastructure | AWS (EC2, RDS, S3) | - |

## Project Structure

```
sen2nal/
├── src/
│   ├── api/           # FastAPI endpoints
│   ├── dashboard/     # Streamlit app
│   ├── database/      # Models, migrations
│   ├── ingestion/     # Data fetching (planned)
│   ├── processing/    # Text cleaning (planned)
│   └── scoring/       # FinBERT + calendar (planned)
├── tests/             # Pytest tests
├── scripts/           # Utility scripts
├── infrastructure/    # Docker, AWS configs
└── docs/              # Additional documentation
```

## Development Commands

```bash
# Install dependencies
poetry install

# Run FastAPI server
uvicorn src.api.main:app --reload --port 8000

# Run Streamlit dashboard
streamlit run src/dashboard/app.py --server.port 8501

# Run tests
pytest tests/ -v

# Run migrations
alembic upgrade head

# Docker development
docker-compose up -d

# Code quality
black src/ tests/
ruff check src/ tests/
mypy src/
```

## Key Features

### MVP Features
1. **Dashboard** - Top 10 stocks by market cap with daily scores
2. **Stock Search** - Search S&P 500 stocks with sentiment analysis
3. **Sector View** - Sector-level sentiment aggregation
4. **Calendar Patterns** - Holiday decay, weekend accumulation effects
5. **SHAP Explainability** - Transparent signal decomposition

### LLM Experiment
- 8-week comparison: Sen2Nal vs ChatGPT vs Gemini vs Grok
- Weekly portfolio picks tracked and published
- Research paper output

## Data Sources

| Source | Data Type | Rate Limit |
|--------|-----------|------------|
| Alpha Vantage | Stock prices | 5/min (free) |
| Yahoo Finance | Historical data | Fair use |
| Reddit (PRAW) | Social sentiment | 100/min |
| NewsAPI | News articles | 100/day (free) |
| Fear & Greed | Market sentiment | Hourly |

## Architecture Layers

1. **Ingestion Layer** - APScheduler + API clients + rate limiting
2. **Processing Layer** - Text cleaning, ticker extraction, deduplication
3. **Scoring Layer** - FinBERT sentiment + calendar patterns + signal combination
4. **Storage Layer** - PostgreSQL (dim/fact tables) + S3 (raw data)
5. **Serving Layer** - FastAPI REST endpoints
6. **Presentation Layer** - Streamlit dashboard

## Development Rules

1. **Test Coverage**: Minimum 80% for core scoring logic
2. **Type Hints**: All functions must have type annotations
3. **Docstrings**: Google-style docstrings required
4. **Error Handling**: Never expose raw exceptions to users
5. **Rate Limiting**: Respect all API rate limits
6. **Data Validation**: Use Pydantic for all external data

## Environment Variables

See `.env.example` for required configuration:
- Database connection (PostgreSQL)
- API keys (Alpha Vantage, NewsAPI, Reddit)
- AWS credentials (S3, optional)

## Quality Gates

- All tests pass
- Type checking passes (mypy)
- Linting passes (ruff)
- Code formatted (black)
- Coverage >= 80% for scoring modules

## Current Status (Phase 5.5.1 Complete)

| Component | Status | Details |
|-----------|--------|---------|
| **Python Environment** | ✅ Ready | Python 3.14.2, Poetry installed, 100+ packages |
| **PostgreSQL Database** | ✅ Running | Docker container `sen2nal-postgres` healthy |
| **Database Schema** | ✅ Applied | 10 tables (3 dim, 4 fact, 2 staging, 1 tracking) |
| **Indexes** | ✅ Created | 16 indexes including 5 composite |
| **Foreign Keys** | ✅ Created | 3 FK constraints with CASCADE delete |
| **Alembic Migrations** | ✅ Initialized | Revision '001' recorded |
| **UUID Extension** | ✅ Enabled | uuid-ossp active |

### Quick Start Commands
```bash
# Activate environment (if not active)
cd Sen2Nal
poetry shell

# Start database (if stopped)
docker-compose up -d postgres

# Verify database connection
docker-compose exec postgres psql -U sen2nal_user -d sen2nal -c "\dt"

# Run verification script
poetry run python scripts/check_setup.py
```

### Next Phase: 5.5.2 (Initial Data Pipeline Test)
1. Fetch sample stock data from Alpha Vantage
2. Run FinBERT sentiment analysis
3. Store results in PostgreSQL
4. Visualize in Streamlit dashboard

## Agent Architecture

Sen2Nal uses a **7-Agent System** for modular development:

| Agent | Role | Key Technology |
|-------|------|----------------|
| 1. Data Ingestion | Fetch external data | Alpha Vantage, Reddit, NewsAPI |
| 2. Sentiment Analysis | NLP processing | FinBERT (88% F1), VADER |
| 3. Calendar Pattern | Temporal effects | Holiday decay (e^-n), earnings |
| 4. Feature Engineering | Signal combination | Multi-timeframe, SHAP |
| 5. Prediction | ML inference | XGBoost, walk-forward validation |
| 6. Database | Data persistence | PostgreSQL star schema |
| 7. Dashboard | Visualization | Streamlit, Plotly |

**Pipeline Flow**: Ingestion → Sentiment → Calendar → Features → Prediction → Database → Dashboard

> Token optimization and CLI-first rules: See root [CLAUDE.md](../CLAUDE.md) v2.0.0 (Section 6).

## Documentation References

### Core Documentation
- [SEN2NAL_PRD.md](SEN2NAL_PRD.md) - Product requirements
- [SEN2NAL_TECHNICAL_ARCHITECTURE.md](SEN2NAL_TECHNICAL_ARCHITECTURE.md) - System design
- [SEN2NAL_API_REFERENCE.md](SEN2NAL_API_REFERENCE.md) - API documentation
- [SEN2NAL_DATABASE_SCHEMA.md](SEN2NAL_DATABASE_SCHEMA.md) - Data models
- [SEN2NAL_TESTING_STRATEGY.md](SEN2NAL_TESTING_STRATEGY.md) - Test approach
- [SEN2NAL_DEVELOPMENT_SETUP.md](SEN2NAL_DEVELOPMENT_SETUP.md) - Setup guide

### Agent & MCP Documentation
- [SEN2NAL_AGENT_PROMPTS.md](SEN2NAL_AGENT_PROMPTS.md) - 7-agent system prompts
- [SEN2NAL_MCP_INTEGRATION.md](SEN2NAL_MCP_INTEGRATION.md) - MCP usage patterns

### Research
- [SEN2NAL_RESEARCH_KNOWLEDGE_BASE.md](SEN2NAL_RESEARCH_KNOWLEDGE_BASE.md) - 47 sources synthesis

---
*Last Updated: 2026-01-16*
*Phase: 5.5.1 Complete - Environment Ready*
*Agent Architecture: 7-Agent System v1.0*
*Token Optimization: See Root CLAUDE.md v2.0.0*
