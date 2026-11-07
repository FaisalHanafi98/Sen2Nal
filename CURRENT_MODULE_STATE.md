# CURRENT_MODULE_STATE

Updated: 8 November 2026. This is the current release and execution entry point.
Earlier checkpoint text is preserved in Git/history and the workspace recovery packet.

## Active continuation: SN02 run/status integrity (8 November 2026)

Starting revision `790bd17`. The owner authorised continued implementation and
atomic local commits. GitHub push remains owner-controlled. The first bounded
repair is complete: runner → critical-stage status validation → halt result,
with every downstream stage mocked. Partial, missing, malformed, unknown or
contradictory status cannot become an ordinary successful run. Invalid/nonfinite
durations are rejected. Unexpected stage exceptions produce bounded failure
results without exception details; optional experiment failures remain non-critical
and are recorded separately. Pending work is rolled back on non-success.
All 44 new run-integrity cases pass. The offline regression suite has 234 passes,
42 PostgreSQL skips, 6 download-calling tests deselected and 63.44% coverage.
Ruff and focused runner typing pass. Full typing remains unverified.
Tests exercise mocked stages and sessions. Agent commits made before validation
still require separate transaction work. The next slice protects BaseAgent
metadata and handles error-bearing payloads. Run correlation, real-agent contracts,
concurrency and read models follow.

## Completed SN01-A foundations (4 November 2026)

The owner authorised continued implementation after SN-BASE. Starting revision:
`1072094`; the original 30 dirty/untracked paths remain outside this work.
The first completed slice removes Bursa holidays from US calendar signals:
the regression was observed red at -0.3 versus -0.0055, then green; all 24 calendar
tests pass. The offline regression subset is 146 passed, 42 PostgreSQL skips,
6 download-calling tests deselected, 59.18% coverage. Ruff and a focused one-file
mypy check with skipped imports pass; full type verification remains open.
The second completed slice adds `src/contracts/publication.py`: an 08:00
America/New_York cutoff and frozen source-version inputs with deterministic
as-of selection. Unknown times and late receipts are excluded; conflicts and
ambiguous revisions fail closed. Explicitly expired revisions are stale, without
inventing a universal freshness window. All 18 new assertions pass; the offline
suite has 164 passes, 42 PostgreSQL skips, 6 download-calling tests deselected and
60.71% coverage. Ruff and the focused publication-module type check pass.
The pure selector does not publish results, enforce provider rights or establish
freshness where no expiry policy is supplied. ADR-004 now distinguishes the
owner's cutoff from its superseded after-close schedule.
The third completed slice adds a versioned, frozen, hashable input manifest with
withheld/no-data/eligible-input states. It validates supplied session intervals,
dated membership with 50 distinct US companies/tickers/ranks, cutoff availability
and nonblank policy references. Canonical JSON round-trips preserve its SHA-256;
late versions, retries and member ordering cannot change the selected original.
The 44 publication tests pass; the offline suite has 190 passes, 42 PostgreSQL
skips, 6 download-calling tests deselected and 63.00% coverage. Ruff and the focused
publication-module type check pass. These are synthetic structural/as-of checks,
not verification of provider truth, policy approval, rights or model quality.

This also completes the pure-manifest portion of SN-M01.1. Persistence, score/model
and supporting-history bindings, read API/UI, private notes and cadence integration
remain open. Actual universe policies/source and a verified calendar feed are still
unresolved; SN01-A is not a completed live release. The next independent repair is
SN02 run/status integrity. Evaluation remains deferred, and full type/PostgreSQL
integration gates remain open. No service or scheduler has been activated.
Revert only the relevant slice's atomic commit to recover; preserve existing local work.

## Completed baseline: SN-BASE (4 November 2026)

The owner selected **SN-BASE only**. The baseline covers checkout/runtime identity,
safe test execution and existing verification/reuse evidence; application behaviour
is unchanged. See the [dated evidence log](docs/audits/TEST_EVIDENCE_LOG.md) for
commands, environment, exclusions, plan mapping and remaining gates.

At source revision `e6ee318`, fresh offline checks produced **146 passed,
42 PostgreSQL skips, 6 download-calling tests deselected, 59.20% coverage**.
The separate mocked database-safety run passed all 12 cases. Ruff and frontend
build passed; frontend lint reported zero errors and one existing hook warning.
Mypy exceeded its 90-second limit and remains unverified. These checks do not
establish real PostgreSQL isolation, a complete pipeline journey or release readiness.

The existing Python 3.11.9 Poetry environment was reused through a process-local
`VIRTUAL_ENV`; unqualified Poetry currently selects host Python 3.14.6 instead.
No environment was installed/rebound. Existing E0.M2 evidence and an E0.M3 harness
were found on other local branches and require reconciliation before reuse.
The later continuation starts SN01-A above. Evaluation remains deferred, and the
US-only/top-50/08:00 New York contract below is retained.

## Owner-defined release contract

| Area | Current decision |
|---|---|
| Purpose | Personal supplementary market research, not a primary investment reference |
| Market | US stocks only; Bursa expansion is outside this release |
| Initial universe | 50 largest US companies by market capitalisation, one ticker per company; implementation pending |
| Cadence | Daily; supersedes the earlier weekly-direction answer |
| Publication | 08:00 America/New_York, on the appropriate US trading schedule |
| Malaysia clock | 20:00 during US daylight time, 21:00 during US standard time |
| Inputs | Ticker-specific news/forum NLP sentiment, supported by roughly one year of historical performance |
| Output | Explainable Buy/Sell research tags, sources, timestamps, uncertainty and prominent risk wording |
| Exclusions | No stock-price targets, order execution, guaranteed performance or personalised portfolio instruction |

