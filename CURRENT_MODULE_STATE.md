# CURRENT_MODULE_STATE.md

> Living engineering state file. Update at every module boundary.
> Last updated: 2026-07-04 (E0.M1 merged)

---

Current Programme:
Sen2Nal Architecture Refactor & Reorganisation (pre-expansion hardening)

Current Wave:
Wave 0 — Verification Baseline

Current Epic:
E0 — Verification Baseline

Current Module:
E0.M1 — Restore Execution Environment

Status:
MERGED. PR #1 squash-merged to main (6efc43d, 2026-07-04). CI green (lint-and-test pass).

Module completion: 100%
Wave 0 completion: 33% (1 of 3 modules: E0.M1 done; E0.M2, E0.M3 remaining)
Overall programme: ~3% (1 of 37 modules)

---

Completed (E0.M1):
- Poetry virtualenv created and bound to Python 3.11.9 (host default is 3.14.6 — KI-004).
- Full dependency set installed from committed poetry.lock (torch, transformers 4.57.3,
  xgboost 2.1.4, fastapi, sqlalchemy, etc.).
- SEN2NAL_DEVELOPMENT_SETUP.md §2.0 added: verified no-Docker local setup path.
- Local test run captured: 124 passed, 42 skipped, 0 failed (54.9s).
- Committed (3d2ae7f), pushed, PR #1 created, squash-merged to main (6efc43d).

Remaining (this module):
- NONE. Module fully closed.

Blocked:
- Nothing blocks E0.M1.
- E0.M3 (later) is blocked by the Docker constraint for the *full* PostgreSQL path;
  runs via mocked externals + CI Postgres instead.

Regression Risk:
None. Docs-only diff (+40 lines, 0 deletions). No source/config/schema touched.

Next Action:
Await owner authorisation for E0.M2 — Test Evidence Baseline (the next module in
Wave 0). Branch convention: conventional branch from main (e.g. docs/e0m2-test-evidence).
Commit message SOP: docs/COMMIT_MESSAGE_SOP.md. Full execution plan:
docs/plans/EXECUTION_PLAN_v1.md (37 modules, 10 epics, 5 waves).

Quality Gate:
PASSED for E0.M1 —
  [x] ruff/format: n/a (docs only)
  [x] mypy: n/a (docs only)
  [x] build: poetry install exit 0
  [x] tests: 124 passed / 42 skipped / 0 failed locally; CI runs PG-backed remainder on PR
  [x] docs: SEN2NAL_DEVELOPMENT_SETUP.md updated in same commit
  [x] scope: one module, one commit, one PR
  [x] owner approval / merge: DONE (PR #1 merged 2026-07-04, CI green)

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
