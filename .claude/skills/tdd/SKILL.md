---
name: tdd
description: Apply to every implementation task - features, fixes, refactors: red-green-refactor in vertical slices, no production code without a failing test first. references/ carries the deep technique (mocking, interface design, deep modules). Exceptions require explicit user approval.
---

# Test-driven development

The loop: write ONE minimal failing test → watch it fail for the right reason
→ write the least code that passes → watch it pass → refactor on green.
Repeat per behavior. Never write all tests up front (horizontal slicing
produces tests that check shapes, not behavior — see philosophy).

For bug fixes, the regression cycle is mandatory: test passes against the bug
→ fails with your fix reverted → passes with it restored. Skipping it means
you don't know whether the test catches anything.

| Going deeper on | Read |
|---|---|
| Why vertical slices; anti-patterns | [references/philosophy.md](references/philosophy.md) |
| The iron law and rationalization table | [references/iron-law.md](references/iron-law.md) |
| What good tests look like | [references/tests.md](references/tests.md) |
| When and how to mock | [references/mocking.md](references/mocking.md) |
| Designing testable interfaces | [references/interface-design.md](references/interface-design.md) |
| Deep modules | [references/deep-modules.md](references/deep-modules.md) |
| Refactoring on green | [references/refactoring.md](references/refactoring.md) |
