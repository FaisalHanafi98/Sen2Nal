# Sen2Nal — DE Infrastructure Upgrades Implementation Plan

> **SOP Classification**: TIER 3 (Complex) — New files, multi-directory changes
> **Validation Required**: Full 8-actor before merge
> **Model**: Opus (planning) → Sonnet (implementation)

---

## Critical Assessment: What the Prompt Asks vs What the Project Needs

### Current Reality Check

| Fact | Implication |
|------|-------------|
| Core pipeline = 0% implemented | No data flows between agents yet |
| Tests = empty (only conftest.py fixtures) | CI will pass trivially |
| FastAPI = 1 health endpoint | Docker container does almost nothing |
| Streamlit = placeholder page | Dashboard container is ceremony |
| Phase 5.5.2 smoke test = not yet completed | Stack not validated |
| Great Expectations validates data at scale | No data exists to validate |

### Recommendation: Reorder and Modify

The prompt says "execute in order 1-5". I recommend a different order based on dependency analysis and value-at-this-stage:

| Priority | Task | Rationale |
|----------|------|-----------|
| **1st** | TASK 5: ADRs | Zero risk, zero deps, pure documentation of decisions already made |
| **2nd** | TASK 4: Data Contracts | Foundational — defines agent interfaces BEFORE building agents |
| **3rd** | TASK 1: CI Pipeline | Quality gates, even with thin tests. Ruff + mypy find real issues. |
| **4th** | TASK 2: Docker Multi-Service | Infrastructure readiness for future dev |
| **5th** | TASK 3: Data Quality | **MODIFY** — Replace Great Expectations with lightweight Pydantic-based validation |

---

## TASK 5 → Do First: Architectural Decision Records

**Effort**: Low | **Risk**: None | **Value**: High (portfolio, interviews, methodology clarity)

### Files to Create

```
docs/adr/
├── README.md           # ADR index + template
├── ADR-001-postgresql-star-schema.md
├── ADR-002-finbert-over-gpt4.md
├── ADR-003-xgboost-over-lstm.md
├── ADR-004-batch-over-realtime.md
└── ADR-005-walk-forward-validation.md
```

### Template (Michael Nygard format)

```markdown
# ADR-NNN: Title

**Status**: Accepted
**Date**: 2026-02-18
**Context**: [Business/technical context]
**Decision**: [What we chose]
**Alternatives Considered**: [What we didn't choose + why]
**Consequences**: [Trade-offs accepted]
```

### Content Sources

Each ADR pulls from existing project documentation:
- ADR-001 → SEN2NAL_DATABASE_SCHEMA.md + models.py
- ADR-002 → Research KB Source #12 (FinBERT 88% F1), cost analysis
- ADR-003 → Research KB Source #18 (XGBoost 90%+), SHAP requirement
- ADR-004 → SEN2NAL_TECHNICAL_ARCHITECTURE.md, business case
- ADR-005 → Research KB Source #7 (lookahead bias prevention)

### Validation (Lightweight)

- PM: Documents rationale for stakeholders ✓
- Portfolio: Interview-ready architectural thinking ✓

---

## TASK 4 → Do Second: Data Contracts (Pydantic Schemas)

**Effort**: Medium | **Risk**: Low | **Value**: Very High (foundational for all future agents)

### Files to Create

```
src/contracts/
├── __init__.py
├── base.py              # Base contract, DataContractViolation exception
├── ingestion.py         # IngestionOutput
├── sentiment.py         # SentimentOutput
├── calendar.py          # CalendarOutput
├── features.py          # FeatureOutput
└── prediction.py        # PredictionOutput
```

### Schema Definitions (derived from SEN2NAL_AGENT_PROMPTS.md)

```python
# ingestion.py
class IngestionOutput(BaseModel):
    source: Literal["alpha_vantage", "newsapi", "reddit", "yahoo", "finviz"]
    raw_text: str                     # headline or post body
    ticker_mentions: list[str]        # extracted tickers
    published_at: datetime | None     # original publish time
    fetched_at: datetime              # when we fetched it
    external_id: str | None           # source's article/post ID
    content_hash: str                 # SHA256 for dedup

# sentiment.py
class SentimentOutput(BaseModel):
    ticker: str
    sentiment_score: float            # [-1, 1]
    confidence: float                 # [0, 1]
    source_count: int
    model_used: Literal["finbert", "vader"]
    processing_timestamp: datetime

# calendar.py
class CalendarOutput(BaseModel):
    ticker: str
    date: date
    holiday_decay: float              # [0, 1]
    day_of_week_effect: float         # [-1, 1]
    earnings_proximity: int | None    # days until earnings, None if >30
    trading_day_of_month: int
    calendar_score: float             # [-1, 1] composite

# features.py
class FeatureOutput(BaseModel):
    ticker: str
    date: date
    feature_vector: dict[str, float]  # named features
    feature_timestamp: datetime
    data_completeness: float          # [0, 1]
    shap_values: dict[str, float]     # feature contributions

# prediction.py
class PredictionOutput(BaseModel):
    ticker: str
    date: date
    direction: Literal[0, 1]          # 0=bearish, 1=bullish
    probability: float                # [0, 1]
    confidence: Literal["high", "medium", "low"]
    top_features: list[tuple[str, float]]  # SHAP contributions
    model_version: str
    shap_json: dict[str, float]
```