Use exchange time rather than a fixed Malaysia offset. The owner wants publication
after returning from work. NYSE regular trading starts at 09:30 Eastern; the timing
and DST references are [NYSE](https://www.nyse.com/trade/trading-information) and
[NIST](https://www.nist.gov/pml/time-and-frequency-division/local-time-faqs).

The owner has explicitly deferred evaluation design until the shared improvements
are finished. Do not reopen that decision or start label/evaluation changes now.
The following details belong to that later work:

- The dated market-cap source, rebalance cadence and representative share class;
  the selection rule itself is settled. Backtests need point-in-time
  membership or an explicit survivorship limitation, not today's leaders assumed historical.
- Which information is excluded by the owner's same-day pre-market evaluation
  instruction. Distinguish news inputs available before 08:00, regular-session price
  history, the evaluation entry baseline and outcomes observed after publication.
- How sentiment and the one-year history combine into a tag; define evidence
  thresholds and neutral/insufficient/stale-source behaviour rather than force confidence.
- The outcome horizon, benchmark, costs and scoring appropriate to daily research.
  A classification target is not the same as forecasting a numeric stock price.

## Current implementation versus intent

Current code still defaults to 10 tickers and its previous signal categories.
The daily 50-stock release, new publication schedule and revised tagging/evaluation
contract are **not implemented**. Do not claim them as working from this document.

Prediction code currently overlaps a same-row daily-return feature and target and
does not establish the required as-of boundary. Stage names do not prove record
validation; only Calendar currently overrides extraction for its Pydantic contract.
Those are investigation/remediation items under SN01, not a verified daily signal.

Keep legitimate existing decisions: React frontend; PostgreSQL-only integration;
ADR-005's 252/21 trading-date intent (actual current row slicing needs repair);
feature_contributions naming; metrics in pipeline_runs.result_json; no local Docker.
The owner's roughly one-year support/history requirement does not silently set a
252-session total-retention cap. A 252-date training window plus a 21-date holdout,
feature warm-up and label maturity needs more history. Establish minimum data and
an insufficient-history outcome during the deferred evaluation design.
No public hosting, scheduler, external API/model call or deployment is authorised
merely by this release contract.

## Earlier verified local changes (20 October 2026)

| Change | Evidence |
|---|---|
| Staged-blob Git scanner | b934d84; owned source refresh, existing registration preserved |
| Frontend security patch | 79741c4; Vite 7.3.7 pinned, baseline/updated builds passed |
| Test lint hygiene | 7b7711c; three unused imports removed separately |
| Test database isolation | f6a4b34; explicit local test URL, unique owned schema, no application-table reset |
| Backend local tests | 152 passed, 42 PostgreSQL-dependent skips, 59.69% coverage; 40% floor retained |
| Safety regressions | 12 mocked cases pass; original destructive fixture and routing bypasses reproduced red/green |
| Frontend checks | Build and loopback HTML/client/TSX/CSS/synthetic-proxy passed; lint: zero errors / one hook warning |
| Native host | Actual Codex/Claude lifecycle event enforcement remains unverified |

Python 3.11.9 tests used explicit synthetic configuration with downloads/external
keys disabled. Existing environments were reused; no ML stack was reinstalled.
Full ruff passes. The broad mypy command stalled and exceeded a bounded retry;
type verification remains **unverified**, not green. No real PostgreSQL connection
or schema change was performed. Mocks do not establish real search-path isolation,
database identity, pool behaviour or unrelated-sentinel preservation.

Working branch remains chore/e0m1-environment-baseline with new local commits;
existing PR/remote status was not refreshed or changed. No push or merge occurred.
Unrelated prior documentation/UI work remains uncommitted and preserved.

## Risk communication and release gates

Keep the existing **NOT FINANCIAL ADVICE** requirement and make the research-only
purpose, possible stale/incorrect/incomplete AI output, independent verification,
risk of loss and the user's responsibility for decisions prominent. Explain the
method, publication cutoff, data/model limitations and dated evaluation honestly.

Draft wording for later UI review:

> Experimental research only — NOT FINANCIAL ADVICE. Buy/Sell tags summarise this
> project's method and may be wrong, incomplete or stale. Use independent sources;
> do not rely on this site as your primary investment reference. Trading can cause
> losses. You are responsible for your decisions. Past performance does not
> guarantee future results.

Do not claim blanket legal immunity or licence exemption from a disclaimer.
The SC's [investment-advice guidance, paragraph 2.2](https://www.sc.com.my/api/documentms/download.ashx?id=d22c8909-06e8-40bf-a8da-4fc31b4606c0)
says disclaimer text alone does not settle licensing; activity and circumstances
matter. US-law applicability and the effect of any terms remain unresolved.
The older SEC 2011 overview explicitly warns it may be out of date, so it is not
used as current clearance. This document is not a legal determination.

Before a public release: settle the contract above, prove time-correct evaluation
and stage/data gates, verify model/data rights and free quotas, establish isolated
PostgreSQL evidence, resolve type checking and security/recovery/hosting gates.
The full reel programme status remains in the
[workspace master plan](../../workspace/reels-improvement-2026-10-19/REELS_IMPROVEMENT_PLAN.md).
