# Engineering Standard: Commit Message Standard Operating Procedure (SOP)

All commit messages in this repository must adhere to the standardized Conventional Commits specification with detailed metadata, verification evidence, and justification.

## Format Specification

```text
<Type>(<Scope>): <Short description in sentence case ending with a period.>

Project: <Project Name>
Date: DD Month YYYY
Task:

<Short human task title>

<Plain-language UK English explanation of what changed, why it changed, and architectural context.>

Verified that:

1. <Specific verification check with test command/evidence>
2. <Specific verification check>

<Why this change matters / risk reduction / impact.>

[Assisted by AI, reviewed manually by Faisal]
```

## Allowed Types
- `Feat`: New feature or major capability.
- `Fix`: Bug fix or defect remediation.
- `Refactor`: Code change that neither fixes a bug nor adds a feature.
- `Test`: Adding missing tests or correcting existing tests.
- `Chore`: Build tasks, dependency updates, tooling configuration.
- `Docs`: Documentation-only changes or state updates.
- `Security`: Security hardening, secret remediation, or audit fixes.
