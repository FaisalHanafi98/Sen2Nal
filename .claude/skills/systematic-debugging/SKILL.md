---
name: systematic-debugging
description: Use for any bug or unexpected behavior BEFORE proposing a fix: reproduce, trace the root cause, then fix once. Not for greenfield feature work.
---

# Systematic Debugging

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

Proposing a solution before tracing the root cause is a process violation. Symptom fixes are debugging failure.

## The Four Mandatory Phases

### Phase 1: Root Cause Investigation

- Read the error message completely — do not skim
- Reproduce the issue consistently with exact steps
- Review recent changes (git log, dependency changes, config changes)
- For multi-component systems: add diagnostic instrumentation at each component boundary
- Trace data flow backward from the symptom to find where the problem originates

Do NOT propose a fix until you have completed this phase.

### Phase 2: Pattern Analysis

- Locate similar working code in the codebase
- Compare working examples against the broken implementation completely
- Document every difference — do not stop at the first difference
- Understand all dependencies and assumptions in both

### Phase 3: Hypothesis and Testing

- Form one specific, testable hypothesis about the root cause
- Test with a minimal change (one variable at a time)
- Verify results before forming a new hypothesis
- If understanding is incomplete, say so — do not guess

### Phase 4: Implementation

- Write a failing test that reproduces the bug first
- Implement one targeted fix
- Verify the fix works without breaking other tests
- **If 3+ fix attempts have failed: STOP. Question the architecture, not the fix.**

## Red Flags — Stop and Restart Phase 1

- You are proposing a solution without having traced the data flow
- You are making multiple changes simultaneously
- You skipped evidence-gathering and jumped to a hypothesis
- You have attempted 3+ fixes without finding root cause

## Why This Works

Systematic debugging achieves ~95% first-time fix rates vs ~40% with guess-and-check. Spending 10 minutes on root cause investigation saves hours of thrashing.

## Integration with SOP

This skill applies to ALL tiers for any bug investigation:
- TIER 1-2: Apply directly before any fix attempt
- TIER 3-4: Apply in BRAINSTORM stage; root cause must be confirmed before PLAN stage begins
