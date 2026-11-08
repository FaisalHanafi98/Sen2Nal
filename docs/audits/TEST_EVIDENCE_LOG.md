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

## SN01-A.2 — Cutoff and source-version selection (4 November 2026)

Starting revision: `455470f`. `src/contracts/publication.py` adds frozen strict
evidence references and pure inclusive 08:00 New York selection. Source times are
aware UTC instants, with unknown timestamps retained as unknown. Selection is
deterministic across input order/retries, preserves first receipt, uses only the
latest eligible revision and refuses conflicting/ambiguous versions. Explicit
expiry marks a latest revision stale without resurrecting older content. Missing
expiry is unassessed freshness, not a freshness or publication certificate.
No licensed source text is copied into these references. ADR-004's dated amendment
reconciles the owner cutoff and records that the legacy scheduler is not integrated.

Red/green progression observed: the unimplemented cutoff failed both DST cases;
a late revision was initially selected incorrectly; eligible retries/revisions
were initially order-dependent; expiry/conflict/ambiguity controls initially failed;
timestamp order and an empty naive-cutoff request were initially accepted.
Each group passed after its corresponding implementation. The completed suite
also asserts unknown times, naive source times, exact cutoff/microsecond boundaries,
UTC normalisation, first receipt and frozen records. Inputs are synthetic.

| Check | Fresh result |
|---|---|
| Offline regression command above, plus `-q` | 164 passed, 42 skipped, 6 deselected in 3.42s; 60.71% coverage; 40% floor retained; zero blocked connection attempts |
| Publication subset within that run | 18 passed; 71/71 module statements covered |
| `poetry run ruff check src/ tests/` | Exit 0 |
| `poetry run python -m mypy src/contracts/publication.py --follow-imports=skip --ignore-missing-imports` | Exit 0; one file; imported modules deliberately skipped |

Self-review covered cutoff inclusivity, DST, chronology, identity conflicts,
deterministic ordering, source-only references and immutable nested values.
The selector is not wired to persistence/API/scheduling and does not certify
freshness, rights or signal quality. Full mypy, PostgreSQL, real calendar/universe
and publication journey checks remain open. The next independent package is a
hashable manifest with explicit withheld/no-data reasons; evaluation stays deferred.

## SN01-A.3 / SN-M01.1 — Pure evidence manifest (4 November 2026)

Starting revision: `d07e1e7`. Frozen supplied US-session and universe records now
form an input manifest with explicit cutoff, timezone, run/method/configuration
identity and `NOT FINANCIAL ADVICE`. Membership requires 50 distinct US companies,
tickers and ranks, dated effectiveness and nonblank source/share-class/rebalance
references. Session intervals are explicit, so closed and half-day fixtures do not
silently become weekday/default-close assumptions. No actual provider or owner
policy was selected by these synthetic records.

The availability states are `withheld`, `no_data` and `eligible_inputs`.
`eligible_inputs` means supplied structural/as-of prerequisites only: it does not
certify source truth, approved policies, rights, freshness without an expiry,
run validation or model quality. No tag is published. A manifest rejects ineligible
evidence rather than allowing constructor calls to bypass source selection.
Canonical JSON includes frozen original input facts and round-trips through the
strict model. Its SHA-256 includes run/method/configuration and source identities;
it is not a cross-run publication uniqueness constraint or a persistence ledger.

Observed red/green cases: missing calendar/universe initially reported eligible;
closed/mismatched/late calendars and ineffective/late universes initially passed;
duplicate mappings, malformed intervals and ineligible manifest evidence were
initially accepted; cutoff was initially absent; blank provenance and a session
opening at the cutoff were initially accepted. Each group passed after repair.
Further cases prove exact hash/JSON replay, late-version and retry sentinels,
member-order canonicalisation, changed-version hash distinction, half-day cutoff,
frozen nested originals, 49-member refusal and non-US refusal.

| Check | Fresh result |
|---|---|
| `offline_pytest.py tests/test_publication.py --no-cov -q` | 44 passed in 0.23s; zero blocked connection attempts |
| Offline regression command above, plus `-q` | 190 passed, 42 skipped, 6 deselected in 4.02s; 63.00% coverage; 40% floor retained; zero blocked connection attempts |
| `poetry run ruff check src/ tests/` | Exit 0 |
| `poetry run python -m mypy src/contracts/publication.py --follow-imports=skip --ignore-missing-imports` | Exit 0; one source file, imports skipped |

Self-review covered strict frozen inputs, date/time boundaries, unique membership,
source-only references, canonical hashing, constructor bypass and calibrated state
names. This is SN-M01.1's pure input-manifest foundation, not the journal/replay
module's persisted publication-to-note journey. Score/model/history bindings,
source rights, approved actual membership, live session integration, PostgreSQL
and full mypy remain open. Next: independently repair SN02 run/status boundaries;
do not use a nonblank synthetic policy reference as owner approval.

