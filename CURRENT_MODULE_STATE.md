# CURRENT_MODULE_STATE.md

> Living engineering state file. Update at every module boundary.
> Last updated: 2026-07-04 (E0.M2 merged)

---

Current Programme:
Sen2Nal Architecture Refactor & Reorganisation (pre-expansion hardening)

Current Wave:
Wave 0 — Verification Baseline

Current Epic:
E0 — Verification Baseline

Current Module:
E0.M2 — Test Evidence Baseline (COMPLETE; next is E0.M3)

Status:
E0.M2 MERGED. PR #2 squash-merged to main (49a0d4e, 2026-07-04). CI green (lint-and-test pass 2m32s).

Module completion: 100% (E0.M2)
Wave 0 completion: 67% (2 of 3 modules: E0.M1, E0.M2 done; E0.M3 remaining)
Overall programme: ~5% (2 of 37 modules)

---

Completed (E0.M1 — Restore Execution Environment):
- Poetry virtualenv created and bound to Python 3.11.9 (host default is 3.14.6 — KI-004).
- Full dependency set installed from committed poetry.lock (torch, transformers 4.57.3,
  xgboost 2.1.4, fastapi, sqlalchemy, etc.).
- SEN2NAL_DEVELOPMENT_SETUP.md §2.0 added: verified no-Docker local setup path.
- Local test run captured: 124 passed, 42 skipped, 0 failed (54.9s).
- PR #1 squash-merged to main (6efc43d). CI green.

Completed (E0.M2 — Test Evidence Baseline):
- docs/audits/TEST_EVIDENCE_LOG.md created: records pass/fail of all 166 tests.
- CI evidence (PG-backed): 166 passed, 0 failed, 0 skipped, 61.34% coverage, 8.17s.
  ruff check passed, mypy "Success: no issues found in 35 source files".
  GitHub Actions run 28694643277, PostgreSQL 15-alpine, Python 3.11.15.
- Local evidence (no-DB): 124 passed, 42 skipped, 0 failed, 54.9s.
- All 166 per-test results recorded with file, class, method, and PASSED status.
- KI-001 RESOLVED.
- PR #2 squash-merged to main (49a0d4e). CI green.

Remaining (this module):
- NONE. Module fully closed.

Blocked:
- E0.M3 (next) is partially blocked by the Docker constraint for the full PostgreSQL
  path; runs via mocked externals + CI Postgres instead.

Regression Risk:
None. E0.M2 was docs-only (1 file, 436 insertions, 0 deletions). No source/config/schema touched.

Next Action:
Await owner authorisation for E0.M3 — E2E Pipeline Harness (the next and final module
in Wave 0). Spec: docs/plans/EXECUTION_PLAN_v1.md §9, Epic E0. Branch convention:
conventional branch from main. Commit message SOP: docs/COMMIT_MESSAGE_SOP.md.
Full execution plan: docs/plans/EXECUTION_PLAN_v1.md (37 modules, 10 epics, 5 waves).

Quality Gate:
PASSED for E0.M2 —
  [x] ruff/format: n/a (docs only)
  [x] mypy: n/a (docs only)
  [x] build: verified in E0.M1 (poetry install exit 0)
  [x] tests: n/a (this module IS the test record; CI ran full suite green on PR #2)
  [x] docs: docs/audits/TEST_EVIDENCE_LOG.md created in same commit
  [x] scope: one file, one commit, one PR
  [x] owner approval / merge: DONE (PR #2 merged 2026-07-04, CI green)

---

Constraints in force:
- Docker is OFF-LIMITS (owner instruction, 2026-07-04). No docker/compose files or
  commands until lifted. Affects E1.M2, E2.M4, E9.M2, E9.M3 and the full-DB path of E0.M3.
- One PR = one module. Commit -> test -> verify -> merge, sequentially.
- Change control: discoveries are recorded, never implemented in-module.

Approved decisions:
- D1 Bursa: decide at E8.M2 (recommendation: state honestly / defer to Horizon 2 Stage 4).
- D2 SHAP: rename to feature_contributions (owner approved).
- D3 walk-forward metrics: store in pipeline_runs.result_json (owner approved).
- D4 coverage ratchet target: TBD at E9.M4 (55 or 60).
- D5 news provider: decide before Horizon 2 Stage 1.
