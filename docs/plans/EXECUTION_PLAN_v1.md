# SEN2NAL — EXECUTION PLAN v1
## Master Implementation Specification: Refactor & Reorganisation Programme

> **Document status**: AUTHORITATIVE. This is the complete externalisation of the execution
> plan approved by the owner on 2026-07-03/04. It supersedes any partial copies in chat
> transcripts or handover notes. If this document and a conversation transcript disagree,
> this document wins.
>
> **Provenance**: Derived from two completed studies performed against commit `c9acb31`:
> (1) Architecture Maturity & Scalability Audit (10 phases); (2) Market Universe Feasibility
> Study (10 phases). Both were read-only analyses; their load-bearing findings are
> reproduced in §6 with file:line evidence anchors so this document stands alone.
>
> **Version**: 1.2 (v1.0 = plan as approved; v1.1 = export updated for Docker constraint
> and E0.M1 completion; v1.2 = post-merge update: PR #1 merged, handover docs + commit SOP
> committed, C4 updated to reference docs/COMMIT_MESSAGE_SOP.md, B1/B7 resolved)
> **Date**: 2026-07-04
> **Owner**: Faisal (FaisalHanafi98)
> **Companion files**: `CURRENT_MODULE_STATE.md` (living status),
> `docs/handover/HANDOVER_2026-07-04.md` (session handover)

---

## 1. EXECUTIVE OVERVIEW

Sen2Nal is a 6-agent sequential ML pipeline (FinBERT sentiment + calendar signals →
XGBoost predictions → weekly AI-vs-AI experiment) with a FastAPI backend, PostgreSQL star
schema, and a React 19 dashboard. Two comprehensive studies concluded:

- The **architecture skeleton is production-grade in miniature** (stage-gated pipeline,
  properly indexed star schema, PostgreSQL-backed tests, CI, ADR discipline).
- The **scientific core and deployment path are prototype-grade** (ML label leakage,
  fake walk-forward, fake SHAP, vacuous contract enforcement, two production first-boot
  breakers, biased experiment).
- The **documentation actively misrepresents which is which** (~45% of ~10,000 doc lines
  describe a superseded or never-built system; the three entry documents each contain
  materially false claims).

This programme converts 61 study recommendations into **10 epics / 37 modules / 5 waves**,
estimated **25–35 focused engineering days**. Universe expansion (10 → 500 tickers) is
**Horizon 2** — out of scope until this programme's exit gate passes, because scaling an
invalid signal industrialises noise.

**Execution discipline** (owner-mandated): one module = one branch = one PR = one merge,
strictly sequential (commit → test → verify → merge → next). **Docker is OFF-LIMITS**
until the owner lifts the constraint (§5.1).

**Current status at export time**: E0.M1 COMPLETE (PR #1 open). Next module: E0.M2.
See §21.

---

## 2. ENGINEERING OBJECTIVES

1. **Make the flagship claims true or retract them**: contract-enforced pipeline,
   walk-forward-validated predictions, fair AI-vs-AI experiment, SHAP explainability.
2. **Make first-boot production deployment survivable**: migrations complete, credentials
   not clobbered, model artifacts persistent. (Partially Docker-blocked; see §5.1.)
3. **Establish verification before claims**: captured test evidence, an E2E harness, and
   CI gates that prevent recurrence of each defect class.
4. **Reduce the claims-vs-code gap to zero** in the entry documents (README, CLAUDE.md,
   Known Issues register).
5. **Remove dead weight and duplication** (~22 dead config/constants, 6 unused
   dependencies, duplicated holiday logic, triplicated feature-vector construction).
6. **Leave the codebase gated**: coverage ratchet raised, migration drift check in CI,
   permanent leakage-regression test, frontend CI job.
7. **Unblock Horizon 2** (S&P 500 expansion) as a formally gated follow-on.

Non-objectives: new features, universe expansion, streaming/real-time processing,
multi-tenancy, queue infrastructure (explicitly premature — §9 E-notes and §18).

---

## 3. ARCHITECTURAL PRINCIPLES

1. **Nothing moves until the test baseline exists** (Wave 0). Before this programme, no
   captured pytest or E2E evidence existed (KI-001/KI-009), so regressions were
   indistinguishable from pre-existing defects.
2. **Mechanical refactors before semantic changes.** Behavior-preserving extractions land
   first with golden-snapshot tests; behavior changes (ML target fix) land on the single
   consolidated code path afterwards. Never combine both in one diff.
3. **One high-risk module in flight at a time.** Six modules are high-risk; no wave has
   more than two, never concurrent.
4. **Evidence over assertion.** Every acceptance criterion produces a captured artifact
   (test output, EXPLAIN plan, boot log) recorded in `docs/audits/TEST_EVIDENCE_LOG.md`.
5. **Change control is absolute.** Discoveries are recorded (§17), never absorbed into
   the current module. The audit showed unwired ceremony and scope drift are existing
   failure patterns; this plan must not add to them.
6. **Preserve the correct decisions.** ADR-001 (star schema), ADR-002 (FinBERT+VADER),
   ADR-003 (XGBoost), ADR-004 (daily batch) survive at every scale contemplated. Only
   ADR-005's *implementation* is wrong; its *specification* is the target.
7. **Proportionate tooling.** Solo project: one-off measured benchmarks, not a perf lab;
   in-process TTL caches, not Redis; a worker container, not Celery.

---

## 4. OVERALL REFACTORING STRATEGY

Five waves. Wave 0 builds the measuring instruments. Wave 1 fixes data-layer integrity
and documentation truth in parallel (docs have zero code risk). Wave 2 fixes pipeline
reliability and performs mechanical hygiene. Wave 3 is the ML core — the highest-risk,
strictly sequential wave. Wave 4 hardens the API surface, security, and operations, and
certifies the whole programme with a coverage ratchet. An exit review re-scores the
audit scorecard and formally unblocks Horizon 2.

Per-module workflow (owner-mandated):
```
branch → implement → local gates → commit → push → PR → CI verify → owner merge → next
```

---

## 5. STANDING CONSTRAINTS & APPROVED DECISIONS

### 5.1 Constraints in force

| # | Constraint | Effect |
|---|---|---|
| C1 | **Docker OFF-LIMITS** (owner, 2026-07-04, host Docker issue) | No docker/compose file edits, no docker commands. **Docker-blocked modules**: E1.M2 (can edit files but cannot boot-verify — split acceptance, see spec), E2.M4 (volume mounts deferred), E9.M2, E9.M3 (deferred entirely), E0.M3 full-DB path (use mocked externals + CI Postgres). Re-plan acceptance when lifted. |
| C2 | One PR = one module; strictly sequential; owner merges | No bundling; no parallel PRs |
| C3 | Change control: record discoveries, never implement in-module | Discovery ledger = §17 + E8.M6 |
| C4 | Commit format per `docs/COMMIT_MESSAGE_SOP.md` (structured `Type(Scope): Title.` with Project/Date/Task/Verified-that sections and `[Assisted by AI, reviewed manually by Faisal]` footer); explicit file staging; never `--no-verify`; never `git add -A` | Replaces the prior `Co-Authored-By` convention from 2026-07-04 onward |
| C5 | Always run via `poetry run` (env = Python 3.11.9; host default is 3.14) | KI-004 |
| C6 | No new features, no tickers added, no universe expansion during this programme | Horizon 2 gated |

### 5.2 Decisions (owner approved 2026-07-04 unless noted)

| ID | Decision | Status | Rationale / alternatives |
|---|---|---|---|
| D1 | Bursa Malaysia scope | **OPEN** — decide at E8.M2 | Code has zero Bursa tickers; only holiday data exists (and is wrongly blended into all tickers). Options: (a) docs say "US top-10 today, Bursa planned (Horizon 2 Stage 4)" — recommended, truthful; (b) drop the claim. Cross-project note: RinggitSense is documented as consuming Sen2Nal data. |
| D2 | Fake SHAP | **APPROVED: rename** to `feature_contributions` | Real `shap` blocked by MSVC build tools on the dev host (commented out in pyproject.toml:29). Alternative (optional `shap` extra) rejected for now; may revisit post-programme. |
| D3 | Walk-forward metrics storage | **APPROVED: `pipeline_runs.result_json`** | Lighter than a new table; a `fact_model_metrics` table remains the escalation path if metrics need querying. |
| D4 | Coverage ratchet target | **OPEN** — decide at E9.M4 (55 vs 60) | Set after Waves 1–3 land their tests. |
| D5 | News provider for Horizon 2 | **OPEN** — decide before Horizon 2 Stage 1 | Recommendation: Finnhub-class per-symbol news (free tier 60/min covers 500 symbols); NewsAPI free tier (100 req/day) is a dead end beyond ~90 tickers. |
| D6 | Ticker-mention storage (E1.M4) | **DECIDED in plan: association tables** over JSONB+GIN | Relational, indexable, testable; removes the broken-`contains` bug class entirely rather than patching it. |
| D7 | Background pipeline execution (E3.M1) | **DECIDED: sync `def` task** (Starlette threadpool) + run guard | One-line fix vs process-worker redesign; worker extraction is E9.M3 (Docker-blocked, later). |
| D8 | Long-term architecture | **DECIDED: parametrized modular monolith** with separated batch worker | Queue/worker-pool (Celery+Redis) rejected as premature below ~1,000 tickers — would repeat the ceremony-before-need pattern. ADR-004's anti-streaming reasoning stands. |
| D9 | Test database policy | **INHERITED: PostgreSQL only**, no SQLite | Existing project decision; conftest already implements it. |

---

## 6. GROUNDING FINDINGS (evidence anchors — verify before relying on any)

The five most consequential defects (all have owning modules):

1. **ML label leakage**: `src/agents/prediction.py:104-125` — same-row `daily_return` is
   both a feature in X and the source of target y (`1 if daily_return > 0`); comment says
   "next-day" but no shift exists. → E2.M1.
2. **Fake walk-forward**: `prediction.py:60-64` truncates to last 252 *rows* (not days;
   rows are interleaved across tickers, so 252 rows ≈ 25 days at 10 tickers) and fits
   once; no test window, no metrics. ADR-005 specifies rolling 252/21-day folds. → E2.M2.
3. **Prod first-boot breakers**: (a) `infrastructure/postgres/init.sql:8` runs
   `ALTER USER sen2nal_user WITH PASSWORD 'sen2nal_password'` and is mounted in
   `docker-compose.prod.yml` — clobbers `${DB_PASSWORD}` on first init → E1.M2;
   (b) migration `src/database/migrations/versions/001_initial_schema.py` creates 9
   tables — `pipeline_runs`/`pipeline_logs` missing → `POST /pipeline/run` crashes on a
   migrated DB; tests hide it via `Base.metadata.create_all` in `tests/conftest.py` → E1.M1/M3.
4. **Vacuous contracts**: only `CalendarAgent` implements `_validation_records()`
   (`src/agents/calendar.py:167`); the base-class default (`src/agents/base.py:39-45`)
   silently skips the other four stages. Contract tests use a synthetic
   `FakeValidatedAgent`, masking this. CLAUDE.md claims "all 5 enforce". → E3.M3.
5. **Event-loop-blocking trigger**: `src/api/routers/pipeline.py` —
   `_run_pipeline_background` is `async def` but calls the fully synchronous pipeline;
   async background tasks run on the event loop → the entire API freezes for the run
   duration. → E3.M1.

Additional catalogued defects (owning modules in §7):
- Experiment bias: `src/agents/experiment.py:253-262` — `_get_latest_price` returns 0.0
  for un-priced tickers; LLMs pick from full S&P 500 but only 10 tickers have prices →
  LLM returns recorded as 0.0. → E4.M1.
- Sentiment backlog: `src/agents/sentiment.py:193,218` — fixed `limit(500)` per run, no
  drain loop. FinBERT confidence computed then discarded (no staging column). → E3.M2 (+B4).
- Suspected broken query: `src/agents/features.py:160-184` —
  `tickers_mentioned.contains([ticker])` on a generic `JSON` column renders as a string
  LIKE on PostgreSQL (non-JSONB) — likely errors or matches nothing; never executed E2E
  (KI-009). → E1.M4.
- Calendar signal is ticker-invariant (`src/agents/calendar.py:177-208`); "earnings
  proximity" hardcodes the 15th of Jan/Apr/Jul/Oct and ignores its ticker argument
  (`calendar.py:234-248`); US + Malaysian holidays blended for ALL tickers
  (`calendar.py:218-223`). → honest re-scoping in E8.M2 + Horizon 2 Stage 4.
- Holiday logic duplicated wholesale between `src/agents/calendar.py:19-125` and
  `scripts/seed_calendar.py` (two Easter algorithms, two MY-holiday tables). → E5.M1.
- Feature vector hand-built three times in `prediction.py` (`_build_dataset`, `_predict`,
  `_fallback_predictions`). → E5.M2.
- Dead surface (grep-verified): ~11 settings (`src/config.py`: `secret_key`, AWS quartet,
  `alpha_vantage_api_key`, 3 rate limits, `conflict_threshold` (ignored by
  `features.py:116` which hardcodes 0.1), `calendar_lookback_months`, 2 feature flags)
  and ~11 constants (`src/constants.py`: `FEAR_GREED_THRESHOLDS`, `GICS_SECTORS`,
  `DataSource`, `Direction`, `PipelineStatus`, `FINBERT_LABEL_MAP`, `FINBERT_LABELS`,
  `PIPELINE_RUN_HOUR/MINUTE`, `DEFAULT_PAGE_SIZE`, `MAX_PAGE_SIZE`, `MAX_HISTORY_DAYS`,
  `EXPERIMENT_TOTAL_WEEKS`, `SIGNAL_WARNING`, rate-limit defaults); 6 unused deps
  (`aiohttp`, `boto3`, `spacy`, `playwright`, `jupyter`, plus black+isort redundant with
  ruff). **Exception: `tenacity` is unused but KEPT — E3.M4 uses it.** → E5.M3/M5.
- Import side effects: `src/config.py:190` runs `setup_logging()` at import (creates
  `logs/`, attaches root handlers); `src/database/connection.py:17` creates the engine at
  import. → E5.M4 (logging only; engine deferred = B5).
- `/alerts` (`src/api/routers/alerts.py`): unbounded history scan, latent 500 on NULL
  `combined_score` in message f-strings. → E6.M1.
- `/pipeline/status` (`pipeline.py`): 7× `COUNT(*)` polled every 30s; hardcodes a 5-stage
  list that doesn't match the 6 real agents (frontend mirrors it in
  `frontend/src/lib/constants.ts` `PIPELINE_STAGES`). → E6.M2.
