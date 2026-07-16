---
name: backend
description: Use when designing server-side architecture or REST APIs in any stack - service/repository layering, caching, error handling, rate limiting, background jobs, plus REST resource naming, status codes, pagination, and versioning conventions. Not a substitute for stack-specific skills.
---

# Backend architecture

Two depths. Load the reference that matches the work:

| Doing | Read |
|---|---|
| Layering, caching, errors, rate limits, jobs | [references/patterns.md](references/patterns.md) |
| Designing or reviewing REST endpoints | [references/api-design.md](references/api-design.md) |

Iron rules regardless of reference:

- Validate at system boundaries; trust nothing that crossed one.
- Errors are responses, not surprises: consistent shape, right status code,
  no stack traces to clients.
- Queries stay under the project's latency target; measure before and after.
