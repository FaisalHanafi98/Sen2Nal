# Sen2Nal 📊

**Stock Sentiment + Calendar Signal Analysis System**

[![CI](https://github.com/FaisalHanafi98/Sen2Nal/actions/workflows/ci.yml/badge.svg)](https://github.com/FaisalHanafi98/Sen2Nal/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61dafb.svg)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Last refreshed**: 2026-05-19 — stale Streamlit references removed; structure aligned with 6-agent pipeline and React frontend. Current verified status: see [docs/audits/CURRENT_SYSTEM_STATE.md](docs/audits/CURRENT_SYSTEM_STATE.md).

---

## ⚠️ Important Disclaimer

**Sen2Nal is NOT a financial advisor.** This project is for **EDUCATIONAL AND INFORMATIONAL PURPOSES ONLY**. 

- This is not investment advice
- You may lose money by investing in securities
- Past performance does not guarantee future results
- The creator(s) bear no liability for any financial losses

**Always consult a licensed financial professional before making investment decisions.**

[Read Full Disclaimer →](docs/SEN2NAL_LEGAL_DISCLAIMER.md)

---

## 🎯 What is Sen2Nal?

Sen2Nal is a stock sentiment analysis platform that combines:

1. **NLP Sentiment Analysis** - Using FinBERT to analyze news and social media
2. **Calendar Pattern Recognition** - Historical seasonal patterns from trading experience
3. **Transparent Signal Generation** - Explainable signals with SHAP
4. **Live Research Experiment** - Sen2Nal vs ChatGPT vs Gemini vs Grok

### Key Features

| Feature | Description |
|---------|-------------|
| 📊 **Dashboard** | Top 10 stocks by market cap with daily sentiment scores |
| 🔍 **Search** | Analyze any S&P 500 stock |
| 🌡️ **Fear & Greed** | Market-wide sentiment indicator |
| ⚡ **Conflict Detection** | Highlights when NLP and Calendar disagree |
| 📈 **Momentum Tracking** | Sentiment change over time |
| 🏭 **Sector View** | Aggregated sentiment by industry |
| 🧪 **Live Experiment** | Weekly comparison vs LLM stock picks |
| 📖 **Research Paper** | Transparent methodology documentation |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
│   Alpha Vantage │ Yahoo Finance │ Reddit │ NewsAPI │ Fear/Greed │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AWS CLOUD INFRASTRUCTURE                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    EC2 (t3.medium)                        │  │
│  │  Ingestion → Sentiment → Calendar → Features →            │  │
│  │  Prediction → Experiment → FastAPI                        │  │
│  │                              ↓                            │  │
│  │                       React (Vite) UI                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│          │                                        │              │
│          ▼                                        ▼              │
│  ┌───────────────┐                    ┌───────────────────┐     │
│  │  S3 (Raw Data)│                    │  RDS (PostgreSQL) │     │
│  └───────────────┘                    └───────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- AWS Account (for production)
- API Keys: Alpha Vantage, NewsAPI, Reddit

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/FaisalHanafi98/Sen2Nal.git
cd Sen2Nal

# 2. Install backend dependencies (Poetry)
poetry install

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your API keys (NewsAPI, Reddit, Alpha Vantage)

# 4. Start PostgreSQL (Docker)
docker-compose up -d postgres

# 5. Run database migrations
poetry run alembic upgrade head

# 6. Seed calendar (NYSE + Bursa holidays 2024-2027)
poetry run python scripts/seed_calendar.py

# 7. Start API server
poetry run uvicorn src.api.main:app --reload --port 8000

# 8. Start React frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Access

- **Frontend (Vite dev):** http://localhost:5173
- **API Docs (Swagger):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

> **Verification status**: end-to-end frontend↔backend wiring is **not yet verified** — see [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) KI-008.

---

## 📁 Project Structure

```
sen2nal/
├── src/
│   ├── agents/         # 6 pipeline agents (base + ingestion/sentiment/
│   │                   # calendar/features/prediction/experiment)
│   ├── api/            # FastAPI app + routers (stocks, experiments,
│   │                   # pipeline, alerts)
│   ├── contracts/      # Pydantic data contracts per stage
│   ├── data_quality/   # Stage validator
│   ├── database/       # SQLAlchemy models, Alembic migrations
│   ├── pipeline/       # Runner (orchestrator) + scheduler
│   ├── config.py       # Pydantic Settings
│   └── constants.py    # ALLOWED_TICKERS whitelist
├── frontend/           # React + Vite + TS + Tailwind (NightOps Terminal)
│   └── src/{pages,components,api,hooks,types}
├── tests/              # 13 pytest files (~2.1k LOC)
├── scripts/            # smoke_test, seed_calendar, check_setup,
│                       # check_dependencies
├── infrastructure/     # docker, nginx, deploy-lightsail.sh (UNPROVEN)
├── docs/
│   ├── adr/            # 5 Architecture Decision Records
│   ├── audits/         # CURRENT_SYSTEM_STATE, TEST_EVIDENCE_LOG
│   ├── ai/             # AI_CONTEXT_INDEX (canonical doc map)
│   ├── evidence/       # pipeline + frontend runtime evidence
│   ├── security/       # SECURITY_REVIEW
│   ├── ops/            # PROD_READINESS, ROLLBACK, MONITORING
│   └── KNOWN_ISSUES.md # Active blockers register
└── docker-compose.yml  # 3 services: postgres, app, frontend
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/stocks/top10` | Top 10 stocks with scores |
| GET | `/api/v1/stocks/{ticker}` | Detailed stock analysis |
| GET | `/api/v1/stocks/search?q=` | Search stocks |
| GET | `/api/v1/sectors` | Sector aggregation |
| GET | `/api/v1/market/fear-greed` | Fear & Greed index |
| GET | `/api/v1/experiment` | Experiment results |

[Full API Reference →](docs/SEN2NAL_API_REFERENCE.md)

---

## 📊 Signal Interpretation

| Signal | Combined Score | Interpretation |
|--------|---------------|----------------|
| 🟢 **STRONG BUY** | > 0.70 | Both NLP and Calendar strongly positive |
| 🟢 **BUY** | 0.55 - 0.70 | Positive sentiment and/or favorable patterns |
| 🟡 **HOLD** | 0.45 - 0.55 | Neutral or mixed signals |
| 🔴 **AVOID** | < 0.45 | Negative sentiment and/or unfavorable patterns |

**Remember:** These signals are for informational purposes only and are NOT investment advice.

---

## 🧪 The Experiment

Sen2Nal includes a live 8-week experiment comparing stock picks:

| Method | How Picks Are Made |
|--------|-------------------|
| **Sen2Nal** | Top 3 stocks by combined score (>0.6) |
| **ChatGPT** | GPT-4 with standardized prompt |
| **Gemini** | Gemini Pro with same prompt |
| **Grok** | Grok with same prompt |

**Protocol:**
- **Entry:** Monday market open
- **Exit:** Friday market close
- **Holding Period:** 5 trading days
- **Picks:** 3 stocks per method per week

Results are tracked and published transparently, including weeks where Sen2Nal underperforms.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Language | Python 3.11 | Core development |
| API | FastAPI | REST API with auto-docs |
| Frontend | React 18 + Vite + TypeScript + Tailwind | NightOps Terminal UI |
| NLP | FinBERT | Financial sentiment |
| ML | XGBoost | Directional prediction |
| Explainability | SHAP | Feature importance |
| Database | PostgreSQL | Structured storage |
| Object Storage | AWS S3 | Raw data lake |
| Compute | AWS EC2 | Application hosting |
| Scheduling | APScheduler | Daily pipeline |

---

## 📈 Development Phases

| Phase | Duration | Focus |
|-------|----------|-------|
| **Phase 0** | Week 1 | AWS setup, project scaffold |
| **Phase 1** | Week 2-3 | Data pipeline, ingestion |
| **Phase 2** | Week 3-4 | Scoring engine, features |
| **Phase 3** | Week 4-5 | API & Dashboard (Beta) |
| **Phase 4** | Week 5-8 | Experiment, polish |

**Target:** Beta in 4 weeks, Full release in 8 weeks

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [PRD](docs/SEN2NAL_PRD.md) | Product Requirements Document |
| [Technical Architecture](docs/SEN2NAL_TECHNICAL_ARCHITECTURE.md) | System design and algorithms |
| [Database Schema](docs/SEN2NAL_DATABASE_SCHEMA.md) | PostgreSQL schema |
| [API Reference](docs/SEN2NAL_API_REFERENCE.md) | Endpoint documentation |
| [Development Setup](docs/SEN2NAL_DEVELOPMENT_SETUP.md) | Local development guide |
| [Deployment Guide](docs/SEN2NAL_DEPLOYMENT_GUIDE.md) | AWS deployment |
| [Legal Disclaimer](docs/SEN2NAL_LEGAL_DISCLAIMER.md) | Terms and liability |
| [Future Features](docs/SEN2NAL_FUTURE_FEATURES.md) | Roadmap (KIV) |

---

## 🎯 Portfolio Objectives

This project demonstrates skills across multiple data roles:

### Data Analyst
- Exploratory data analysis
- Calendar pattern discovery
- Data quality assessment
- Business rule definition

### Data Engineer
- ETL pipeline design
- AWS infrastructure
- API integration
- Scheduling and orchestration

### Data Scientist
- NLP model integration
- Feature engineering
- Model training (XGBoost)
- Explainability (SHAP)

---

## 👤 Author

**Mohamad Faisal Bin Mohd Hanafi**

- Data Science Graduate, IIUM (CGPA 3.72, Gold Medal)
- Application Development Associate, Accenture Technology Malaysia
- AWS Solutions Architect Associate (In Progress)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Final Reminder

**This project is for educational and portfolio demonstration purposes.**

- NOT financial advice
- NOT a recommendation to buy or sell securities
- Past performance does NOT guarantee future results
- The creator bears NO LIABILITY for financial losses

**Always do your own research and consult a licensed financial professional.**