- `get_stocks` (`src/api/routers/stocks.py`): `response.headers[...]` placed BEFORE the
  docstring (docstring becomes inert); no Pydantic response models anywhere; `limit`
  capped `le=50`. → E6.M3 (cap raise is Horizon 2).
- Frontend truthfulness: `USE_MOCK = import.meta.env.VITE_USE_MOCK_DATA !== 'false'`
  (mock is the DEFAULT) with **no visual mock badge anywhere**; `Dashboard.tsx` hardcodes
  fake KPI trends (`trend={{ value: 2.5, label: 'vs last week' }}`); history chart
  hardcodes AAPL. → E6.M4.
- Security: `pipeline_api_key` default-open (endpoint unprotected when unset); dev CORS
  `*`; nginx missing HSTS/CSP; npm audit 21 moderate + 7 high (KI-010). → E7.
- Docs: README links 7 non-existent paths (`docs/audits/`, `docs/ai/`, `docs/ops/`,
  `docs/SEN2NAL_*` — those files live at repo root, and `SEN2NAL_DEPLOYMENT_GUIDE.md`
  never existed), MIT badge with no LICENSE file; `AGENTS.md` is a byte-duplicate of
  `CLAUDE.md` except one word (KI-007's claimed resolution was lost with an orphaned git
  worktree — commits `31c439b`/`9d0bc62` salvaged only KNOWN_ISSUES.md and README.md);
  `PLAN.md` describes a greenfield state ("0% implemented") long superseded;
  `SEN2NAL_TECHNICAL_ARCHITECTURE.md` (1,488 ln) describes a layered/Streamlit/
  CloudFormation design that was never built this way; `SEN2NAL_AGENT_PROMPTS.md`
  specifies 7 agents vs 6 implemented (AG-06 Experiment has no prompt; Agents 6–7
  obsolete); `SEN2NAL_API_REFERENCE.md` documents 13 endpoints with near-zero overlap
  with the real surface (`/stocks`, `/stocks/history`, `/stocks/fear-greed`,
  `/stocks/sectors`, `/experiments`, `/experiments/summary`, `/pipeline/{status,logs,run}`,
  `/alerts`); deploy script REPO_URL `faisalhanafi/sen2nal` vs actual
  `FaisalHanafi98/Sen2Nal`. → E8.
- Misc code smells: `run_pipeline_async` is not async (`src/pipeline/runner.py:116`);
  SQLite pragma listener is dead code (`connection.py:28-35`); `FactSentiment.topics`
  column written by nothing; `scripts/check_dependencies.py` uses emoji/ANSI that crash
  cp1252 consoles (violates the recorded TESTING_NOTES lesson). → E5.M3/M5.

Genuine strengths to PRESERVE: star schema with composite/partial indexes
(`models.py:188-198`), BaseAgent template, stage gating in `runner.py`, PostgreSQL
rollback-isolated test fixtures (`conftest.py`), whitelist enforcement, disclaimer
compliance (`constants.py:246-268`), react-query parallel fetching (`hooks.ts`).

---

## 7. TRACEABILITY MATRIX (finding / Known Issue → owning module)

