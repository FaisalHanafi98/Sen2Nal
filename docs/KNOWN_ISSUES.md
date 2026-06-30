# Sen2Nal — Known Issues Register

> **Created**: 2026-05-19
> **Source**: Audit `docs/audits/CURRENT_SYSTEM_STATE.md` §6 Risk Register
> **Policy**: Every "implemented but unverified" claim in the codebase has an entry here until evidence is captured.
> Entries are removed only when test/runtime evidence is committed under `docs/audits/TEST_EVIDENCE_LOG.md` or `docs/evidence/`.

---

## Severity legend

- **P0 — Blocker**: prevents verification, demo, or deployment. Fix first.
- **P1 — High**: corrupts decision-making (stale docs, hidden defects) or risks production safety.
- **P2 — Med**: degrades quality or maintainability; not blocking.
- **P3 — Low**: cosmetic / nice-to-have.

---

## Open issues

### KI-001 (P0) — No captured pytest evidence for current codebase
- **Symptom**: `docs/audits/TEST_EVIDENCE_LOG.md` has never recorded a passing pytest run against the current commit. Last documented attempt (`TESTING_NOTES.md`, `CODEX.md`) explicitly states "Backend pytest coverage gate was not run."
- **Evidence**: commits `6fd7ac9 fix(ci): restore backend verification`, `6f346cc fix(test): align backend contract tests` indicate recent breakage; no local or CI run output committed.
- **Impact**: All claims of working agents/contracts/pipeline are unverified.
- **Fix**: Run pytest in Docker + Poetry, capture full log.
- **Blocked by**: KI-002, KI-003.
- **Owner**: Dev / QA.

### KI-002 (P0) — Docker daemon not running locally
- **Symptom**: `docker info` returns `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine` on the current host.
- **Evidence**: command output 2026-05-19; same blocker noted in `TESTING_NOTES.md` ("PostgreSQL Connection FAIL — Docker Desktop not running").
- **Impact**: No Postgres → no pytest, no Alembic upgrade, no E2E pipeline run.
- **Fix**: Start Docker Desktop on host, OR install local Postgres 15, OR run inside CI.
- **Owner**: Faisal (host environment).

### KI-003 (P0) — Poetry not installed on current host
- **Symptom**: `poetry --version` → `command not found`.
- **Evidence**: shell probe 2026-05-19; `CODEX.md` notes "Poetry was not on PATH."
- **Impact**: Cannot run `poetry install` / `poetry run pytest` / `poetry run alembic`.
- **Fix**: `pip install --user poetry` or pipx, then `poetry env use python3.11`.
- **Owner**: Faisal / Dev.

### KI-004 (P1) — Python 3.14 on host vs 3.11 in `pyproject.toml`
- **Symptom**: Host `python --version` → 3.14.4; project pins 3.11.
- **Evidence**: shell probe; `pyproject.toml`.
- **Impact**: Local Poetry env may resolve to wrong interpreter; FinBERT/torch wheel availability differs across versions.
- **Fix**: Install Python 3.11 and use `poetry env use python3.11`, OR run only in Docker.
- **Owner**: Dev.

### KI-005 (P1) — README.md is stale (still advertises Streamlit)
- **Symptom**: README shows Streamlit badge, includes Streamlit in architecture diagram, in quickstart commands (`streamlit run src/dashboard/app.py`), and in tech-stack table — despite `1a64d22 refactor: remove Streamlit dashboard`.
- **Evidence**: `grep -n -i streamlit README.md` → 5 hits (lines 8, 67, 120, 146, 210).
- **Impact**: Misleads humans and AI agents working from README → hallucinated changes targeting non-existent Streamlit code.
- **Fix**: Replace with React/Vite content. **Resolved in this sprint — see `[PHASE-1]` commits.**
- **Owner**: Doc Lead.

### KI-006 (P1) — PLAN.md baseline is stale and contradictory
- **Symptom**: PLAN.md opens with "Core pipeline = 0% implemented, Tests = empty (only conftest.py fixtures)" — directly contradicted by ~4.8k LOC across `src/` and 13 test files.
- **Evidence**: `PLAN.md` head; `wc -l tests/*.py src/agents/*.py`.
- **Impact**: Anyone (especially AI) using PLAN.md as a starting point will plan for a greenfield project that no longer exists.
- **Fix**: Archive PLAN.md to `docs/_archive/PLAN_v1_pre_react.md` and write a fresh status-aware plan. **Resolved in this sprint — see Phase 1.**
- **Owner**: Doc Lead.