### Key Design Decisions

1. **Pydantic v2** (already in project) — use `model_validator` for range checks
2. **Strict mode** — reject extra fields to catch bugs early
3. **DataContractViolation** — custom exception raised at agent boundaries
4. **Validators**: sentiment_score in [-1, 1], confidence in [0, 1], etc.
5. **Batch variants**: `IngestionBatch`, `SentimentBatch` for list processing

### Validation (Standard)

- Architect: Matches 7-agent pipeline architecture ✓
- QA: Contracts are inherently testable (Pydantic validates at instantiation) ✓
- Backend: Type-safe interfaces prevent data corruption ✓

---

## TASK 1 → Do Third: GitHub Actions CI Pipeline

**Effort**: Low | **Risk**: Low | **Value**: Medium (quality gates from day 1)

### Files to Create/Modify

```
.github/
└── workflows/
    └── ci.yml

README.md  # Add CI badge
```

### CI Pipeline Design

```yaml
name: Sen2Nal CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: sen2nal_test
          POSTGRES_USER: sen2nal_user
          POSTGRES_PASSWORD: sen2nal_password
        ports: ["5432:5432"]
        options: --health-cmd pg_isready ...
    steps:
      - Checkout
      - Setup Python 3.11
      - Install Poetry
      - poetry install
      - ruff check .
      - mypy src/ --ignore-missing-imports
      - pytest --cov=src --cov-report=xml
      - Upload coverage artifact
```

### Key Decisions