| Finding / KI | Module | | Finding / KI | Module |
|---|---|---|---|---|
| KI-001 no test evidence | E0.M2 | | Label leakage / fake walk-forward | E2.M1, E2.M2 |
| KI-002/003/004 env broken | E0.M1 ✅ | | Fake SHAP | E2.M3 |
| KI-009 no E2E run | E0.M3 | | Vacuous contracts (4/5) | E3.M3 |
| KI-016 migration drift | E1.M1, E1.M3 | | Event-loop blocking trigger | E3.M1 |
| init.sql prod password clobber | E1.M2 | | Sentiment backlog cap | E3.M2 |
| JSON `contains` defect | E1.M4 | | No retries (tenacity unused) | E3.M4 |
| KI-012 model persistence | E2.M4 | | Experiment zero-price bias | E4.M1 |
| Holiday logic ×2 | E5.M1 | | Feature-vector built ×3 | E5.M2 |
| Dead settings/constants/deps | E5.M3 | | Import side effects | E5.M4 |
| Tooling overlap, emoji script | E5.M5 | | `/alerts` NULL crash + scan | E6.M1 |
| `/pipeline/status` cost + fake stages | E6.M2 | | No response schemas, docstring bug | E6.M3 |
| Mock unlabeled, fake KPI trends | E6.M4 | | KI-010 npm audit | E7.M1 |
| Default-open pipeline key, CORS, headers | E7.M2 | | KI-005/006/007 stale docs | E8.M1–M3 |
| Obsolete API reference | E8.M4 | | KI-011 rollback/monitoring docs | E8.M5 |
| KI register stale entries | E8.M6 | | No frontend CI | E9.M1 |
| CUDA torch image, no healthchecks | E9.M2 | | Scheduler in API process | E9.M3 |
| KI-013 untested agents, 40% gate | E9.M4 | | KI-008 FE↔BE unverified | E0.M3 + E6.M4 |
| KI-014 placeholder API keys | E0.M3 (mocks) | | KI-015 bundle warning | Horizon 2 (deferred) |
| KI-017 CI badge unverified | E8.M3 | | Bursa claim vs zero Bursa tickers | D1 → E8.M2 |

---

## 8. EPIC REGISTER

| ID | Epic | Modules | Risk profile | Est. effort | Docker-blocked? |
|---|---|---|---|---|---|
| E0 | Verification Baseline | 3 | Low | 2–4 d | M3 partial (full-DB path) |
| E1 | Data Layer Integrity | 4 | Med–High | 3–5 d | M2 boot-verify only |
| E2 | ML Core Validity | 4 | **High** | 5–7 d | M4 volume mounts |
| E3 | Pipeline Reliability & Enforcement | 4 | Med | 3–5 d | No |
| E4 | Experiment Integrity | 1 | Low–Med | 1 d | No |
| E5 | Code Hygiene & Deduplication | 5 | Low–Med | 3–4 d | No |
| E6 | API & Frontend Corrections | 4 | Low–Med | 3–4 d | No |
| E7 | Security & Configuration | 2 | Med | 1–2 d | Partial (nginx verify) |
| E8 | Documentation Consolidation | 6 | None (docs-only) | 3–4 d | No |
| E9 | CI/CD & Deployment Readiness | 4 | Med | 3–5 d | M2, M3 blocked |
| — | **Total** | **37** | | **≈ 25–35 d** | |

---

## 9. COMPLETE MODULE SPECIFICATIONS

### Global defaults (apply to every module unless overridden)

- **Rollback**: one module = one feature branch = one atomic commit group; rollback =
  `git revert` of the group. DB-touching modules additionally ship a tested Alembic
  `downgrade()`.
- **Testing floor**: full existing suite green (current no-DB baseline: 124 passed /
  42 skipped) + the module's new tests + E0.M3 harness green (once it exists) +
  lint/type/build gates (§13).
- **Pre-implementation validation**: capture current behavior BEFORE the first edit —
  test-run output; for behavior-preserving refactors, a golden snapshot.
- **Regression risk default**: Low unless stated.
- **Evidence**: every acceptance criterion produces an artifact recorded in
  `docs/audits/TEST_EVIDENCE_LOG.md`.

---

### EPIC E0 — VERIFICATION BASELINE (blocks all other epics)

#### E0.M1 — Restore Execution Environment ✅ COMPLETE
- **Purpose**: runnable Python 3.11 + Poetry environment with all dependencies; first
  captured local test run. Resolves/mitigates KI-002/003/004 via the no-Docker fallback.
- **Files affected**: `SEN2NAL_DEVELOPMENT_SETUP.md` only (+40 lines: §2.0 verified
  no-Docker path). Environment actions not in diff: `poetry env use` → venv
  `sen2nal-dawZnZaD-py3.11` (Python 3.11.9); `poetry install` from committed lock.
- **Dependencies**: none. **Risk**: none. **Complexity**: low. **Regression risk**: none.
- **Acceptance (MET)**: `poetry run pytest` executes to completion → **124 passed,
  42 skipped, 0 failed (54.9s)**; skips = PostgreSQL-fixture tests by design.
- **Rollback**: revert single commit; env changes host-local, non-destructive.
- **Testing performed**: install exit 0; suite run; env interpreter verified 3.11.9.
- **Perf/maint gain**: n/a / establishes reproducible dev path.
- **Status**: commit `3d2ae7f`, **PR #1 MERGED** (squash `6efc43d` to main,
  2026-07-04, CI green). Discoveries recorded: B2 (pyproject
  legacy `[tool.poetry]` table), B3 (gh keyring token invalid; git push works via
  credential manager).