### KI-007 (P1) — CLAUDE.md and AGENTS.md are byte-duplicates
- **Symptom**: Both files are 5437 bytes; `diff CLAUDE.md AGENTS.md` shows only the header word swap.
- **Evidence**: shell `diff` output 2026-05-19.
- **Impact**: Drift inevitable; AI agents reading one will not see fixes applied to the other.
- **Fix**: Designate `CLAUDE.md` canonical; `AGENTS.md` becomes a thin pointer file. Map declared in `docs/ai/AI_CONTEXT_INDEX.md`. **Resolved in this sprint.**
- **Owner**: AI Workflow Auditor.

### KI-008 (P1) — Frontend↔Backend runtime never verified
- **Symptom**: React Dashboard exists but no commit or doc shows it fetching real `/stocks` or `/experiments` data; no proxy / `VITE_API_URL` documented.
- **Evidence**: `CODEX.md` lists "Verify frontend-to-API runtime locally" as pending; no `.env` or proxy entry visible in `frontend/vite.config.ts` (re-verify in Phase 5).
- **Impact**: Demo would fail; dashboard could be decorative.
- **Fix**: Phase 5 of current sprint.
- **Owner**: FE.

### KI-009 (P1) — Pipeline E2E run never captured
- **Symptom**: No log of `python -m src.pipeline.runner` succeeding on a single ticker.
- **Impact**: Cannot claim the 6-agent flow works end-to-end.
- **Fix**: Phase 3 — mock external APIs if needed, capture stage-by-stage output.
- **Owner**: ML / Backend.

### KI-010 (P1) — npm audit findings: 21 moderate, 7 high
- **Symptom**: `CODEX.md` records `npm install` audit results.
- **Impact**: Supply-chain risk before any prod intent.
- **Fix**: Re-run `npm audit`, evaluate `npm audit fix`, lock decisions in `docs/security/SECURITY_REVIEW.md`.
- **Owner**: Sec / FE.

### KI-011 (P1) — No rollback plan, no monitoring/logging plan
- **Symptom**: `docker-compose.prod.yml` and `infrastructure/deploy-lightsail.sh` exist; rollback procedure, healthchecks, log shipping all absent.
- **Impact**: Any production attempt is unrecoverable.
- **Fix**: Phase 6 docs.
- **Owner**: DevOps.

### KI-012 (P2) — Model artifact persistence path unverified
- **Symptom**: `CLAUDE.md` describes "joblib to Docker volume for MVP" but no `MODEL_DIR` env var or volume mount confirmed end-to-end.
- **Fix**: Trace through `src/agents/prediction.py` + compose files; document.
- **Owner**: ML.

### KI-013 (P2) — Modules without dedicated unit tests
- **Symptom**: No `tests/test_features.py`, no `tests/test_prediction.py`, no `tests/test_experiment.py`, no `tests/test_alerts_router.py`.
- **Evidence**: `ls tests/`.
- **Impact**: ML feature math + walk-forward predictions are silent-failure prone.
- **Fix**: Add skeletons during Phase 3.
- **Owner**: QA.

### KI-014 (P2) — External data source keys unknown / placeholder
- **Symptom**: `TESTING_NOTES.md` warns 3 optional API keys are placeholders.
- **Impact**: AG-01 will not produce real data without keys; tests must mock.
- **Fix**: Document required keys; provide mock fixtures.
- **Owner**: Data Eng.

### KI-015 (P2) — Large frontend bundle warning at build
- **Symptom**: `CODEX.md` notes "Frontend build reported a large bundle warning."
- **Impact**: TTI regression; not blocking.
- **Fix**: Code-split Dashboard; lazy-load chart libs.
- **Owner**: FE.

### KI-016 (P2) — Alembic migrations: only `001_initial_schema.py`
- **Symptom**: Single migration file; no incremental migrations as schema evolved with feature commits.
- **Impact**: If models drifted, `alembic upgrade head` may not match `src/database/models.py`.
- **Fix**: `alembic revision --autogenerate --check` in Phase 2.
- **Owner**: Backend.

### KI-017 (P3) — README CI badge points to `FaisalHanafi98/Sen2Nal` — actual status unverified
- **Symptom**: Badge URL embedded; no recent green run linked in any doc.
- **Fix**: Verify after Phase 2.
- **Owner**: Dev.

---

## Closed (this sprint)

_(populate as items resolve; reference commit SHA)_
