<!-- GENERATED from core@77f11d8 - edit in core/, then: python core/tools/ai.py sync -->

# Sen2Nal - instructions for AI agents

Read the [workspace standards](../../standards/README.md) once before working.
Shared policies live there; project facts and exceptions follow below.
This shared mode requires the surrounding Development workspace.

Stack rules: [python](../../core/rules/stacks/python.md). Read when relevant.

Stack rules: [react](../../core/rules/stacks/react.md). Read when relevant.

## Project facts

For a request to research or discover this folder, resume prior work, or move to
a new workstation, start with [SESSION_MIGRATION_PROMPT.md](SESSION_MIGRATION_PROMPT.md).
Follow its read-only discovery pass before summarising the project or proposing work.

Six-agent sequential ML pipeline: FinBERT sentiment (VADER fallback) + calendar
seasonality → XGBoost trading signals in the current implementation.
The owner-defined release is daily US-only sentiment-led research tags, initially
the 50 largest US companies by market capitalisation, one ticker per company,
published at 08:00 America/New_York and supported by roughly one year
of history. This supersedes the earlier weekly decision. It is a supplementary
personal research project, with no stock-price targets or trade execution.
Read CURRENT_MODULE_STATE.md for intended versus implemented behaviour and open
implementation gaps. Evaluation design is deferred while shared improvements are
completed; do not claim the 50-stock release is complete.
Philosophy: "signal over certainty" — surface measurable patterns, decompose
every score transparently. Every prediction output carries **NOT FINANCIAL
ADVICE**.

### Pipeline (src/agents/, sequential, stage-gated)

AG-01 ingestion → AG-02 sentiment → AG-03 calendar → AG-04 features →
AG-05 prediction → AG-06 experiment (weekly LLM comparison; non-critical).
Stages 1–5 are intended to be critical. The current runner halts on an explicit
failed status; broader malformed/partial-status handling still needs proof.
All five declare stage names, but currently only Calendar overrides record
extraction for Pydantic validation. A stage name alone is not contract enforcement.
`DataContractViolation` is available; completing the other boundaries is pending.

### Decided — do not re-ask

- Streamlit is dead; the frontend is React (Vite + Tailwind, "NightOps Terminal").
- Walk-forward validation strictly (ADR-005): 252-day train, 21-day test.
- Tests run against PostgreSQL only; SQLite divergence unacceptable.
- Model persistence: joblib to Docker volume for MVP; S3 later.
- Current code has 10 MVP tickers in `ALLOWED_TICKERS` (src/constants.py); the
  chosen market-cap universe is not yet implemented. Dated membership, rebalancing
  and share-class choice still need implementation rules before evaluation.
- Existing calendars contain NYSE and Bursa records; new release scope is US-only.
- Docker is off-limits locally. Do not run Docker/Compose commands or edit its files.

### Commands

Use the verified Python 3.11 environment and project setup guide. Local tests
need synthetic configuration; PostgreSQL integration requires the separate
`SEN2NAL_TEST_DATABASE_URL` and an authorised disposable local database.
The app's `DATABASE_URL` never grants test reset permission. No seed, pipeline,
scheduler, model download or exposed API launch follows from reading this guide.

### Gates and security

Required gates: coverage ≥40% (Wave 1; 80% end target), mypy and ruff, and verified
contracts at stage boundaries. These are requirements, not a claim all pass.
`POST /pipeline/run` requires `X-Api-Key`
when `PIPELINE_API_KEY` is set; ticker whitelist enforced at the API; never
return synthetic data from API responses.

### External data limits

Verify current provider quotas, rights and exact model-artifact licence before
calls or redistribution. Existing configuration values are not free usage grants.
No paid external calls or private-data uploads. ADRs live in `docs/adr/`.

## Synced skills

On-demand skills in `.claude/skills/`: python, backend, tdd, security-review, systematic-debugging, code-commenting, verification-before-completion.
Trust their trigger descriptions; don't preload them.
