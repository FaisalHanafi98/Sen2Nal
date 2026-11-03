# Sen2Nal test evidence log

Recorded: 4 November 2026, Asia/Kuala_Lumpur. Work order: **SN-BASE only**.
Status: local baseline recorded; integration and release acceptance remain open.
This entry records current observations, not a hosted CI or deployment result.

## Scope and acceptance

The owner selected SN-BASE in this session after supplying the
[project workflow](../../../../workspace/reels-improvement-2026-10-19/implementation/Sen2Nal/00-PROJECT-WORKFLOW.md).
The implementer journey was: identify this checkout and existing runners; inspect
fixture/import effects; exercise the mocked test-database permission boundary;
record fresh safe checks and unavailable verification. Only evidence documentation
is delivered. There are no application, schema, evaluation or dependency changes.

| Acceptance | Evidence / conclusion |
|---|---|
| Identify source and dirty scope | `e6ee318dadfa21d316b1364ecc80c4d864165396`, branch `chore/e0m1-environment-baseline`; initially 26 tracked dirty paths, 4 untracked files, no staged changes |
| Reuse the actual runtime and locks | Existing Python 3.11.9 environment executed successfully; `poetry check --lock` exited 0; sampled installed versions match `poetry.lock` |
| Inspect effects before tests | Fixture, configuration, connection, API lifespan, runner/model loading and test call sites reviewed; controls/exclusions below |
| Exercise allowed/denied resource boundaries | 12 mocked safety cases pass; unset/unsafe URL refusals, unique schema ownership, setup/cleanup failure and routing cases; zero real connections |
| Record runnable gates and limits | Fresh results below; no PostgreSQL, browser or hosted CI claim |
| Preserve existing work and bound recovery | Only this log and `CURRENT_MODULE_STATE.md` are delivery files; initial dirty paths checked by status and SHA-256 after verification |

## Checkout and existing work

The original dirty scope contains shared guide/agent pointers and deleted shared
reference copies, `.cursor/rules/core.mdc`, `.hooks/pre-commit`, `CLAUDE.md`,
`README.md`, `docs/COMMIT_MESSAGE_SOP.md`,
`docs/ai-context/00_PROJECT_SOURCE_OF_TRUTH.md` and
`frontend/src/styles/globals.css`. The four pre-existing untracked files are
`.claude/launch.json`, `.claude/settings.local.json`,
`docs/handover/HANDOVER_2026-07-04.md` and `docs/plans/EXECUTION_PLAN_v1.md`.
Their contents are outside this delivery. No local settings or environment contents
are included in the evidence log.

`git worktree list --porcelain` also registers an OpenCode `swift-tiger` checkout
on `main` at `894ad92`. Its working-tree status check returned
`fatal: this operation must be run in a work tree`; its runtime/dirty state is
unverified. No worktree metadata was repaired or removed. Branch discovery was
local only; remote refs were not refreshed.

| Older plan item | Located evidence | SN-BASE disposition |
|---|---|---|
| E0.M1 environment | Current setup guide plus executable cached environment | Reused; no scaffolding/install |
| E0.M2 test record | `docs/e0m2-test-evidence` at `e227f97f2400f48e8db650831e6f29b7314be6ad` contains `docs/audits/TEST_EVIDENCE_LOG.md` | Historical record exists elsewhere; this entry uses its established path/purpose for fresh evidence, without copying earlier CI claims |
| E0.M3 pipeline harness | `test/e0m3-e2e-harness` at `5443f38339ef290bb7ef7ff0d4b7ada8c893cf02` contains `tests/test_pipeline_e2e.py` | Present elsewhere, not run or imported here; repair/reconciliation needed before reuse |

The older harness deletes metadata table contents during cleanup and accepts some
failed pipeline outcomes as documented discoveries. Its `e2e` marker is absent
from this checkout's strict marker configuration. Reconcile it with the current
owned-schema fixture and require explicit success/failure acceptance before using
it as an end-to-end success gate. It was not cherry-picked or rewritten here.
The old plan's next-day labels, sequencing and commit-message rules do not override
the current deferred evaluation decision or workspace standards.

## Runtime and lock identity