## SN02.1 — Critical-stage result envelopes (8 November 2026)

Starting revision: `790bd17`. Every critical runner boundary now requires explicit
`success` to advance. Recognised `partial`, `invalid` and `failed` results halt
with their failure kind retained. Missing/unknown/unhashable statuses, non-dict
results, success accompanied by an error, and invalid/nonfinite/overflowing
durations become bounded `invalid` results. Unexpected constructor/run exceptions
become generic failed results without forwarding their text. Non-success rolls
back pending session work and logs only stage/status context. A non-critical
experiment failure is recorded separately and cannot invalidate valid critical
stages. Returned payload dictionaries are copied before normalisation.

Observed red/green: five partial-stage cases originally reported overall success;
32 malformed/exception cases originally raised or misreported outcomes; five
bad-duration cases originally reported success. All passed after their repairs.
An additional overflowing-integer case and explicit successful empty-record envelope
positive control pass. Empty records in an explicit success envelope are not
themselves malformed; this does not prove real-agent record validation/empty states.

| Check | Fresh result |
|---|---|
| Focused integrity/runner/contract run | 65 passed in 0.71s before the final two edge cases; zero blocked connection attempts |
| Offline regression command above, plus `-q` | 234 passed, 42 skipped, 6 deselected in 6.38s. Coverage 63.44%, above the 40% floor. Zero blocked connection attempts. |
| New integrity subset within regression | 44 passed |
| `poetry run ruff check src/ tests/` | Exit 0 |
| `poetry run python -m mypy src/pipeline/runner.py --follow-imports=skip --ignore-missing-imports` | Exit 0; one file with imports skipped |

Self-review covers every critical stage, downstream refusal, failure-kind identity,
exception redaction, finite numeric durations and non-critical experiment handling.
All stages and sessions were mocks; no actual pipeline, provider or database ran.
Rollback cannot undo earlier agent commits. Pre-persistence contracts, validated
empty/partial data handling, run correlation, concurrent admission and read-model
truth remain open.

## SN02.2 — BaseAgent result ownership (8 November 2026)

Starting revision `cefc3f8`. BaseAgent owns status, agent identity, run ID, elapsed
time and error code. Malformed or reserved-metadata payloads are invalid. An
execution error is failed and a data contract violation is invalid. Exceptions
and execution error payloads use bounded messages in results and logs. Duration
comes from a monotonic clock. The tests use mocked sessions.

The targeted red run reproduced 11 metadata, classification and redaction failures.
The offline regression run passed 241 tests, skipped 42 PostgreSQL tests and
deselected six download-calling cases in 4.91s. Coverage reached 63.56% against
the 40% floor, with zero blocked connection attempts. Full Ruff and focused
`python -m mypy src/agents/base.py --follow-imports=skip --ignore-missing-imports`
passed. Agent commits before validation and real PostgreSQL remain open.

## SN02.3 — Run identity through the API worker (8 November 2026)

Starting revision `e8260c7`. The trigger creates an opaque run ID within the
existing column limit. The worker fetches its active row before starting,
passes its ID and target date to the runner, and checks the returned identity
before storing the result and stage logs. The runner binds each stage result
to the active ID. Worker errors roll back pending writes and store a bounded
failure for an active row. Tests exercise the configured API key through ASGI.

The Windows event loop socket conflicted with the offline guard. The final
fixture drives HTTPX's in-memory ASGI transport directly and runs mocked sync
I/O inline. With that fixture, five tests failed on the old implementation and
the two denied-key controls passed. All seven pass after the fix. The offline
suite passed 248 tests, skipped 42 PostgreSQL tests and deselected six
download-calling cases in 4.48s. Coverage was 65.56% with zero blocked connection
attempts. Ruff and focused mypy on the runner and pipeline router passed.

Security review found the configured-key boundary preserved in the exercised
path. The synthetic tests cover allowed and denied requests, mismatched identity,
terminal or missing rows, safe error text and worker-session cleanup. Review
remains open for PostgreSQL transactions, concurrent admission and worker
scheduling. The worker still uses the existing asynchronous dispatch shape.

## SN02.4 — Run-specific status projection (8 November 2026)

Starting revision `be37835`. The status endpoint queries the latest saved run
or a requested run ID. It projects the five critical stages from a matching
run, date and outcome. Zero counts remain visible, active runs keep their
recorded running state, and unsupported legacy success is unverified. The
projection includes only recognised status, duration and count fields. Its
storage indicator refers to the saved run result.