- **Python 3.11** in CI (matches pyproject.toml `^3.11`, NOT user's local 3.14)
- **PostgreSQL service** in CI for integration test readiness
- **No torch/transformers install** in CI initially (too heavy, ~2GB). Add later when ML tests exist.
- **Ruff + mypy** will catch real issues even without tests
- **Coverage artifact** uploaded (not published to Codecov yet — add later)

### Honest Assessment

With empty tests, CI will:
- ✅ Catch ruff linting violations (real value)
- ✅ Catch mypy type errors (real value)
- ⚠️ Show 0% coverage (expected, not useful yet)
- ⚠️ Pass trivially on pytest (no tests to run)

Value increases as tests are added in future phases.

---

## TASK 2 → Do Fourth: Multi-Service Docker Compose

**Effort**: Medium | **Risk**: Low | **Value**: Medium (infrastructure readiness)

### Files to Create/Modify

```
Dockerfile              # FastAPI service
Dockerfile.streamlit    # Dashboard service
.dockerignore           # Exclude unnecessary files
docker-compose.yml      # Updated with app + dashboard services
```

### Dockerfile (FastAPI)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install poetry && poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-interaction
COPY src/ ./src/
COPY alembic.ini ./
EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile.streamlit

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install poetry && poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-interaction
COPY src/ ./src/
EXPOSE 8501
CMD ["streamlit", "run", "src/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### docker-compose.yml Updates

Add two new services to existing file:
- `app` (FastAPI) — depends_on: postgres (healthy)
- `dashboard` (Streamlit) — depends_on: app

Keep existing `postgres` and `pgadmin` services unchanged.

### .dockerignore

```
.git
.venv
__pycache__
*.pyc
.env
.env.*
logs/
htmlcov/
.pytest_cache
.mypy_cache
.ruff_cache
node_modules
*.egg-info
```

### Key Decisions

- **Python 3.11-slim** in Docker (stability > bleeding edge)
- **No ML model baking** into images (FinBERT downloads at runtime, ~400MB)
- **Multi-stage builds** NOT needed yet (app is small)
- **poetry.lock committed** for reproducible builds (note: currently in .gitignore — needs fix)

### ⚠️ Issue Found: poetry.lock in .gitignore

The `.gitignore` excludes `poetry.lock`. For Docker builds and reproducible CI, this should be committed. This needs to be addressed before Docker builds work reliably.

---

## TASK 3 → Modified: Data Quality (Pydantic-Based, NOT Great Expectations)

**Effort**: Low | **Risk**: None | **Value**: Medium (ready when pipeline exists)

### Why NOT Great Expectations

| Concern | Detail |
|---------|--------|
| **Weight** | GE installs 100+ transitive deps (~500MB) |
| **Premature** | Pipeline stages don't exist — no data to validate |
| **Overlap** | TASK 4 contracts already validate schemas via Pydantic |
| **Complexity** | GE requires datasource config, checkpoints, stores — overkill for 0% pipeline |
| **When it makes sense** | When you have production data flowing and need statistical checks (distribution drift, freshness, volume anomalies) |

### What to Do Instead

Create a lightweight validation layer using the TASK 4 contracts:

```
src/data_quality/
├── __init__.py
└── validator.py    # validate_stage() using Pydantic contracts
```

```python
# validator.py
from src.contracts.base import DataContractViolation

def validate_stage(stage: str, data: list[dict]) -> ValidationResult:
    """Validate data between pipeline stages using Pydantic contracts."""
    contract = STAGE_CONTRACTS[stage]  # maps stage name → Pydantic model
    errors = []
    for i, record in enumerate(data):
        try:
            contract.model_validate(record)
        except ValidationError as e:
            errors.append(StageError(index=i, errors=e.errors()))
    return ValidationResult(stage=stage, total=len(data), errors=errors)
```

### Future: When to Add Great Expectations

Add GE when ALL of these are true:
- [ ] AG-01 (Ingestion) produces real data
- [ ] AG-02 (Sentiment) processes real articles
- [ ] Database has >1000 rows of real data
- [ ] You need statistical checks (distribution drift, freshness monitoring)

Estimated: Phase 6+ (multi-stock + calendar), not Phase 5.5.

---

## Execution Plan

### Session Sequencing

| Session | Tasks | Est. Files | Prerequisite |
|---------|-------|------------|--------------|
| **A (this session)** | Complete smoke test first, then TASK 5 (ADRs) | 7 new files | None |
| **B** | TASK 4 (Contracts) + TASK 3 (Validator) | 8 new files | ADRs done |
| **C** | TASK 1 (CI) + TASK 2 (Docker) | 6 new/modified files | Contracts done |

### Why This Order

1. **Smoke test first** — validates that the stack actually works before adding infrastructure on top
2. **ADRs** — documents WHY decisions were made (zero risk, immediate portfolio value)
3. **Contracts** — defines WHAT data flows between agents (foundational for all future work)
4. **CI + Docker** — establishes HOW code is validated and deployed (infrastructure layer)
5. **Data quality** — validates data WHEN it flows (deferred until pipeline exists)

### Dependency Graph

```
Smoke Test (Phase 5.5.2)
    ↓
ADRs (TASK 5) ← no deps
    ↓
Contracts (TASK 4) ← ADRs document the "why" behind contract shapes
    ↓
Data Quality Validator (TASK 3 modified) ← uses TASK 4 contracts
    ↓
CI Pipeline (TASK 1) ← needs contracts to have something meaningful to lint/type-check
    ↓
Docker (TASK 2) ← needs CI to validate builds
```

---

## Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| poetry.lock in .gitignore | HIGH for Docker/CI | Remove from .gitignore, commit poetry.lock |
| Python 3.14 local vs 3.11 Docker/CI | MEDIUM | Pin Docker/CI to 3.11, document 3.14 local as dev convenience |
| torch/transformers too heavy for CI | MEDIUM | Skip ML deps in CI until ML tests exist |
| Empty tests = trivial CI | LOW | Ruff + mypy still catch real issues; tests come in Phase 5.5.3 |
| GE overkill at this stage | LOW | Replaced with Pydantic-based validation (TASK 3 modified) |
| DB migration UUID vs Integer mismatch | MEDIUM | Fix in separate PR before contracts reference models |

---

## 8-Actor Quick Validation (for this plan)

```
ACTOR VALIDATION:
- [x] PM: DE infrastructure supports all 7 agents, aligns with roadmap
- [x] Architect: Contracts match agent prompts, CI/Docker follow standard patterns
- [x] Backend: Pydantic validation at boundaries, PostgreSQL in CI
- [x] ML: FinBERT/XGBoost not in CI yet (too heavy), documented in ADRs
- [x] QA: CI establishes quality gates, contracts are inherently testable
- [x] DevOps: Docker multi-service, CI pipeline, reproducible builds
- [x] Legal: No PII, financial disclaimers in ADRs, "NOT FINANCIAL ADVICE"
- [x] Portfolio: ADRs are interview gold, CI badge signals professionalism
```