| Component | Observed |
|---|---|
| Shell/default Python | PowerShell; `C:\Program Files\Python314\python.exe`, 3.14.6 |
| Poetry | 2.4.1; unqualified `poetry env info` reports no project virtualenv |
| Selected existing environment | `C:\Users\asbou\AppData\Local\pypoetry\Cache\virtualenvs\sen2nal-dawZnZaD-py3.11` |
| Verified interpreter | Selected environment's `Scripts\python.exe`, CPython 3.11.9 |
| Other cache | `sen2nal-9rhhmiXY-py3.11` also runs Python 3.11.9; not selected for checks |
| Node / npm | 24.18.0 / 11.16.0; existing frontend dependencies reused |
| Frontend installed tools | Vite 7.3.7, TypeScript 5.9.3, ESLint 9.39.4 |
| Backend installed / locked samples | pytest 7.4.4, pytest-cov 4.1.0, ruff 0.1.15, mypy 1.19.1, transformers 4.57.3, torch 2.9.1, xgboost 2.1.4, pydantic 2.12.5, SQLAlchemy 2.0.45; all nine samples match |

Each backend invocation set `VIRTUAL_ENV` only inside its command process. This
selects an existing environment without `poetry env use`, a config write or an
install. `poetry check --lock` reported legacy Poetry metadata warnings, not an
error. The version sample does not certify the entire installed dependency graph.

SHA-256 of unchanged input files:

| File | Hash |
|---|---|
| `pyproject.toml` | `ebb0c444340ab3b3d0e7115b6578741f0fad238de037d7246bcda5d351eb33cd` |
| `poetry.lock` | `170ff1615c33ea1b173f93600e575c4dc93314776e07950ca90e6b77d468e7d4` |
| `frontend/package.json` | `9b2c944963ad2d340408cee966a6217f0e8c9abd698502c163bea90b5cc2e23f` |
| `frontend/package-lock.json` | `a7bc24283d054cc6a1e76f14a63e85690461868a4475f774fe1a2c253982132f` |

## Safe execution controls and fresh results

`tests/conftest.py` imports settings, a SQLAlchemy engine and the FastAPI app.
Configuration normally reads `.env` and appends a dated local log at import.
Engine construction is not a connection, but API lifespan can check the database
and start the scheduler. The PostgreSQL fixture creates/drops an owned schema only
when an explicit permitted test URL is supplied; it uses metadata creation, not
Alembic. No disposable database target/role was authorised in this session.

A session-only wrapper at `tmp/sn-base-2026-11-04/offline_pytest.py` suppressed
dotenv loading via `BaseSettings.__init__`, supplied synthetic testing settings,
removed the test database URL, PostgreSQL routing variables and provider keys,
disabled scheduler/retraining/backtest/experiment flags, enabled Hugging Face
offline mode, and guarded Python socket connections plus `psycopg2.connect`.
It explicitly loaded only pytest-cov/pytest-asyncio plugins. Guards count attempts
even if application code catches the raised error; both runs ended with count 0.
This is test-process instrumentation, not a change to the app or a shipped runner.

The wrapper SHA-256 is
`88c459c66649ef708907cb29b7a5b572325ca87ed267f13f16e4ce617d94e245`.
It and session coverage/cache outputs are Git-ignored. Existing root `.coverage`
and `coverage.xml` were not used as fresh evidence. The six
`TestVaderFallback` cases explicitly call `nltk.download`; their exclusion avoids
treating their no-download docstring as an enforced offline guarantee.

Commands below ran from the project root with the selected process-local
`VIRTUAL_ENV`, except frontend commands which ran in `frontend/`.

| Command | Fresh result |
|---|---|
| `poetry check --lock` | Exit 0, legacy metadata warnings |
| `poetry run python tmp/sn-base-2026-11-04/offline_pytest.py tests/test_database_safety.py --no-cov` | Exit 0; 12 passed in 0.06s; zero blocked connection attempts |
| `poetry run python tmp/sn-base-2026-11-04/offline_pytest.py --deselect=tests/test_sentiment.py::TestVaderFallback --cov=src --cov-report=term` | Exit 0; 194 collected, 146 passed, 42 skipped, 6 deselected in 5.34s; 59.20% coverage (1,821 statements, 743 missed), 40% gate retained; zero blocked connection attempts |
| `poetry run ruff check src/ tests/` | Exit 0 |
| `poetry run mypy src/ --ignore-missing-imports` | `subprocess.TimeoutExpired` at 90 seconds; incomplete, not a pass; reporting wrapper exited 1 |
| `npm run lint` | Exit 0; 0 errors, 1 `react-hooks/exhaustive-deps` warning at `ExperimentTable.tsx:33` (`methods`) |
| `npm run build` with process-local `VITE_USE_MOCK_DATA=true` | Exit 0; Vite build 8.73s; JS 781.69 kB / gzip 243.37 kB; chunk-size warning |