#### E0.M2 — Test Evidence Baseline  ← NEXT MODULE
- **Purpose**: create the recreated-from-loss `docs/audits/TEST_EVIDENCE_LOG.md`
  recording pass/fail of the full suite. Resolves KI-001 ("every 'implemented but
  unverified' claim has a register entry until evidence is captured").
- **Files affected**: new `docs/audits/TEST_EVIDENCE_LOG.md` (docs only).
- **Dependencies**: E0.M1. **Risk**: low. **Complexity**: low. **Regression risk**: none.
- **Docker note**: full PG-backed local run needs PostgreSQL. Options: (a) native
  PostgreSQL 15 install + `sen2nal_test` DB; (b) **recommended**: capture the CI run from
  PR #1 (CI provisions postgres:15 and runs ruff+mypy+pytest+coverage) as the PG-backed
  evidence, plus the local 124/42 record.
- **Acceptance**: every test's status is on record with date, commit, environment, and
  command; any failures become discovery-log entries, NOT fixes.
- **Testing**: none new (this module IS the test record).
- **Perf/maint gain**: n/a / restores the evidence policy the KI register depends on.

#### E0.M3 — E2E Pipeline Harness
- **Purpose**: a pytest-marked integration test running `run_full_pipeline` on one ticker
  with ALL five external sources mocked (yfinance, NewsAPI, Reddit/PRAW, CNN F&G, LLM
  APIs). Addresses KI-009 (no E2E run ever captured) and KI-014 (keys are placeholders —
  mocks make them unnecessary). Becomes the standing regression instrument.
- **Files affected**: new `tests/test_pipeline_e2e.py` + fixture data; possibly a
  conftest marker registration.
- **Dependencies**: E0.M1; PG required → runs in CI (or native PG if installed).
- **Risk**: low. **Complexity**: medium. **Regression risk**: none (additive test).
- **Acceptance**: harness executes all 6 stages against a migrated-or-created schema and
  asserts row counts in staging + fact tables. **Expected outcome**: likely FAILS at the
  features stage (the `JSON.contains` defect, §6) — that failure is a DELIVERABLE
  confirming E1.M4's priority; record it, do NOT fix it here (change control).
- **Testing**: the module is a test. Manual: run once with `-m e2e` locally (DB tests
  skip without PG; assert in CI).
- **Perf/maint gain**: n/a / every later module gains an end-to-end tripwire.

---

### EPIC E1 — DATA LAYER INTEGRITY

#### E1.M1 — Migration 002: Pipeline Tables
- **Purpose**: add `pipeline_runs` + `pipeline_logs` DDL missing from migration 001, so
  `POST /pipeline/run` works on a migrated database (currently crashes; KI-016 class).
- **Files affected**: new `src/database/migrations/versions/002_pipeline_tables.py`.
- **Dependencies**: E0. **Risk**: low (additive DDL). **Complexity**: low.
- **Acceptance**: fresh DB via `alembic upgrade head` matches `Base.metadata`
  (`alembic check` clean); `POST /pipeline/run` succeeds against a MIGRATED (not
  `create_all`) database; `downgrade()` tested.
- **Rollback**: `alembic downgrade -1` + revert commit.
- **Testing**: migration up/down test; the migrated-DB trigger test (may live here or in
  E1.M3's fixture).
- **Perf/maint gain**: none / removes a whole "works in tests, breaks in prod" class.

#### E1.M2 — Split Dev/Prod DB Init  ⚠ DOCKER-BLOCKED (verification only)
- **Purpose**: remove the `ALTER USER … PASSWORD 'sen2nal_password'` and test-DB creation
  from the production bootstrap path (`infrastructure/postgres/init.sql` is mounted in
  BOTH compose files → prod first boot clobbers `${DB_PASSWORD}`).
- **Files affected**: `infrastructure/postgres/init-dev.sql` (new),
  `infrastructure/postgres/init-prod.sql` (new), `docker-compose.yml`,
  `docker-compose.prod.yml` (mount changes), delete/deprecate old `init.sql`.
- **Dependencies**: E0. **Risk**: MEDIUM (prod bootstrap). **Complexity**: low.
  **Regression risk**: medium — dev onboarding must not break.
- **Docker note (C1)**: compose files are Docker artifacts. UNDER THE CURRENT CONSTRAINT:
  either defer the whole module, or (owner's call) edit files WITHOUT boot verification
  and mark acceptance PARTIAL until Docker returns. **Full acceptance requires**: clean-
  volume prod-compose boot authenticates with `${DB_PASSWORD}`; clean dev boot still
  creates `sen2nal_test`. Both drills evidence-logged.
- **Rollback**: revert compose mounts (retain old file until wave exit).
- **Perf/maint gain**: none / closes a security hole + first-boot outage.

#### E1.M3 — CI Migration Gate
- **Purpose**: prevent recurrence of schema drift: CI runs `alembic upgrade head` +
  `alembic check`; one integration fixture converts from `create_all` to migrations.
- **Files affected**: `.github/workflows/ci.yml`, `tests/conftest.py` (add a
  migrated-schema fixture path; keep the fast `create_all` fixture for unit tests).
- **Dependencies**: E1.M1. **Risk**: low. **Complexity**: low-medium.
- **Acceptance**: CI fails when models and migrations diverge — verified by a deliberate
  scratch-branch divergence experiment (do not merge the experiment).
- **Testing**: the CI run is the test; local `alembic check` clean.
- **Perf/maint gain**: none / drift becomes impossible to merge.

#### E1.M4 — Ticker-Mention Storage Rework  ★ HIGH RISK
- **Purpose**: fix the suspected-broken, non-sargable
  `tickers_mentioned.contains([ticker])` (features agent) — the only superlinear query in
  the system and a likely live bug on PostgreSQL. Per D6: association tables.
- **Files affected**: `src/database/models.py` (new `StgNewsTicker`, `StgRedditTicker`
  models or equivalent), new migration `003_mention_tables.py` (+ backfill from existing
  JSON arrays), `src/agents/ingestion.py` (write mentions), `src/agents/features.py`
  (query rewrite).
- **Dependencies**: E0.M3 (harness proves the fix end-to-end), E1.M1.
- **Risk**: HIGH (schema + two agents in the data path). **Complexity**: medium-high.
  **Regression risk**: medium-high.
- **Acceptance**: E0.M3 harness aggregates NON-ZERO sentiment for seeded mentions
  (previously failing stage now green); unit tests for mention writes/reads; `EXPLAIN`
  shows index scan (artifact logged); backfill verified against seeded legacy JSON rows;
  `downgrade()` tested.
- **Rollback**: `alembic downgrade` + revert; old JSON columns retained (dual-write not
  required — cutover is atomic within the pipeline's batch cadence).
- **Testing**: unit (mention CRUD), integration (harness), performance (EXPLAIN + timing
  note), migration up/down.
- **Perf gain**: features-stage query cost becomes independent of staging-table growth
  (the audit modeled 15–30+ min at 500 tickers → sub-minute). **Maint gain**: removes a
  bug class; mentions become queryable/aggregatable.

---

### EPIC E2 — ML CORE VALIDITY  ★ HIGHEST-RISK EPIC (TIER 3 per root SOP: plan approval + full 8-actor validation before merge)

#### E2.M1 — Target Correctness (label leakage)  ★ HIGH RISK
- **Purpose**: make predictions forward-looking: target = t+1 (or t+5, decide in-module
  and document) forward return via lagged join; same-row `daily_return` removed from X or
  lagged. Fixes the audit's #1 finding.
- **Files affected**: `src/agents/prediction.py` (dataset builder only — the vector
  builder itself was consolidated by E5.M2 first).
- **Dependencies**: **E5.M2 MUST land first** (mechanical extraction before semantic
  change), E0.M3. **Risk**: HIGH — every prediction changes, by design.
  **Complexity**: medium. **Regression risk**: high (mitigated by golden separation).
- **Acceptance**: (a) unit test on a synthetic frame proving `y_t` derives from
  `return_{t+1}`; (b) **permanent leakage-regression test** — a model trained with
  shuffled-future targets must score ≈ chance (this test never leaves the suite);
  (c) harness green; (d) model version bumped to `xgb-v2.0` so old/new predictions are
  distinguishable in `fact_predictions.model_version`.
- **Rollback**: revert; version tag isolates any persisted predictions.
- **Testing**: unit + leakage guard + harness; no perf tests needed (training on ≤252
  samples is milliseconds).
- **Perf gain**: none. **Maint gain**: the model's outputs become scientifically
  meaningful — the programme's core deliverable.

#### E2.M2 — True Walk-Forward Evaluation  ★ HIGH RISK
- **Purpose**: implement ADR-005 as specified: rolling folds, 252 trading-DAY train
  window / 21-day test window (fixing the rows-vs-days conflation), per-fold metrics
  (accuracy, precision; extendable) persisted per D3 into `pipeline_runs.result_json`.
- **Files affected**: `src/agents/prediction.py`; `docs/adr/ADR-005-*.md` (status update
  to Implemented + commit SHA).
- **Dependencies**: E2.M1. **Risk**: medium-high. **Complexity**: medium-high.
- **Acceptance**: metrics artifact produced per run; unit tests assert no test-period
  data appears in any fold's training window (temporal boundary test); dataset query
  pushes windowing to SQL (no more load-all-then-slice); ADR-005 updated.
- **Rollback**: revert; result_json is additive.
- **Testing**: unit (fold boundaries, window arithmetic in days not rows), harness.
- **Perf gain**: dataset load bounded (currently loads ALL history then slices).
  **Maint gain**: reported metrics become trustworthy; monthly-retrain design realizable.

#### E2.M3 — Explainability Honesty
- **Purpose**: per D2, rename the `importance × value` output from "SHAP" to
  `feature_contributions` everywhere; ensure no doc or column comment claims SHAP.
- **Files affected**: `src/agents/prediction.py`; `src/database/models.py`
  (`feature_importance` column comment); `CLAUDE.md`; any ADR/doc references (grep-driven
  list at implementation time).
- **Dependencies**: E2.M2. **Risk**: low. **Complexity**: low.
- **Acceptance**: repo-wide grep — "SHAP" appears only in (a) archived docs with
  superseded banners, (b) honest statements that SHAP is NOT implemented / future work.
- **Testing**: existing suite; grep artifact logged.
- **Perf/maint gain**: none / claims-vs-code gap closed for explainability.

#### E2.M4 — Model Artifact Persistence  ⚠ PARTIALLY DOCKER-BLOCKED
- **Purpose**: model survives container recreation (KI-012). `MODEL_DIR` setting replaces
  hardcoded relative `Path("models")` (`prediction.py:23-24`); named volumes for models +
  HF cache in both compose files.
- **Files affected**: `src/config.py`, `src/agents/prediction.py`,
  `docker-compose.yml`, `docker-compose.prod.yml`.
- **Dependencies**: none within wave (parallel-safe). **Risk**: low. **Complexity**: low.
- **Docker note (C1)**: the config/code half (MODEL_DIR env) is implementable and
  locally testable NOW; the compose-volume half is Docker-blocked. Either split the
  module (code now, volumes later) or defer whole — owner's call at execution time.
  Acceptance is correspondingly split: (code) unit test that MODEL_DIR env overrides
  path; (volumes, deferred) train → `docker compose down && up` → model loads without
  retrain, evidence-logged.
- **Rollback**: revert; volumes are additive.
- **Perf gain**: removes ~400MB HF re-download per container recreation. **Maint gain**:
  KI-012 closed.

---

### EPIC E3 — PIPELINE RELIABILITY & ENFORCEMENT

#### E3.M1 — Non-Blocking Trigger + Run Guard
- **Purpose**: per D7 — `_run_pipeline_background` becomes sync `def` (Starlette runs
  sync background tasks in a threadpool, not on the event loop); `POST /pipeline/run`
  returns 409 while a run is active (checked via `PipelineRun.status == "running"`).
- **Files affected**: `src/api/routers/pipeline.py`.
- **Dependencies**: E1.M1 (pipeline tables must exist under migrations).
- **Risk**: low (~5-line diff). **Complexity**: low.
- **Acceptance**: integration test — health endpoint answers while a mocked-slow pipeline
  runs; second trigger during a run → 409; stale-"running" rows handled (decide: age
  timeout or manual reset; document choice).
- **Testing**: integration (concurrency), unit (guard logic).
- **Perf gain**: API no longer freezes for the entire pipeline duration (at 10 tickers
  ≈ minutes; would be ~an hour at 500). **Maint gain**: honest execution semantics.

#### E3.M2 — Sentiment Drain Loop
- **Purpose**: replace the single `limit(500)` pass with loop-until-drained (configurable
  batch size, safety max-iterations cap) so processing rate scales with arrival rate.
- **Files affected**: `src/agents/sentiment.py`, `src/config.py` (batch-size setting).
- **Dependencies**: E0. **Risk**: low. **Complexity**: low.
- **Acceptance**: unit test — 1,200 unprocessed fixture rows all processed in one
  `execute()`; max-iteration cap test.
- **Explicitly OUT of scope** (recorded as B4): persisting FinBERT confidence to staging
  (needs a schema change).
- **Perf gain**: prevents unbounded staging backlog (structural at ≥100 tickers).
  **Maint gain**: removes a silent-at-small-scale failure mode.

#### E3.M3 — Contract Enforcement Wiring  ★ HIGH RISK
- **Purpose**: make CLAUDE.md's flagship claim true — implement `_validation_records()`
  for ingestion, sentiment, features, prediction agents against the existing contracts in
  `src/contracts/`. In scope: reconciling contract shapes with actually-persisted shapes
  (e.g., `IngestionOutput` describes an article record, but the agent's result dict
  currently returns counts — agents must expose record lists for validation).
- **Files affected**: `src/agents/ingestion.py`, `sentiment.py`, `features.py`,
  `prediction.py`; possibly `src/contracts/*.py` (shape reconciliation);
  `tests/test_contract_enforcement.py` (real-agent coverage replacing the
  `FakeValidatedAgent`-only tests).
- **Dependencies**: **AFTER E2** (validate corrected outputs, not ones about to change)
  and after E1.M4 (features' records stabilized). **Risk**: MEDIUM-HIGH — introduces a
  new intended failure mode (pipeline halts on violation). **Complexity**: medium-high.
  **Regression risk**: medium.
- **Acceptance**: contract tests exercise REAL agents; E0.M3 harness green WITH
  enforcement active; a deliberately malformed record halts the pipeline in a test;
  CLAUDE.md's contracts claim updated by E8.M2 to match (coordinate).
- **Rollback**: revert; contracts revert to calendar-only (documented state).
- **Perf gain**: negligible cost (Pydantic on batch outputs). **Maint gain**: the
  pipeline's central integrity mechanism actually functions.

#### E3.M4 — Retry/Backoff on External Calls
- **Purpose**: wrap the 5 external fetch paths (prices, news, Reddit, F&G, LLM) with
  `tenacity` (already a dependency, currently unused): 3 attempts, exponential backoff,
  then the existing log-and-continue behavior. No retry on 4xx client errors.
- **Files affected**: `src/agents/ingestion.py`, `src/agents/experiment.py`.
- **Dependencies**: E0. **Risk**: low. **Complexity**: low.
- **Acceptance**: unit tests with fail-twice-succeed-third mocks per path; 4xx-no-retry
  asserted; total retry budget bounded (document worst-case added wall-clock).
- **Perf gain**: reliability under flaky APIs (all 5 sources are flaky). **Maint gain**:
  matches the original agent-prompt spec that was never implemented.

---

### EPIC E4 — EXPERIMENT INTEGRITY

#### E4.M1 — Fair-Comparison Guards
- **Purpose**: (a) constrain the LLM prompt (`src/constants.py:228`
  `LLM_EXPERIMENT_PROMPT`) to the priced universe; (b) validate parsed picks against
  `dim_stocks`; (c) refuse to record entries with entry price 0.0. Prompt change =
  protocol change → explicit prompt version bump (the `llm_prompt` column already
  snapshots per-run text, giving natural versioning).
- **Files affected**: `src/constants.py`, `src/agents/experiment.py`.
- **Dependencies**: E0. **Risk**: low-medium (public-facing experiment protocol).
  **Complexity**: low.
- **Acceptance**: unit tests — out-of-universe pick → rejected/re-picked path; zero-price
  entry writes NO row; prompt version visible in stored record; `EXPERIMENT_DISCLAIMER`
  untouched (compliance).
- **Note**: Horizon 2's universe expansion largely dissolves this bias naturally (S&P 500
  coverage prices most LLM picks); this module makes the CURRENT experiment honest.
- **Perf/maint gain**: none / the project's headline comparison becomes methodologically
  defensible.

---

### EPIC E5 — CODE HYGIENE & DEDUPLICATION

#### E5.M1 — Single Market-Calendar Module
- **Purpose**: one source of truth for US/MY holiday logic. Currently duplicated
  wholesale: `src/agents/calendar.py:19-125` AND `scripts/seed_calendar.py` each carry
  their own Easter algorithm, NYSE rules, and 4-year Malaysian holiday table.
- **Files affected**: new `src/market_calendar.py` (name at implementer's discretion);
  `src/agents/calendar.py`; `scripts/seed_calendar.py`.
- **Dependencies**: E0. **Risk**: MEDIUM (core signal path + seed path).
  **Complexity**: medium.
- **Pre-implementation validation (MANDATORY)**: golden snapshot — full holiday sets
  2024–2027 captured from BOTH current implementations BEFORE editing; post-refactor
  output must be identical. Any divergence between the two existing copies is itself a
  bug discovery (record, decide which is correct, document).
- **Acceptance**: golden tests pass; both consumers import the shared module; duplicate
  code deleted; existing calendar tests (24) green.
- **Maint gain**: highest in the epic — the domain's core data has one home.

#### E5.M2 — Shared Feature-Vector Builder
- **Purpose**: one function replaces the three hand-built 13-element vectors in
  `prediction.py` (`FEATURE_COLS` order must be provably consistent).
  Behavior-preserving.
- **Files affected**: `src/agents/prediction.py`.
- **Dependencies**: E0. **Sequencing: MUST precede E2.M1** (principle #2).
- **Risk**: low-medium. **Complexity**: low.
- **Acceptance**: golden vector-equality test old-vs-new on fixture rows (all three call
  sites); suite green.
- **Maint gain**: a silent train/inference feature-order divergence becomes impossible.

#### E5.M3 — Dead Weight Removal
- **Purpose**: delete the grep-verified unused surface (§6 list): ~11 settings, ~11
  constants, dependencies `aiohttp`/`boto3`/`spacy`/`playwright`/`jupyter`, SQLite pragma
  listener, `run_pipeline_async`, `.memsearch/`, stale `.env.example` blocks (Streamlit,
  AWS). **KEEP `tenacity`** (E3.M4). `settings.conflict_threshold`: wire into
  `features.py` OR delete — decide in-module, document (B6).
- **Files affected**: `src/config.py`, `src/constants.py`, `pyproject.toml`,
  `src/database/connection.py`, `src/pipeline/runner.py`, `.env.example`, `.memsearch/`.
- **Dependencies**: E0; coordinate with E3.M4 (tenacity) and E6 (any constant an E6
  module decides to USE instead — check before deleting `DEFAULT_PAGE_SIZE` etc.).
- **Risk**: low but wide. **Complexity**: low.
- **Acceptance**: suite green; fresh `poetry lock` + install exit 0; repo-wide grep shows
  zero references to every removed name (artifact logged).
- **Maint gain**: ~1,000 lines of misleading surface removed.

#### E5.M4 — Import Side-Effect Removal (logging)
- **Purpose**: `setup_logging()` no longer runs on `import src.config`
  (`config.py:190`); explicit calls in the three entrypoints (API lifespan, runner
  `__main__`, scheduler start). Engine-at-import (`connection.py:17`) is EXPLICITLY
  DEFERRED (B5) — larger blast radius than warranted now.
- **Files affected**: `src/config.py`, `src/api/main.py`, `src/pipeline/runner.py`,
  `src/pipeline/scheduler.py`.
- **Dependencies**: E0. **Risk**: medium (logging behavior). **Complexity**: low.
- **Acceptance**: importing `src.config` in a clean interpreter creates no `logs/` dir
  and attaches no handlers (unit-testable); all three entrypoints still emit logs
  (manual verification, evidence-logged).
- **Maint gain**: tests and scripts stop spraying log files as an import side effect.

#### E5.M5 — Tooling Consolidation
- **Purpose**: `ruff format` replaces black+isort (remove both deps + their pyproject
  sections; add ruff format/isort config); `scripts/check_dependencies.py` made
  ASCII-safe (the recorded cp1252 lesson from TESTING_NOTES.md); optional pre-commit
  config.
- **Files affected**: `pyproject.toml`, `scripts/check_dependencies.py`, optionally
  `.pre-commit-config.yaml`, CI (if format check added).
- **Dependencies**: E5.M3 (dependency removal coordination). **Risk**: trivial.
- **CRITICAL RULE**: the repo-wide reformat diff must be a **formatting-only commit with
  zero logic changes**, isolated for reviewability (may be a second commit in the same
  PR, clearly labeled).
- **Acceptance**: `ruff format --check` clean; suite green; script runs on a cp1252
  console without crash.

---

### EPIC E6 — API & FRONTEND CORRECTIONS

#### E6.M1 — `/alerts` Hardening
- **Purpose**: latest-date scoping + date filter (currently scans ALL history — "active"
  alerts include years-old rows and the query grows forever); NULL-safe message
  formatting (latent 500: `f"{float(sent.combined_score):.2f}"` on NULL).
- **Files affected**: `src/api/routers/alerts.py`; new `tests/test_alerts_router.py`.
- **Dependencies**: E0. **Risk**: low. **Complexity**: low.
- **Acceptance**: unit tests incl. NULL-score row (no 500) and old-history exclusion;
  response shape unchanged for the frontend.
- **Perf gain**: query cost bounded by latest date instead of total history.

#### E6.M2 — `/pipeline/status` Truth + Cost
- **Purpose**: derive the stage list from `PipelineRun.result_json` (6 real agent stages)
  instead of the hardcoded 5-name list; short-TTL in-process cache for the 7 `COUNT(*)`
  queries (frontend polls every 30s); align frontend `PIPELINE_STAGES`.
- **Files affected**: `src/api/routers/pipeline.py`; `frontend/src/lib/constants.ts`;
  `frontend/src/components/pipeline/PipelineFlow.tsx`.
- **Dependencies**: E1.M1, E3.M1. **Risk**: low-medium (UI contract — version the
  response shape or change both sides in this one module, which is why FE files are in
  scope). **Complexity**: medium.
- **Acceptance**: FE renders 6 stages from live data; repeated polls within TTL hit cache
  (asserted via query-count spy or timing); mock data updated to match shape.
- **Perf gain**: status endpoint cost independent of table growth.

#### E6.M3 — API Response Contracts
- **Purpose**: Pydantic response models for the 8 endpoints (restores the never-built
  schema layer; prerequisite for E8.M4 doc regeneration); fix the header-before-docstring
  bug in `get_stocks`. **Models describe CURRENT shapes — this is not a redesign.**
- **Files affected**: new `src/api/schemas.py`; `src/api/routers/*.py` (4 files).
- **Dependencies**: E6.M1, E6.M2 (model their final shapes once). **Risk**: medium
  (serialization is regression-prone). **Complexity**: medium.
- **Acceptance**: existing API tests green UNCHANGED (shapes preserved); OpenAPI spec
  diff reviewed and logged; docstring renders in Swagger.
- **Maint gain**: typed API surface; auto-generatable reference.

#### E6.M4 — Frontend Truthfulness
- **Purpose**: (a) visible MOCK-mode badge — mock is currently the DEFAULT
  (`USE_MOCK = env !== 'false'`) and renders fabricated signals with no indicator,
  violating the repo's own no-synthetic-data rule; (b) remove hardcoded KPI trend values
  in `Dashboard.tsx` (compute from data or omit); (c) ticker selector replacing the
  hardcoded-AAPL history fetch in `hooks.ts`.
- **Files affected**: `frontend/src/api/hooks.ts`, `frontend/src/pages/Dashboard.tsx`,
  `frontend/src/components/ui/KpiCard.tsx` (if trend prop handling changes),
  `frontend/src/components/layout/TopBar.tsx` or shell (badge placement).
- **Dependencies**: E0. **Risk**: low. **Complexity**: low-medium.
- **Acceptance**: mock build shows badge; live build shows no fabricated values;
  `tsc -b` + eslint + `npm run build` green; closes the demo-integrity half of KI-008.

---

### EPIC E7 — SECURITY & CONFIGURATION

#### E7.M1 — npm Audit Triage (KI-010)
- **Purpose**: re-run `npm audit` on the current lockfile (the 21 moderate/7 high record
  predates the current dependency set); apply safe fixes; document accepted residual
  risks for E8.M5.
- **Files affected**: `frontend/package.json`, `frontend/package-lock.json`; decision
  record (docs).
- **Dependencies**: E9.M1 (CI job catches breakage — schedule after it exists).
- **Risk**: medium (dependency bumps). **Complexity**: low.
- **Acceptance**: build + FE CI green; audit report before/after logged; unfixable items
  documented with rationale.

#### E7.M2 — Production Security Defaults  ⚠ nginx verify Docker-blocked
- **Purpose**: (a) fail-fast (or loud startup warning — decide in-module) when
  `pipeline_api_key` unset with `environment=production` (currently default-open);
  (b) verify prod CORS origin path (`allowed_hosts` split logic in `main.py`);
  (c) add HSTS + baseline CSP headers to `infrastructure/nginx.conf`.
- **Files affected**: `src/config.py` or `src/api/main.py` (guard), `infrastructure/nginx.conf`.
- **Dependencies**: E0. **Risk**: low-medium (prod-only paths). **Complexity**: low.
- **Docker note**: nginx header verification normally uses a local nginx container →
  blocked; acceptable interim evidence = config-file review + a recorded curl check
  deferred until Docker returns or first deployment.
- **Acceptance**: unit test for the config guard; nginx config change reviewed; deferred
  runtime check recorded in evidence log as pending.

---

### EPIC E8 — DOCUMENTATION CONSOLIDATION (zero code risk; parallel-safe from Wave 1)

#### E8.M1 — Archive Obsolete Artifacts
- **Purpose**: move to `docs/_archive/` with a standard superseded banner (template:
  status, superseded-by, date, why): `PLAN.md`, `SEN2NAL_TECHNICAL_ARCHITECTURE.md`,
  `SEN2NAL_AGENT_PROMPTS.md`, `SEN2NAL_API_REFERENCE.md`; strip CODEX.md to durable rules
  (fold into CLAUDE.md) or archive whole; delete `.memsearch/` stubs (coordinate with
  E5.M3 — whoever runs first).
- **Acceptance**: no un-bannered root doc describes the dead architecture; all inbound
  links updated.

#### E8.M2 — Canonical AI Context
- **Purpose**: correct CLAUDE.md's five false claims — (1) "all 5 agents enforce
  contracts" (state calendar-only until E3.M3 lands, then update again); (2) Bursa
  Malaysia per D1; (3) "Redux" → react-query; (4) SHAP per E2.M3; (5) test/service
  counts (166 tests / 11 files at baseline; compose services 3 + profile-gated pgadmin).
  AGENTS.md becomes a ≤5-line pointer (finishes KI-007 for real this time).
- **Acceptance**: every CLAUDE.md claim traceable to code at the current commit;
  `diff CLAUDE.md AGENTS.md` no longer near-identical. **Timing note**: schedule the
  final pass AFTER E3.M3 to avoid stating a claim twice.

#### E8.M3 — README Repair
- **Purpose**: fix the 7 broken links; add a LICENSE file (MIT, matching pyproject) or
  remove the badge; regenerate the endpoint table from the real surface; make the
  structure section match the actual tree; reconcile the repo-URL mismatch (deploy
  script vs badge — actual remote is `FaisalHanafi98/Sen2Nal`); verify the CI badge
  renders green (KI-017).
- **Acceptance**: zero dead links (link-check artifact); every statement verifiable.

#### E8.M4 — API Reference Regeneration
- **Purpose**: export the live OpenAPI spec (FastAPI serves it at
  `/api/v1/openapi.json`) into a committed reference doc replacing the archived one.
- **Dependencies**: E6.M3 (schemas make it meaningful) — scheduled late (Wave 4).
- **Acceptance**: committed reference matches the served spec (regeneration command
  documented so it stays reproducible).

#### E8.M5 — Ops Documentation (KI-011)
- **Purpose**: rollback procedure, monitoring/logging plan, backup note; folds in
  E7.M1's audit decisions. Docker-blocked items documented as "pending Docker" rather
  than omitted.
- **Acceptance**: an operator could revert a bad deploy following the doc alone.

#### E8.M6 — Known Issues Refresh + Discovery Ledger (OPENS Wave 1, stays open to exit)
- **Purpose**: close resolved KIs with commit SHAs; correct stale premises (KI-007 false
  resolution, KI-008's vite-proxy premise); ADD the standing "Discoveries" section that
  change control (C3) writes into. This module is the programme's ledger — it opens
  early and its final closing commit is part of the exit review.
- **Acceptance**: register accurately reflects reality at each wave exit.

---

### EPIC E9 — CI/CD & DEPLOYMENT READINESS

#### E9.M1 — Frontend CI Job
- **Purpose**: add a CI job: `tsc -b`, eslint, `npm run build`, `npm audit` report
  artifact. The frontend currently has ZERO CI coverage.
- **Files affected**: `.github/workflows/ci.yml`.
- **Dependencies**: E0. **Risk**: low (additive). **Complexity**: low.
- **Acceptance**: job fails on an introduced TS error (scratch verification, not
  merged); green on the real branch.

#### E9.M2 — Image & Runtime Hardening  ⛔ DOCKER-BLOCKED (deferred until C1 lifts)
- **Purpose**: CPU-only torch pin in the image (default Linux resolution pulls CUDA
  builds → multi-GB image); healthchecks for app/frontend in prod compose; log-rotation
  options.
- **Files affected**: `Dockerfile`, `docker-compose.prod.yml`, possibly `pyproject.toml`
  (source-pinned torch) — ALL Docker artifacts.
- **Risk**: medium. **Complexity**: medium.
- **Acceptance (when unblocked)**: image size before/after recorded (target <~2.5GB);
  containers report healthy; FinBERT inference smoke test passes on the CPU wheel.

#### E9.M3 — Scheduler Extraction  ⛔ DOCKER-BLOCKED (deferred until C1 lifts)
- **Purpose**: move APScheduler from the API lifespan (`src/api/main.py:48-53`) to a
  dedicated worker container; API ships `ENABLE_SCHEDULER=false`. The strategic unblock
  for any future API replication (replicas would currently duplicate pipeline runs).
- **Files affected**: new worker entrypoint (e.g. `src/pipeline/worker.py` or compose
  command reusing `scheduler.py`), `docker-compose.prod.yml`, `src/api/main.py`.
- **Dependencies**: E3.M1, E9.M2. **Risk**: medium (deployment topology).
- **Acceptance (when unblocked)**: API container spawns no scheduler thread (log/inspect
  evidence); worker fires the cron (verified with a near-term test cron, evidence-logged).
- **Docker-constraint fallback**: the pure-code half (worker entrypoint + config flag) MAY
  be implemented and unit-tested without Docker if the owner wants partial progress;
  container verification deferred.

#### E9.M4 — Coverage Ratchet + Gap Tests  (MUST BE LAST)
- **Purpose**: raise `--cov-fail-under` from 40 to the D4 target; add any KI-013 test
  files not already created by owning modules (E2 → prediction tests; E1.M4/E0.M3 →
  features coverage; E4 → experiment tests; E6.M1 → alerts tests; this module closes the
  remainder, e.g. `tests/test_features.py` unit gaps). Certifies the programme.
- **Files affected**: `pyproject.toml` (addopts), `ci.yml`, new/extended test files.
- **Dependencies**: ALL prior waves. **Risk**: low. **Complexity**: medium (test writing).
- **Acceptance**: CI green at the new gate; KI-013 closed; final evidence-log entry.

---

## 10. EXECUTION ORDER

```
WAVE 0  ─ E0.M1 ✅ → E0.M2 → E0.M3                    [GATE 0: baseline exists]
WAVE 1  ─ E1.M1 → E1.M3 → E1.M2†  ║  E8.M1 M2 M3 M6 ║  E9.M1
WAVE 2  ─ E3.M1 → E3.M2 → E1.M4* → E3.M4  ║  E5.M1* M3 M4 M5
WAVE 3  ─ E5.M2 → E2.M1* → E2.M2* → E2.M3 → E2.M4† → E4.M1 → E3.M3*
WAVE 4  ─ E6.M1 M2 M3 M4 → E7.M1 M2† → E9.M2⛔ → E9.M3⛔ → E8.M4 M5 → E9.M4
EXIT    ─ re-audit spot check, scorecard delta, discovery triage, Horizon 2 go/no-go

*  = high-risk (max one in flight, never two concurrently)
†  = partially Docker-blocked (split acceptance per spec)
⛔ = fully Docker-blocked (deferred until constraint C1 lifts; slot them at the end of
     Wave 4 or a post-constraint mini-wave — do NOT hold the exit review hostage to
     them; exit review may proceed with them formally deferred)
║  = parallel-safe track (disjoint files)
```

**Ordering rationale (load-bearing choices):**
- E0 first: no baseline → no attributable regressions.
- E1.M1 before E3.M1: the run guard queries `pipeline_runs`.
- E1.M4 after E0.M3: the harness is the instrument that proves the fix.
- E5.M2 before E2.M1: mechanical before semantic (principle #2).
- E3.M3 after E2 and E1.M4: wire validation around final shapes, not twice.
- E6.M3 before E8.M4: schemas before doc regeneration.
- E9.M4 strictly last: the ratchet certifies the finished state.
- Docs parallel from Wave 1: zero code risk; stale docs demonstrably CAUSE code defects
  (KI-005's history), so truth pays earliest.
- No circular dependencies (all edges point forward; parallel tracks touch disjoint files).

---

## 11. INTEGRATION CHECKPOINTS

| Checkpoint | When | Verification |
|---|---|---|
| IC-0 | Wave 0 exit | Suite baseline recorded; harness exists and its failures are catalogued |
| IC-1 | Wave 1 exit | Fresh migrated DB boots the API incl. `POST /pipeline/run`; entry docs truthful; FE CI green |
| IC-2 | Wave 2 exit | Harness green INCLUDING the features stage; API responsive during a pipeline run; golden calendar tests pass |
| IC-3 | Wave 3 exit | Leakage guard green; ADR-005 = Implemented; contracts enforced on real agents; experiment guards active |
| IC-4 | Wave 4 exit | All non-Docker-blocked modules merged; coverage at D4 target; KI register current |
| EXIT | Programme end | Scorecard re-score vs audit (targets: Deployment D→B−*, Documentation D+→B, Testing C+→B); Horizon 2 go/no-go. *Deployment target reduced scope while C1 holds — re-score honestly. |

`main` stays releasable at all times; waves merge only at wave boundaries after the exit
gate (all constituent modules green + harness green).

---

## 12. TESTING STRATEGY

Per-category requirements (each module's spec adds specifics):

| Category | Pre-impl | Unit | Integration | Perf | Regression | Manual | Build | Docs |
|---|---|---|---|---|---|---|---|---|
| Schema/migration (E1.M1,M4) | `alembic check` baseline | up/down | migrated-schema fixture | E1.M4 EXPLAIN | suite+harness | fresh-DB boot | ✔ | schema docs |
| Agent logic (E2.*, E3.M2–M4, E4, E5.M1–M2) | golden snapshots | ✔ new | harness | n/a | suite + **permanent leakage guard** | pipeline CLI vs mocks | ✔ | ADR/CLAUDE |
| API (E3.M1, E6.M1–M3, E7.M2) | capture response shapes | ✔ | TestClient vs migrated DB | E6.M2 latency note | suite | Swagger check | ✔ | API ref |
| Frontend (E6.M4, E9.M1, E7.M1) | current build output | cheap component tests | — | bundle size note | eslint+tsc | visual mock & live | `npm run build` | README |
| Infra (E1.M2, E2.M4, E9.M2–M3) | current behavior | — | — | image size/boot | harness after | **mandatory drills — Docker-blocked → recorded as PENDING** | image builds | ops docs |
| Docs (E8.*) | link-check baseline | — | — | — | — | link check + claim-vs-code audit | — | is the deliverable |

Permanent instruments left behind: E0.M3 harness; E2.M1 leakage guard; E1.M3 migration
gate; E9.M1 FE job; E9.M4 ratchet.

Environment reality: local suite (no PG) = 124 passed / 42 skipped baseline; PG-backed
tests run in CI (postgres:15 service). TDD applies to all new behavior per the root SOP.

---

## 13. QUALITY GATES (every module, in order)

```
Code complete
 → ruff check  +  ruff format --check        (post-E5.M5; before that, black --check)
 → mypy src/
 → build: poetry install exit 0 / npm run build (FE modules)
 → alembic check                              (schema-relevant modules)
 → poetry run pytest  (coverage ≥ current gate: 40% until E9.M4)
 → E0.M3 harness                              (Wave ≥1, once it exists)
 → module acceptance criteria demonstrated → evidence into docs/audits/TEST_EVIDENCE_LOG.md
 → docs touched by the change updated in the SAME branch
 → SOP validation: TIER 2 lightweight, or TIER 3 full 8-actor for E1.M2, E1.M4, E2.*, E3.M3, E9.M3
 → owner approval (feat/fix/refactor always need confirmation per SOP §13.3)
 → merge → next module
```

**Failure protocol**: any red gate stops the line. Diagnose root cause (never retry
blind, never `--no-verify`). Fix exceeds module scope → revert branch to last green,
file the finding in the E8.M6 ledger, re-plan the module. Two consecutive failures on
the same gate → escalate to owner with findings before a third attempt.

---

## 14. CHANGE CONTROL

1. **Module scope is a contract** — the spec's file list is the blast radius; exceptions:
   `TEST_EVIDENCE_LOG.md` and the E8.M6 ledger are always writable.
2. **Discoveries recorded, never absorbed** (ledger entry: what, where, proposed owner
   module or "new", priority).
3. **One module = one branch = one PR**; formatting-only diffs isolated.
4. **No opportunistic improvement** — the audit documented ceremony-before-need and scope
   drift as existing failure patterns.
5. Wave boundaries are merge boundaries; `main` stays releasable.

---

## 15. ROLLBACK STRATEGY

- Default: `git revert` of the module's commit group (modules are atomic by construction).
- Schema modules: tested Alembic `downgrade()` + revert; E1.M4 retains the legacy JSON
  columns through the transition so downgrade loses nothing.
- Behavior-changing ML modules: model artifacts version-tagged (`xgb-v2.0`) so persisted
  predictions from old/new code are distinguishable and old behavior is restorable by
  revert without data ambiguity.
- Deployment topology (E9.M3): compose change is revertible by file; scheduler flag
  (`ENABLE_SCHEDULER`) provides an instant runtime fallback.
- Prod-boot module (E1.M2): old `init.sql` retained until wave exit; mounts revertible.

---

## 16. ROADMAP SUMMARY

| Wave | Modules | Deps | Risk | Key deliverables | Exit criteria |
|---|---|---|---|---|---|
| 0 (2–4 d) | E0.M1✅ M2 M3 | — | Low | Env, evidence log, E2E harness | Baseline recorded; harness failures catalogued |
| 1 (4–6 d) | E1.M1 M3 M2† ∥ E8.M1–M3 M6 ∥ E9.M1 | W0 | Med | Complete migrations + CI gate; safe prod bootstrap (files); truthful entry docs; FE CI | IC-1 |
| 2 (6–9 d) | E3.M1 M2 M4, E1.M4* ∥ E5.M1* M3 M4 M5 | W1 | High | Non-blocking trigger, drain loop, retries, mention-storage fix, single calendar module, dead weight gone | IC-2 |
| 3 (7–10 d) | E5.M2 → E2.M1*–M4 → E4.M1 → E3.M3* | W2 | Highest | Valid ML core, honest explainability, fair experiment, real contract enforcement | IC-3 |
| 4 (6–9 d) | E6.M1–M4, E7.M1–M2, E9.M2⛔ M3⛔, E8.M4 M5 → E9.M4 | W3 | Med | Hardened API/UI/security, regenerated docs, coverage ratchet | IC-4 + EXIT |

Total: ≈ 25–35 focused engineering days (Docker-blocked modules excluded from the
critical path; they append when C1 lifts).

---

## 17. DEFERRED WORK (Discovery Backlog — change-control ledger seed)

| ID | Item | Reason deferred | Priority | Deps | Impact |
|----|------|-----------------|----------|------|--------|
| B1 | Commit this plan file | DONE — committed to main (this document) | — | — | — |
| B2 | Migrate pyproject to PEP 621 `[project]` table (Poetry 2.x deprecation warnings) | Out of E0.M1 scope | Low | E5.M5 | Removes 6 warnings |
| B3 | `gh auth refresh -h github.com` (keyring token invalid; push works via credential manager) | Owner host action | Med | owner | Restores gh automation |
| B4 | Persist FinBERT confidence to staging (currently computed then discarded) | Schema change beyond E3.M2 | Med | E3.M2 | Confidence-weighted aggregation |
| B5 | Engine-created-at-import in `connection.py` | Blast radius vs benefit | Low | E5.M4 | Test isolation |
| B6 | `settings.conflict_threshold` wire-or-delete | Decide in E5.M3 | Low | E5.M3 | Config honesty |
| B7 | Commit handover docs (`CURRENT_MODULE_STATE.md`, `docs/handover/*`) durably | RESOLVED — committed to main at `c1f36ac` alongside `docs/COMMIT_MESSAGE_SOP.md` | — | — | — |
| B8 | `.env.example` dead vars cleanup | Covered by E5.M3 scope | Low | E5.M3 | — |
| B9 | Real `shap` as optional extra (post-D2 revisit) | MSVC constraint; renamed instead | Low | E2.M3 | True SHAP if env allows |
| B10 | Frontend bundle code-split (KI-015: recharts+framer-motion) | Perf, not correctness | Low | Horizon 2 UI work | TTI |
| B11 | Treemap → sector rollup redesign (unreadable ≥100 tickers) | Horizon 2 presentation | Low | Horizon 2 | UX at scale |
| B12 | Stale-"running" PipelineRun recovery policy | Decide within E3.M1 or ledger | Med | E3.M1 | Guard robustness |

---

## 18. FUTURE ROADMAP (Horizon 2+ — GATED on programme exit; do NOT start)

From the feasibility study (its full analysis lives with the owner; operative summary):

- **Stage 1 — 50 tickers** (~1–2 wk): `universes` + `universe_members` tables + S&P
  constituents loader; delete `ALLOWED_TICKERS`/`_STOCK_META` constants in favor of DB;
  provider abstraction + news-source decision (D5); ThreadPool fetching (4–8 workers);
  bulk `yf.download`; `ON CONFLICT` upserts (constraints already exist); `/stocks` cap
  raise + server-side pagination; table sorting.
- **Stage 2 — 100** (~1–2 wk): cashtag-priority + NER ticker matching (S&P 500 contains
  common-word tickers A/T/IT/ALL/SO/COST/LOW — substring matching collapses); TTL caches;
  sector-rollup treemap; run-duration metrics.
- **Stage 3 — S&P 500** (~2–4 wk): cohort checkpoint/resume in `pipeline_runs`;
  scheduler-worker split (E9.M3 foundation); staging retention policy; materialized views
  (`mv_top10_stocks`, `mv_sector_sentiment` — already designed in
  SEN2NAL_DATABASE_SCHEMA.md §5, never built); UI virtualization + search
  (pg_trgm/FTS) + stock detail page; memory plan (FinBERT ~1.2–1.5GB RSS; 8GB box or
  pipeline/API split); explicit global-vs-per-sector model decision.
- **Stage 4 — Multi-market (Bursa)** (~2–3 wk): market/exchange entity (currency,
  timezone, per-market trading calendars — also FIXES the existing US+MY holiday blending
  defect); per-market scheduling; makes the D1 claim true if chosen.
- **Stage 5 — User-defined universes** (~3–6 wk + product decisions): users/auth,
  watchlists, per-user quotas, on-demand backfill; the first stage where queue/worker
  infrastructure (rejected as premature in D8) earns its cost.
- Rate-limit economics: NewsAPI free (100 req/day) hard-blocks ≥~90 tickers at 1
  req/ticker; Finnhub-class per-symbol news is $0 at 500; yfinance viable at 500 only via
  bulk download; licensed EOD feed needed at ~5,000.
- Long-term architecture (D8): parametrized modular monolith + separated batch worker;
  ceiling ~1,000–2,000 tickers on one node.

---

## 19. KNOWN RISKS

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Docker constraint persists → E1.M2/E9.M2/E9.M3 acceptance stuck at PARTIAL | Med | Deployment score can't reach target | Exit review scores honestly with formal deferral; modules pre-specced for fast completion when lifted |
| CI reveals PG-backed failures invisible locally (42 skipped tests never observed passing in-session) | Med | Wave 0/1 rework | E0.M2 captures CI evidence FIRST; failures become scoped discoveries |
| E1.M4 backfill mishandles malformed legacy JSON | Low-Med | Data loss in staging | Backfill is additive (new tables), legacy columns retained; verify counts pre/post |
| E2.M1 changes headline predictions users have seen | Certain (by design) | Perceived regression | Model version tag + honest changelog; the old numbers were invalid |
| E3.M3 contract enforcement halts pipeline on previously-tolerated dirty data | Med | Nightly run failures | Harness + staged rollout (log-only mode first is an allowed in-module option — document if used) |
| gh token stays broken | Low | Manual PR steps | Push works via credential manager; B3 owner action |
| Scope creep via "while I'm in here" fixes | Ever-present | Programme integrity | C3 + §14; reviewer checks file list |
| Solo-maintainer bus factor | — | Continuity | This document + handover pack + evidence log ARE the mitigation |

---

## 20. SUCCESS CRITERIA & DEFINITION OF DONE

**Per module**: all §13 gates green + acceptance artifacts logged + owner merge.
**Per wave**: integration checkpoint (§11) passed; `main` releasable; ledger current.
**Programme (Definition of Done)**:
1. All P0/P1 Known Issues closed with commit SHAs (or formally deferred with owner
   sign-off — currently expected: KI-002 host Docker, Docker-blocked module remainders).
2. The five §6 headline defects fixed and guarded by permanent tests.
3. Zero false claims in README / CLAUDE.md / KNOWN_ISSUES.
4. E2E harness green with contract enforcement active.
5. Coverage gate at D4 target; migration drift structurally impossible to merge.
6. Scorecard re-score: Documentation D+→B, Testing C+→B, Deployment D→B− (or honest
   partial with C1 deferral documented).
7. Horizon 2 formally unblocked at exit review.

---

## 21. CURRENT EXECUTION STATUS (updated 2026-07-04)

- **Done**: E0.M1 (original commit `3d2ae7f`, PR #1 MERGED to main as squash `6efc43d`,
  CI green). Local baseline: 124 passed / 42 skipped / 0 failed. Poetry env
  `sen2nal-dawZnZaD-py3.11` (Python 3.11.9).
- **Process docs committed**: `CURRENT_MODULE_STATE.md`,
  `docs/handover/HANDOVER_2026-07-04.md`, `docs/COMMIT_MESSAGE_SOP.md`, and this file
  committed to main at `c1f36ac` (handover docs + SOP) and this commit (plan).
  B1 and B7 resolved.
- **Next**: **E0.M2** — Test Evidence Baseline (needs explicit owner authorisation to start).
- **Update protocol for this document**: append status changes to §21 and tick modules in
  §9 at every module merge; structural changes to the plan itself require owner approval
  and a version bump.

*End of EXECUTION_PLAN_v1.md — self-verification: 10 epics ✔, 37 modules ✔ (E0:3, E1:4,
E2:4, E3:4, E4:1, E5:5, E6:4, E7:2, E8:6, E9:4), all dependencies ✔, 5 waves + exit ✔,
gates ✔, testing matrix ✔, acceptance criteria per module ✔, decisions D1–D9 ✔,
constraints C1–C6 ✔, backlog B1–B12 ✔, risks ✔, DoD ✔.*
