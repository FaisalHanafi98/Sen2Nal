<!-- GENERATED from core@3b953ef - edit in core/, then: python core/tools/ai.py sync -->

# Sen2Nal - instructions for AI agents

# Constraints

These are the rules that apply to every session. Everything procedural lives in
skills and loads on demand — this file stays small on purpose.

## Git

- Never force-push, hard-reset, or delete branches without an explicit request.
- Never skip hooks (`--no-verify`). If a hook blocks you, fix the cause.
- Stage specific files; no blanket `git add -A` in repos with unrelated changes.
- Commit format: `type(scope): description` — feat, fix, refactor, docs, test, chore.
- Commit when a discrete task completes. Ask before pushing to main/master/dev.

## Secrets and data

- No secrets, credentials, or `.env` files in any commit, ever. The pre-commit
  secret scan is a backstop, not permission to be careless.
- PDPA: no real personal data in code, tests, or fixtures. CREAMS and
  RinggitSense are sensitive; use synthetic data.
- Financial advice output (RinggitSense, Sen2Nal) carries the mandatory
  disclaimers defined in each project's facts.

## Engineering

- Behavior changes need a test that fails first. Run the verification command
  and read its output before claiming anything works.
- Prefer built-in tools and CLIs over MCP when an equivalent exists.
- Keep diffs scoped to the task. No opportunistic refactors or drive-by fixes;
  flag them instead.
- Don't invent facts — especially Malaysian regulations, bank formats, or
  statistics. Say what you don't know.

## Escalation

- Ask before anything destructive, schema-changing, or production-affecting.
- When a task turns out bigger than classified, say so before continuing.

## Python / FastAPI

- Python 3.11+, type hints on public functions, pydantic models at API boundaries.
- Lint with ruff; keep imports explicit; no bare `except`.
- Tests: pytest, written before the implementation for any behavior change.
  Cover the changed behavior meaningfully — coverage % is a floor, not the goal.
- Async for I/O paths in FastAPI; no blocking calls inside async handlers.
- Depth on patterns and testing technique: the `python` skill
  (references/patterns.md and references/testing.md, loaded on demand).

## React / TypeScript

- React 18 + TypeScript, strict mode. Server data through a query library
  (SWR/React Query) — never raw `useEffect` fetching.
- Parallelize independent fetches; no request waterfalls.
- Accessibility before aesthetics: labels, keyboard nav, 4.5:1 contrast,
  44px touch targets. The `ui-accessibility` skill has the full checklist.
- Semantic color tokens, no hardcoded hex in components.
- Depth: `react-ui-patterns` and `frontend-design-aesthetics` skills.

## Project facts

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

## Synced skills

On-demand skills in `.claude/skills/`: python, backend, tdd, security-review, systematic-debugging, code-commenting, verification-before-completion.
Trust their trigger descriptions; don't preload them.
