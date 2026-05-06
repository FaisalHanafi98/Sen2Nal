# Codex Resume Baseline

Use this file as the starting point for future Codex sessions in Sen2Nal.

## Current Baseline

- Project: Sen2Nal
- Branch: main
- Latest local commit: `7e51de8 feat(frontend): add React baseline`
- Frontend baseline has been committed locally.
- No push has been run from Codex.
- Deployment is not proven.
- CI status is not verified in this session.

## Session Rules

- Do not deploy unless Faisal explicitly asks for deployment.
- Do not run `git push` without explicit approval.
- Do not use `git add -A`.
- Do not stage `frontend/node_modules/`, `frontend/dist/`, `.memsearch/`, or `.env` files.
- Do not claim staging or production readiness without direct verification.
- Keep infrastructure, production compose, CI workflow, ADR, env, and root `CLAUDE.md` edits in separate approved commit groups.

## Verification State

- `npm install` in `frontend/` passed.
- `npm run build` in `frontend/` passed.
- Frontend build reported a large bundle warning.
- `npm install` reported audit findings: 21 moderate and 7 high vulnerabilities.
- Backend pytest coverage gate was not run because Docker was unavailable and Poetry was not on PATH.

## /resume

Continue from this order:

1. Add AGENTS.md / CODEX.md baseline docs.
2. Re-run backend tests in an environment with Docker and Poetry.
3. Verify frontend-to-API runtime locally.
4. Continue feature/API/UI work after baseline verification.

Before committing, follow Git Commit SOP V2:

- Put the commit title first in `<type>(<scope>): <imperative title>` format.
- Run `git status --short`.
- Stage files explicitly.
- Run `git diff --cached --stat`.
- Run `git diff --cached --name-only`.
- Confirm no forbidden files are staged.
- Run relevant tests or explain why not run.
- Draft the full SOP V2 message before committing.