The database skips comprise 19 API, 14 model and 9 pipeline-state tests. Coverage
is for the selected offline subset, not the full PostgreSQL or VADER suite.
The mypy reporting wrapper then raised `TypeError` while combining partial output
of mixed text/bytes types; no type diagnostics were recovered. The explicit
`TimeoutExpired` traceback establishes the 90-second timeout. No second type-check
run or dependency change was made to hide or work around the incomplete gate.
Mocked stage/validator tests do not prove every real agent validates before
persistence. A frontend build does not prove an interactive/live API journey.
The frontend has dev/build/lint/preview scripts and no configured `npm test`.
Hooks default to mock data unless explicitly disabled; fixtures are not live data.
CI config contains PostgreSQL-backed ruff/mypy/pytest steps but no frontend job;
this is static configuration evidence only. No hosted run was invoked or verified.

## Review, recovery and next gate

Self-review is limited to this evidence diff, its source/command support, local
links and preservation of existing work; no independent reviewer was run.
All 30 original dirty/untracked paths retained their original Git status and
SHA-256 (or deletion state); only the two delivery paths were added to that scope.
Local Markdown file links resolve. Verification command sessions have finished;
no database, service or scheduler was started. Session wrapper/coverage/cache
artifacts remain under the Git-ignored `tmp/sn-base-2026-11-04/` directory;
the frontend build writes ignored `frontend/dist/` and TypeScript cache files.
The active Git hook path is `.hooks`; `pre-commit` invokes the staged-blob scanner.
Only the two evidence documents belong in the documentation commit. Reverting
that commit reverses this delivery without touching application behaviour or the
pre-existing dirty scope.

No Docker command/file edit, database connection/DDL/reset, model download,
provider call, pipeline/scheduler/service launch, account connection, hosted CI,
push or deployment was performed. No outcome horizon, label, benchmark or universe
membership policy was chosen. This work was performed by the Codex assistant;
it is a local verification/documentation contribution, not an ML or deployed-feature
delivery claim.

SN-BASE is recorded with explicit verification gaps. The next proposed work order
is SN01-A: freeze input availability/publication contracts under the existing
US-only/top-50/08:00 `America/New_York` scope. It requires a separate selection;
SN01-B evaluation remains deferred. Real PostgreSQL isolation/sentinel evidence,
Alembic fresh/upgrade paths, full browser/pipeline journeys, the six download-calling
tests and complete type checking remain unverified unless separately evidenced.

## SN01-A.1 — US-only holiday feature (4 November 2026)

Starting revision: `1072094`. The owner authorised continued implementation and
explicitly requested atomic local commits, the CREAMS commit SOP lookup and the
Humanizer guide before finalising messages. CREAMS' current `AGENTS.md` states
that its message format is the shared workspace SOP; that SOP also covers Sen2Nal.
No CREAMS application work was performed.

`CalendarAgent._holiday_decay` previously combined US and Bursa holiday lists
for every ticker. It now uses only the US list, preserving the existing approximate
feature calculation and the separately available Malaysian calendar helpers.
This does not make the approximation an authoritative exchange-session calendar.

| Check | Result |
|---|---|
| Updated US-only regression before fix | Failed with actual `-0.3`, expected `-0.0055`, under supplied synthetic holiday lists |
| `offline_pytest.py tests/test_calendar.py --no-cov` | 24 passed in 0.51s, no blocked connection attempts |
| Offline regression command above, plus `-q` | 146 passed, 42 skipped, 6 deselected in 5.19s; 59.18% coverage; 40% floor retained; no blocked connection attempts |
| `poetry run ruff check src/ tests/` | Exit 0 |
| `poetry run python -m mypy src/agents/calendar.py --follow-imports=skip --ignore-missing-imports` | Exit 0; one source file; skipped imports make this narrower than the unresolved full check |

Self-review covered the two-line behavioural change, meaningful red/green test,
US-only owner scope and preservation of the legacy helper API. No frontend files
changed, so the earlier frontend checks were not repeated. PostgreSQL and full
type checks remain unverified. The next SN01-A slice is the pure cutoff/manifest
contract; no scheduler, external source or evaluation change accompanies this fix.
