# Test-Driven Development

Write the test first. Watch it fail. Write minimal code to pass.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

If you wrote code before the test, delete it completely and start fresh. This is not negotiable.

## The Red-Green-Refactor Cycle

**RED:** Write one minimal test demonstrating the desired behavior.
- Clear name describing what it tests
- Tests one behavior only
- Use real code, not mocks unless truly necessary

**Verify RED:** Run tests. Confirm failure happens for the expected reason — not a typo or import error. This step is mandatory. If you didn't watch it fail, you don't know if it tests the right thing.

**GREEN:** Implement the simplest code possible to make the test pass. Nothing more.
- No over-engineering
- No extra features the test doesn't require

**Verify GREEN:** Confirm the test passes AND all other tests still pass.

**REFACTOR:** Clean up duplication and improve names while keeping tests green.

**Repeat** for the next behavior.

## Regression Test Verification

When fixing bugs, the red-green cycle must be verified:
1. Write regression test → run (must PASS — confirms you reproduced the bug)
2. Revert your fix → run (must FAIL — confirms test actually catches the bug)
3. Restore fix → run (must PASS — confirms fix works)

Skip this = you don't know if your test catches the bug.

## Rationalizations to Reject

| Excuse | Reality |
|---|---|
| "Too simple to test" | Simple code breaks; takes minimal effort |
| "I'll test after" | Tests after pass immediately — proves nothing |
| "Already manually tested" | Manual testing is undocumented and unreproducible |
| "Deleting hours of work is wasteful" | Sunk cost fallacy — untested code is technical debt |
| "Just this once" | No exceptions without explicit human approval |

## When to Apply

- Every new feature
- Every bug fix
- Every refactor
- Every behavior change

**Exceptions** (require explicit user approval):
- Pure configuration changes
- Generated/scaffolded code
- Prototype/throwaway code explicitly labeled as such

## Integration with SOP

This skill applies to ALL tiers during implementation:
- TIER 1-2: Apply directly during implementation
- TIER 3-4: Subagents must follow this skill for each task in subagent-driven-development