Five ASGI regressions failed against the historical-count implementation.
The offline suite passed 257 tests with 42 PostgreSQL skips, six download-calling
cases deselected and 66.86% coverage. The final focused run passed all 60 pipeline
integrity tests after adding deterministic ordering for null start times. Ruff
and focused router mypy passed. Both test runs reported zero blocked connection
attempts. Live PostgreSQL query execution and dashboard rendering remain open.

## SN02.5 — Dashboard run-state display (8 November 2026)

Starting revision `be20c9d`. The dashboard uses the run state from the status API,
includes the calendar node and labels unreported stages in text. Sample responses
carry a visible sample marker. The status card describes the latest saved run.

The local `verify-dashboard.cjs` check failed when a saved failed run rendered
as idle. It now passes for failed, running and unverified inputs, calendar and
unreported labels, and sample mode. It renders the actual dashboard and pipeline
components to static markup with synthetic data and stubbed unrelated widgets.
The test is in the ignored session directory. `npm run build` passed with the
existing chunk-size warning. `npm run lint` exited zero with the existing
ExperimentTable hook warning. Browser and live API verification remain open.
The build used the current worktree. Git's `lib/` ignore rule excludes three
existing frontend modules that tracked components import. Source tracking for
those modules is a separate checkout fix.

## Frontend source tracking (8 November 2026)

Starting revision `9fc0c0d`. The root `lib/` rule ignored the existing frontend
animation, constants and utility modules. A source export from the index failed
to bundle with fourteen unresolved imports into those three modules. The narrow
frontend exception and the three reviewed modules produce a passing bundle from
the staged export with the installed dependency tree. The synthetic nested Python
`lib/` check remains ignored. This verifies source availability and import
resolution. The worktree Vite build is recorded in SN02.5.

## SN02.6 — Sentiment batch validation (8 November 2026)

Starting revision `7c02e58`. The real SentimentAgent validates one score pair per
selected input and checks score, confidence, model kind and timestamp through
the sentiment contract. Each batch is validated before any of its rows are
mutated. A later Reddit failure rolls back pending news work before the stage
commit. The summary records the validated count, actual scorer kind and an
explicit empty state.

Six focused assertions failed before the repair. The offline suite passed
264 tests, skipped 42 PostgreSQL cases and deselected six download-calling
cases in 5.31s. Coverage was 68.66%. Ruff and focused mypy on both changed
Python modules passed. Tests use synthetic scores and mocked sessions with
zero blocked connection attempts. Durable PostgreSQL rollback remains open.

## SN02.7 — Feature write validation (8 November 2026)

Starting revision `d673516`. The feature agent validates the actual daily
sentiment write payload before adding it. Existing decimal history and observed
zero source scores retain their meaning. A failure on a later ticker aborts the
stage and requests rollback of pending writes. Successful stages distinguish
zero new records from a populated write batch.

Six focused assertions failed before repair. The offline suite passed 270 tests,
skipped 42 PostgreSQL cases and deselected six download-calling cases in 5.30s.
Coverage was 71.17%, with zero blocked connection attempts. Ruff and focused
mypy passed. Tests use the real feature agent with mocked reads and sessions.
PostgreSQL transaction verification remains open.

## SN02.8 — Prediction write validation (8 November 2026)

Starting revision `56e6ea3`. Both legacy prediction paths validate the actual
fact write fields. The model path requires a finite binary probability vector
that sums to one within floating-point tolerance. Contribution proxies must be
finite. The fallback keeps a real zero, skips missing scores and uses a version
identifier that fits the existing column. The result records the active mode,
validated count, empty state and the research disclaimer.

Ten focused assertions failed before repair. The offline suite passed 280 tests,
skipped 42 PostgreSQL cases and deselected six download-calling cases in 5.82s.
Coverage was 74.02%, with zero blocked connection attempts. Ruff and focused
mypy passed. Tests mock training, inference and database sessions. The existing
evaluation design remains deferred. Model artifact lifecycle and durable
PostgreSQL transaction verification remain open.

## SN02.9 — News and Reddit staging validation (8 November 2026)

Starting revision `5ed25d4`. Ingestion validates news and Reddit records before
adding them. A malformed record stops the stage and rolls back pending writes.
News timestamps with offsets are stored in UTC. Missing or ambiguous publication
times and missing URLs remain unknown. Transport warnings omit exception text.

Seven focused assertions failed before repair. The offline suite passed 288
tests, skipped 42 PostgreSQL cases and deselected six download-calling cases
in 4.49s. Coverage was 75.80%, with zero blocked connection attempts. Ruff and
focused mypy with skipped imports passed. Tests use fixture payloads and mocked
sessions. Provider response compatibility and PostgreSQL transactions still
require verification.

## SN02.10 — Market ingestion write validation (8 November 2026)

