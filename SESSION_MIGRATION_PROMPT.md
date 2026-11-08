# Sen2Nal workstation migration prompt

This handoff captures the Sen2Nal implementation and GitHub checkpoint verified
on 8 November 2026. Start here on the new workstation. The project’s current
state and test evidence files remain the sources for later updates.

## Start a new session

Open the Sen2Nal repository root on the `chore/e0m1-environment-baseline` branch,
or on a later branch that contains this handoff. When Codex reads the repository’s
`AGENTS.md`, a request to research or discover the folder routes here. You can
also paste this message in any new session.

> Research and discover this Sen2Nal folder. Start by reading
> `SESSION_MIGRATION_PROMPT.md` and follow its discovery pass end to end. Recover
> the prior work from the linked evidence, code, tests and Git history. Return
> one grounded handoff with the current state and next safe step. Keep this first
> pass read-only and ask me only for information the repository cannot establish.

The published implementation checkpoint is `52cbc0c0ce48f0f403afa3bb7f859e4f10ef95e5`.
The session published 37 commits to `chore/e0m1-environment-baseline` and verified
that all commits reachable from local branches and tags were present on GitHub.
Recheck the live refs if asked to verify current GitHub state. A fresh clone
normally starts on the repository’s default branch, so select the handoff
branch before opening the folder. [GitHub branch](https://github.com/FaisalHanafi98/Sen2Nal/tree/chore/e0m1-environment-baseline)

For a fresh checkout, you can select the branch when you clone.

```text
git clone --branch chore/e0m1-environment-baseline https://github.com/FaisalHanafi98/Sen2Nal.git
```

## Discovery pass for the receiving agent

Complete the whole pass in one session. Follow the links and inspect the source
yourself. Continue past missing optional material and report which conclusions
it limits. Use the owner’s latest instructions, current code, Git and fresh
evidence to resolve drift. Treat older plans, status paragraphs and ADR examples
as dated records when later decisions or implementation supersede them.

1. **Identify the checkout.** Record the repository root, branch, full HEAD,
   upstream, other worktrees and tracked and untracked changes. Locate the
   implementation checkpoint in history. If the branch is missing or an older
   checkout is open, identify the correct branch and preserve any existing work
   before changing checkouts. These commands inspect local state.

   ```text
   git rev-parse --show-toplevel
   git status --short --branch --untracked-files=all
   git rev-parse HEAD
   git branch -avv
   git worktree list --porcelain
   git log -35 --oneline --decorate
   git branch -a --contains 52cbc0c0ce48f0f403afa3bb7f859e4f10ef95e5
   ```

2. **Read governing context in order.** Start with the project instructions,
   then the shared workspace standards if present, the current module state,
   the test evidence log and the verified local section of the setup guide.
   Read the relevant ADRs when a decision needs its rationale. The newest test
   evidence sections supersede the original SN-BASE counts and exclusions.
   [Project instructions](AGENTS.md) · [Current module state](CURRENT_MODULE_STATE.md) · [Test evidence](docs/audits/TEST_EVIDENCE_LOG.md) · [Development setup](SEN2NAL_DEVELOPMENT_SETUP.md) · [ADRs](docs/adr/README.md)

3. **Trace the work from commit to test.** Use `git log --oneline e6ee318..52cbc0c`
   to recover the implementation sequence and `git show <commit>` for any slice
   you need to explain. Read the code and tests in the checkpoint map below.
   Follow the trigger into run admission, stage execution and the saved report,
   then follow the status and logs back to the dashboard. Trace the publication
   cutoff and evidence selection separately from the current pipeline’s live
   ingestion and scheduler. Check the newest code if this checkout is ahead.

4. **Recover the work order and local context.** In the full Development
   workspace, read `../../workspace/reels-improvement-2026-10-19/implementation/README.md`,
   `SHARED-WORKFLOW.md` under that implementation directory, and
   `Sen2Nal/00-PROJECT-WORKFLOW.md` plus the matching module file there. Use the
   older `docs/handover/HANDOVER_2026-07-04.md`,
   `docs/plans/EXECUTION_PLAN_v1.md` and `docs/ai-context/` for chronology and
   terminology. The first two were untracked at the publication checkpoint and
   may be absent on a fresh clone. A repo-only checkout still has enough tracked
   context to complete discovery. Recover the shared `standards/` and `core/`
   workspace context before relying on shared-mode tooling for implementation.

5. **Return one consolidated handoff.** Report the actual checkout and dirty
   state, the owner’s release contract, the implementation and its entry points,
   the strongest verification and its limits, and the remaining work in
   dependency order. Separate what you inspected on this machine from what the
   prior session measured. Give a concrete next step and ask only for a missing
   asset, permission or business decision that blocks that step. End discovery
   with the report unless the owner also requests implementation or execution.

## Owner decisions to carry forward

- Sen2Nal is supplementary personal market research. The planned release is US
  stocks only, initially the 50 largest US companies by market capitalisation
  with one representative ticker per company. It uses ticker-specific news and
  forum sentiment, supported by roughly one year of historical evidence.
- Publish daily at 08:00 `America/New_York` on an appropriate US trading session.
  The daily schedule supersedes the earlier weekly direction. Use exchange time
  and daylight-saving rules. The current ten-ticker defaults and approximate
  calendar still exist in the implementation.
- Surface the evidence, timestamps, component scores and uncertainty behind
  explainable research tags. Keep **NOT FINANCIAL ADVICE** on prediction output.
  Stock-price targets, trade execution and personalised portfolio advice are
  outside the release scope.
- The owner deferred evaluation design. Keep the ADR-005 intent of 252 training
  trading dates and 21 test trading dates. Outcome labels, horizons, benchmarks,
  costs and leakage repairs belong to the separately authorised evaluation
  work. The roughly one-year evidence requirement is separate from a data
  retention limit or a minimum evaluation history.

## Implementation checkpoint map

| Slice | Delivered at the checkpoint | Read to recover the implementation |
| --- | --- | --- |
| SN-BASE | Bounded offline baseline with Python 3.11.9, Poetry, synthetic settings and database safety checks. | `1072094`, `f6a4b34`, [test fixtures](tests/conftest.py), [database safety tests](tests/test_database_safety.py) |
| SN01-A | US-only holiday effects, DST-aware cutoff and deterministic selection of versions available by cutoff. The frozen manifest records supplied US session and dated 50-company membership evidence, and distinguishes withheld, no-data and eligible-input outcomes. | `455470f`, `d07e1e7`, `790bd17`, [publication contracts](src/contracts/publication.py), [publication tests](tests/test_publication.py) |
| SN02 stage boundaries | The first five stages require explicit valid success. Invalid, failed and partial outcomes halt the run. Write checks cover ingestion, sentiment, calendar, features and predictions. Valid empty batches have separate outcomes. Pending writes roll back on failure. Earlier committed stages can retain rows. The experiment is non-critical. | `cefc3f8`, `e8260c7`, `d673516` through `79a5e49`, [runner](src/pipeline/runner.py), [agents](src/agents/), [stage and API tests](tests/test_pipeline_integrity.py) |
| SN02 execution and dashboard | API, CLI and scheduler share run admission. The code uses a PostgreSQL transaction lock and saves queued runs. Workers claim a queued run before executing stages and carry its ID into results. The API dispatches the worker through a thread pool. Status and bounded logs follow the saved run. The dashboard labels sample, queued, running, invalid and partial states. | `be37835`, `be20c9d`, `9fc0c0d`, `bb7ea8a`, `3d9a0b8`, `e1fc6e0`, `5337810`, `0aa08f3`, `32c1c19`, [run admission](src/pipeline/runs.py), [pipeline API](src/api/routers/pipeline.py), [dashboard](frontend/src/pages/Dashboard.tsx) |
| SN03-A | VADER tests use a local lexicon or skip explicitly. The standalone local VADER analyser was measured with synthetic text. FinBERT verification awaits an authorised local snapshot. | `79bd774`, [sentiment tests](tests/test_sentiment.py), [asset and timing evidence](docs/audits/TEST_EVIDENCE_LOG.md#sn03-a--offline-vader-verification-and-asset-inventory-8-november-2026) |
| SN-M01.1 | A frozen replay candidate binds supplied tags and score components to the manifest’s members, selected evidence, scorer artifacts and eligible prior history. It has a deterministic hash. | `52cbc0c`, [replay contract](src/contracts/replay.py), [replay and publication tests](tests/test_publication.py) |

The last guarded backend run passed **336 tests**, skipped **43 PostgreSQL tests**
and reached **79.99% coverage**, with zero blocked connection attempts in that
run. Ruff and focused mypy passed. Full mypy timed out at 75 seconds. The frontend
build and lint passed with the existing bundle size and React hook warnings.
These are dated results. The native PostgreSQL concurrency and transaction gates,
provider compatibility, live scheduler behaviour and deployed state need their
own evidence. An early admission test entered the unmocked runner before it was
interrupted. Provider contact for that attempt is unverified. The corrected test
fixture mocks the stages. [Test evidence](docs/audits/TEST_EVIDENCE_LOG.md)

## Resume work when authorised

1. **Rebuild the baseline on the new workstation.** Use the locked Poetry
   environment with an explicit Python 3.11 interpreter. On Windows, `py -0p`
   lists candidates. Verify `poetry run python --version` after selecting the
   environment. Resolve Node from the tracked frontend setup and lockfile.
   Use the no-Docker setup section and check commands against current project
   files. The old Python path, virtual environment and caches are machine-local.
2. **Recreate offline test isolation before running tests.** The prior
   `tmp/sn-base-2026-11-04/offline_pytest.py` was ignored scratch. The evidence
   log describes its controls. Use process-local synthetic settings, suppress
   dotenv, clear provider credentials and test DB routing, disable scheduler
   and training side effects, enforce model offline mode and guard connection
   attempts. Inspect fixtures and ASGI startup before running tests. Avoid
   reading or printing real environment values during setup. Recheck Ruff,
   focused tests and the full mypy gate on the new host as appropriate.
3. **Close SN02’s native database proof when the owner supplies the target.**
   Use only an authorised, disposable local PostgreSQL database ending in
   `_test`, with the separate `SEN2NAL_TEST_DATABASE_URL`. Review the fixture’s
   unique schema ownership and cleanup. Prove overlapping admissions, duplicate
   claims, durable status and rollback behaviour on that target. Define recovery
   for abandoned queued or running rows. The app’s `DATABASE_URL` gives no test
   authority. PostgreSQL is the integration target. [Run state tests](tests/test_pipeline_state.py) · [Database safety tests](tests/test_database_safety.py)
4. **Keep release prerequisites explicit.** SN01-A still needs an authoritative
   exchange calendar, a point-in-time universe source, share-class and rebalance
   policies, verified provider rights and source timestamps, and integration of
   the 08:00 contract with actual publication. SN03-A still needs exact FinBERT
   weights, tokenizer, revision, licence and local measurements. SN03-B is an
   optional comparison after those gates. SN01-B evaluation remains deferred.
5. **Advance the follow-on modules in order.** SN-M01 still needs persistence,
   read API and UI, visibility, private notes and a verified publication journey.
   SN-A1 covers search over authorised historical evidence, starting with cutoff-correct
   lexical retrieval when durable evidence exists. SN-A2 separates operational
   freshness from later outcome-based calibration and drift measures. Start one
   authorised slice at a time and state its acceptance evidence before coding.

Discovery authorises reading and reporting. A separate task or existing explicit
authority is needed for execution that touches databases, providers, model assets,
schedulers, deployments or external services. Local Docker and Compose work is
out of scope. Preserve unrelated edits. For an authorised commit, use the shared
commit SOP, the Humanizer guide and normal hooks. A historical push records what
was authorised in that session. Confirm the scope of any new publication from
the current owner request. [Project instructions](AGENTS.md)

## What to transfer

For a GitHub clone, use the branch containing this prompt and its `AGENTS.md`
pointer. For full workspace tooling, restore the surrounding Development layout
with `projects/Sen2Nal`, `standards/`, `core/` and the relevant work-order folder.
Keep project-relative links and paths intact. A standard clone provides tracked
files and reachable history. It does not carry the 30 uncommitted paths that
existed at the publication checkpoint, the older untracked handover and plan, or
ignored test helpers and caches. Transfer any needed local drafts separately
after reviewing them. Set up credentials through the new machine’s approved
credential store. Keep `.env` files, credentials, raw logs, private data and
machine-specific settings out of this handoff and Git.
