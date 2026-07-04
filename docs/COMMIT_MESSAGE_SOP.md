# Sen2Nal — Commit Message SOP

**Document type**: Governance — commit standards
**Scope**: All Sen2Nal commits on all branches
**Last updated**: 4 July 2026

---

## Required format

```
Type(Scope): Title.

Project: Sen2Nal
Date: DD Month YYYY
Task:

[Short human title]

[Plain-language explanation of what changed and why.]

Verified that:

1. [specific check]
2. [specific check]
3. [specific check]

[Short explanation of why the change matters.]

[Assisted by AI, reviewed manually by Faisal]
```

The footer `[Assisted by AI, reviewed manually by Faisal]` is required on every
commit where AI tooling contributed to the diff. It must appear as the last line
of the message body, separated from the preceding paragraph by a blank line.
Omit the footer only when the entire commit was written and reviewed by a human
with no AI involvement.

---

## Full example

```
Docs(Governance): Establish commit message SOP and preserve E0.M1 handover.

Project: Sen2Nal
Date: 04 July 2026
Task:

Preserve handover artifacts and commit standards on main

Added the cross-model engineering handover (HANDOVER_2026-07-04.md) and the
living state file (CURRENT_MODULE_STATE.md) to main so they survive across
sessions and worktrees. Both files previously existed only as untracked files
in a single working tree and would have been lost on the next clean.

Also added this commit message SOP, adapted from the CREAMS project so that
every Sen2Nal commit follows the same structured format with a verified-that
evidence section and a consistent attribution footer.

Verified that:

1. git status --short confirms only the three intended docs files are staged.
2. No source code, config, schema, or Docker files are in the diff.
3. CURRENT_MODULE_STATE.md updated to reflect PR #1 merged (6efc43d).

The handover and state file are the primary context-recovery instruments for
any engineer or model resuming the refactor programme. Without them on main,
a fresh clone has no record of the 37-module plan or the current checkpoint.

[Assisted by AI, reviewed manually by Faisal]
```

---

## Conventional title

The first line is always a conventional commit title:

```
Type(Scope): Short description in sentence case.
```

- End with a full stop.
- Keep under 72 characters.
- Sentence case: capitalise the type and the first word of the description only.

Types: `Feat`, `Fix`, `Refactor`, `Docs`, `Test`, `Chore`, `Security`

Scopes (Sen2Nal module areas):

| Scope | Covers |
|-------|--------|
| `Env` | Environment setup, Poetry, Python version, dependencies |
| `Tests` | Test suite, test evidence, coverage, conftest |
| `Pipeline` | Pipeline runner, scheduler, stage gating |
| `Contracts` | Pydantic data contracts, data quality validator |
| `Agents` | Pipeline agents (ingestion, sentiment, calendar, features, prediction, experiment) |
| `Db` | Database models, migrations, connection, Alembic |
| `Api` | FastAPI routers, endpoints, middleware |
| `Frontend` | React NightOps Terminal, Vite, Tailwind |
| `Calendar` | Holiday decay, calendar effects, Bursa/NYSE holidays |
| `Sentiment` | FinBERT scoring, VADER fallback |
| `Prediction` | XGBoost, walk-forward validation, label leakage |
| `Features` | Feature engineering, SHAP/feature contributions |
| `Experiment` | Weekly LLM comparison (AG-06) |
| `Alerts` | Alerts router, combined score |
| `Ci` | GitHub Actions, CI pipeline |
| `Docs` | Documentation, ADRs, README, setup guides |
| `Governance` | SOPs, CLAUDE.md, AGENTS.md, handover artifacts |

---

## Writing rules

**Use UK English throughout.**

Write like a real developer explaining a change to a teammate who will read it in six months.

### Avoid

- Co-Authored-By trailers naming a specific AI model or product
- Marketing tone or overpolished AI language
- Vague phrases: "enhanced robustness", "improved reliability" — unless you can state what metric changed
- Emojis in technical commit messages
- Excessive bold formatting
- "not only... but also"
- "from X to Y" unless it refers to a real measurable range (e.g. "from 8 to 12 characters")
- Unnecessary em dashes in prose
- Title-case headings inside the commit body
- Vague claims without evidence

### Prefer

- Direct wording: say what the code does, not how impressive it is
- Clear reason: why did this change happen now?
- Specific test evidence: name the test file or pytest filter used
- Risk reduction language: what could go wrong without this change?
- Honest wording if something is incomplete or deferred

---

## The "Verified that" section

Each numbered item must describe a real check you ran. Examples of good items:

```
1. poetry run pytest tests/test_calendar.py -v passes (14 tests, 0 failures).
2. git diff --cached --name-only confirms only src/agents/prediction.py is staged.
3. ruff check src/agents/prediction.py returns no errors.
4. poetry run python -c "import src.contracts.prediction" exits 0.
```

Examples of bad items (do not use):

```
1. Code is correct.
2. Changes look good.
3. Tests pass.
```

---

## What to include in the body

| Include | Omit |
|---|---|
| What the file/function did before | Line-by-line diff narration |
| What it does now and why | File contents verbatim |
| Which tests cover the change | Editor used |
| What risk this reduces | Praise for the change |
| Any known gaps or deferrals | Future plans unrelated to this commit |

---

## Short commits (docs, typos, renames)

For genuinely trivial commits — a typo fix, a rename-only doc move — you may abbreviate. Omit "Verified that" only when there is nothing to verify beyond "file exists at new path".

```
Docs(Archive): Move PLAN.md into docs/archive/prompts/.

Project: Sen2Nal
Date: 04 July 2026
Task:

Rename only. No content change. Follows the docs/ consolidation.
```

---

## Module commits (refactor programme)

For module commits in the 37-module refactor programme, the title must include the module identifier:

```
Fix(Prediction): Eliminate label leakage with t+1 target shift (E2.M1).
```

This makes `git log --oneline` a readable programme audit trail.

---

## Authority

This SOP is governed by the root `CLAUDE.md` (commit protocol section) and the project `CLAUDE.md`. In case of conflict, the root SOP wins. This file refines the format for the Sen2Nal project specifically.

This SOP replaces the prior convention of `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` footers. All commits from E0.M1 merge onward use the format defined here.
