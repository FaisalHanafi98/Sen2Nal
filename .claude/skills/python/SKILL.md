---
name: python
description: Use for any Python work - FastAPI services, ML pipelines, scripts, tooling. Idioms, typing, and layout in references/patterns.md; pytest technique, fixtures, and coverage strategy in references/testing.md. Triggers for RinggitSense backend and Sen2Nal.
---

# Python

Two depths. Load the reference that matches the work:

| Doing | Read |
|---|---|
| Writing or reviewing implementation code | [references/patterns.md](references/patterns.md) |
| Writing tests, fixtures, mocks, or planning coverage | [references/testing.md](references/testing.md) |

Iron rules regardless of reference:

- Type hints on public functions; pydantic models at API boundaries.
- ruff clean; no bare `except`; no mutable default arguments.
- Async handlers never make blocking calls (FastAPI).
- Tests are pytest, written before the implementation for behavior changes.