Starting revision `ca5eefe`. Price rows require bounded finite OHLC values,
consistent bar ranges, whole nonnegative volume and ordered dates within the
requested window. A flat return is stored as zero. Fear & Greed requires a
score and rating. It preserves an observed zero prior score when calculating
the change. Malformed market records roll back pending ingestion writes.

Thirteen focused assertions failed before repair. The offline suite passed 301
tests, skipped 42 PostgreSQL cases and deselected six download-calling cases.
Coverage was 77.91%, with zero blocked connection attempts. Ruff and focused
mypy with skipped imports passed. The tests use fixture provider responses and
mocked sessions. Live provider shapes, as-of eligibility and PostgreSQL storage
remain unverified.

## SN02.11 — Calendar signal boundary (8 November 2026)

Starting revision `666036d`. A valid weekday signal failed the strict contract
because the stage validated its serialised date. It now validates the original
date alongside each computed signal before returning the ISO date summary.
Out-of-range signals still fail the stage and are withheld from downstream.

The weekday regression failed before the fix. The offline suite passed 303
tests, skipped 42 PostgreSQL cases and deselected six download-calling cases
in 7.08s. Coverage was 78.21%, with zero blocked connection attempts. Ruff and
focused mypy with skipped imports passed. The calendar features still use
local estimates for holidays, trading days and earnings proximity.

## SN02.12 — Explicit ticker selection (8 November 2026)

Starting revision `0716212`. An explicit selection with no allowed tickers
fails validation before any stage starts. Repeated allowed tickers are passed
once, in request order. An omitted selection still uses the legacy default.

Two focused assertions failed before repair. The offline suite passed 306 tests,
skipped 42 PostgreSQL cases and deselected six download-calling cases in 6.58s.
Coverage was 78.39%, with zero blocked connection attempts. Ruff and focused
mypy with skipped imports passed.

## SN02.13 — Logs for the displayed run (8 November 2026)

Starting revision `ab5d522`. The log endpoint accepts an optional saved run ID,
returns each row's run ID and caps requests at 100 rows. The response exposes
bounded worker outcomes and withholds historical free text. The dashboard
fetches logs for the run returned by status and skips the request when idle.

Four focused assertions failed before repair. The socket-free ASGI tests
verify query bounds, run filtering and withholding of exception text. The
guarded offline suite passed 310 tests, skipped 42 PostgreSQL cases and
deselected six download-calling cases in 8.61s. Coverage was 78.66%, with zero
blocked connection attempts. Ruff and focused mypy with skipped imports passed.
A synthetic fixture exercised the dashboard request hook with and without a
saved run. The Vite build and ESLint passed with the existing chunk-size and
React hook warnings. Live browser and PostgreSQL acceptance remain open.

## SN02.14 — API run admission (8 November 2026)

Starting revision `bb7ea8a`. The API takes a schema-scoped PostgreSQL advisory
transaction lock before checking for an active run. A busy lock or active row
returns HTTP 409 without saving another run or dispatching a worker. The lock
ends with the admission transaction. The saved row remains active until the
worker records a terminal state. Recovery of abandoned rows needs a separate
policy. The CLI and scheduler do not use this API guard.

The first regression attempt entered the unmocked runner and was interrupted.
The ASGI fixture now mocks all stages by default. The two corrected regressions
failed before repair, then passed. The guarded offline suite passed 312 tests,
skipped 43 PostgreSQL cases and deselected six download-calling cases in 7.05s.
Coverage was 78.75%, with zero blocked connection attempts in that completed
run. Ruff and focused mypy with skipped imports passed. The new test with
two PostgreSQL sessions was skipped because the authorised test URL was unset.

## SN02.15 — Partial ingestion on fetch failure (8 November 2026)

Starting revision `3d9a0b8`. A reported price, configured NewsAPI or configured
Reddit fetch failure marks the stage partial and rolls back pending writes.
A valid empty news response can still succeed. Missing optional text
credentials preserve the existing skip. Fear & Greed remains supplemental
context and its transport availability is reported separately. The locked
yfinance adapter accepts the option to raise fetch errors.

The two failure regressions reproduced ordinary success before repair. The
guarded offline suite passed 315 tests, skipped 43 PostgreSQL cases and
deselected six download-calling cases in 7.88s. Coverage was 78.91%, with zero
blocked connection attempts. Ruff and focused mypy with skipped imports passed.
Provider behaviour and PostgreSQL rollback remain unverified.

## SN02.16 — Readable stage failure outcomes (8 November 2026)

Starting revision `79a5e49`. The dashboard uses the saved stage outcome to
show incomplete inputs, invalid output and other errors as separate text
labels. The synthetic render reproduced the missing distinction before repair.
It then checked all three labels, the saved run status and sample mode. The
Vite build and ESLint passed with the existing chunk-size and React hook
warnings. A live browser session was outside this check.
