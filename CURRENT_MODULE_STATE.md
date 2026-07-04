# CURRENT_MODULE_STATE.md

> Living engineering state file. Update at every module boundary.
> Last updated: 2026-07-04 (E0.M3 merged -- Wave 0 complete)

---

Current Programme:
Sen2Nal Architecture Refactor & Reorganisation (pre-expansion hardening)

Current Wave:
Wave 0 — Verification Baseline (COMPLETE)

Current Epic:
E0 — Verification Baseline (COMPLETE)

Current Module:
E0.M3 — E2E Pipeline Harness (COMPLETE; Wave 0 exit gate passed)

Status:
E0.M3 MERGED. PR #3 squash-merged to main (a1085a1, 2026-07-04). CI green
(lint-and-test pass 2m41s). 167 passed, 0 skipped, 68.92% coverage in CI.

Module completion: 100% (E0.M3)
Wave 0 completion: 100% (3 of 3 modules: E0.M1, E0.M2, E0.M3 all done)
Overall programme: ~8% (3 of 37 modules)

---

Completed (E0.M1 — Restore Execution Environment):
- Poetry virtualenv created and bound to Python 3.11.9 (host default is 3.14.6 — KI-004).
- Full dependency set installed from committed poetry.lock.
- SEN2NAL_DEVELOPMENT_SETUP.md §2.0 added: verified no-Docker local setup path.
- PR #1 squash-merged to main (6efc43d). CI green.

Completed (E0.M2 — Test Evidence Baseline):
- docs/audits/TEST_EVIDENCE_LOG.md created: records pass/fail of all 166 tests.
- CI evidence: 166 passed, 61.34% coverage. Local: 124 passed, 42 skipped.
- KI-001 RESOLVED.
- PR #2 squash-merged to main (49a0d4e). CI green.

Completed (E0.M3 — E2E Pipeline Harness):
- tests/test_pipeline_e2e.py created: E2E integration test running run_full_pipeline
  on one ticker (AAPL) with all 5 external sources mocked (yfinance, NewsAPI,
  Reddit/PRAW, CNN F&G, LLM APIs).
- e2e marker registered in pyproject.toml.
- CI: 167 passed (including the E2E test), 0 skipped, 68.92% coverage.
- The E2E test discovered TWO pre-existing defects (recorded, NOT fixed per C3):
  1. numpy type binding: ingestion code passes numpy.float64 to SQLAlchemy;
     psycopg2 raises InvalidSchemaName("schema np does not exist"). Mock uses
     Python native types to bypass. Discovery for E1.M4 or E5.M3 ledger.
  2. Calendar contract mismatch: CalendarOutput.holiday_decay specified as
     [0, 1] but actual value is negative (-0.3 * e^(-n)). CalendarAgent is
     the only agent with _validation_records(), so it is the only one where
     contract enforcement runs. The test handles this gracefully. Discovery
     for E3.M3 ledger.
- KI-009 RESOLVED (E2E run captured). KI-014 addressed (mocks replace placeholder keys).
- PR #3 squash-merged to main (a1085a1). CI green.

Remaining (this module):
- NONE. Module fully closed. Wave 0 complete.

Blocked:
- E1.M2 (Wave 1): partially Docker-blocked (can edit files but cannot boot-verify).
- E9.M2, E9.M3 (Wave 4): fully Docker-blocked.
- E0.M3 full-DB path: resolved via CI PostgreSQL (not blocked).

Regression Risk:
Low. E0.M3 added 1 test file + 1 marker registration. No source code changes.
The E2E test is additive (new test, no existing tests modified).

Next Action:
Wave 0 is complete (IC-0 checkpoint passed). The next module is in Wave 1:
E1.M1 — Migration 002: Pipeline Tables (add pipeline_runs + pipeline_logs DDL
missing from migration 001). This is the first code module in Wave 1.
Await owner authorisation to start Wave 1.

Quality Gate:
PASSED for E0.M3 —
  [x] ruff: clean
  [x] mypy: "Success: no issues found in 35 source files"
  [x] build: poetry install exit 0
  [x] tests: 167 passed in CI (124 local + 43 skipped + E2E test in CI)
  [x] coverage: 68.92% (gate: 40%)
  [x] docs: test docstring documents discoveries
  [x] scope: 2 files (test + pyproject.toml), 3 commits, 1 PR
  [x] owner approval / merge: DONE (PR #3 merged 2026-07-04, CI green)

---

Constraints in force:
- Docker is OFF-LIMITS (owner instruction, 2026-07-04). No docker/compose files or
  commands until lifted. Affects E1.M2, E2.M4, E9.M2, E9.M3.
- One PR = one module. Commit -> test -> verify -> merge, sequentially.
- Change control: discoveries are recorded, never implemented in-module.

Approved decisions:
- D1 Bursa: decide at E8.M2.
- D2 SHAP: rename to feature_contributions (owner approved).
- D3 walk-forward metrics: store in pipeline_runs.result_json (owner approved).
- D4 coverage ratchet target: TBD at E9.M4 (55 or 60).
- D5 news provider: decide before Horizon 2 Stage 1.

Discoveries from E0.M3 (for the E8.M6 discovery ledger):
- D-E0.M3-1: Ingestion code passes numpy.float64 to SQLAlchemy; psycopg2 cannot
  bind numpy types. Pre-existing, never caught because no E2E test existed.
  Proposed owner: E1.M4 or E5.M3.
- D-E0.M3-2: CalendarOutput contract specifies holiday_decay in [0, 1] but the
  actual holiday_decay function returns negative values. CalendarAgent is the
  only agent with _validation_records(). Contract needs fixing or calendar
  math needs adjusting. Proposed owner: E3.M3.
