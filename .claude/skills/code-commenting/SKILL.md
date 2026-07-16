---
name: code-commenting
description: Apply whenever writing or reviewing code comments. Default is no comment; add one only when the code cannot express the why. Not a documentation-writing guide.
---

# Code Commenting Conventions

## The Default Rule

**Default: no comment.**

Add a comment only when the code cannot express the information itself. If you can rename a variable or extract a function to make a comment unnecessary, do that instead.

> "Don't comment bad code — rewrite it." — Kernighan & Plauger
> "The proper use of comments is to compensate for our failure to express ourselves in code." — Robert C. Martin

---

## The One Question

Before writing any comment, ask:

> **"Would a competent developer who knows the language but not this codebase be confused without this comment?"**

If yes → write it. If no → skip it.

---

## When to Comment

### 1. WHY, never HOW

Comments explain reasoning. Code explains mechanics.

```python
# BAD: explains HOW (the code already shows this)
# Loop through users and increment counter
for user in users:
    count += 1

# GOOD: explains WHY
# Exclude service accounts — they inflate DAU metrics
active_users = [u for u in users if not u.is_service_account]
```

### 2. Non-obvious behaviour or side effects

```php
// Soft delete only — PDPA requires audit trail; hard delete is a compliance violation
$patient->delete();
```

```python
# BCrypt has a 72-byte input limit; truncate before hashing to avoid silent failures
password = password[:72]
hashed = bcrypt.hash(password)
```

### 3. Workarounds and known gotchas

```typescript
// Safari <16 doesn't support ResizeObserver in cross-origin iframes
// Fallback to polling until we drop Safari 15 support (target: Q3 2026)
const observer = typeof ResizeObserver !== 'undefined'
  ? new ResizeObserver(callback)
  : setInterval(callback, 200)
```

### 4. External references at the point of use

```python
# Levenshtein distance — O(m*n) time, O(min(m,n)) space
# https://en.wikipedia.org/wiki/Wagner%E2%80%93Fischer_algorithm
def edit_distance(s1: str, s2: str) -> int:
```

```php
// Bursa Malaysia API rate limit: 10 req/min per key (see: internal/api-limits.md)
// Retry with exponential backoff after 429
```

### 5. Bug fixes with context

```java
// Fix for #412: JPA generates cartesian product on nested LEFT JOINs
// Using separate queries + manual merge is 40x faster on datasets > 10k rows
List<Project> projects = projectRepo.findAllBase();
Map<Long, List<Tag>> tags = tagRepo.findAllGrouped();
```

### 6. TODO with ownership

```typescript
// TODO(asbou): Replace polling with WebSocket once backend #89 is merged
// Tracking: https://github.com/org/repo/issues/89
```

### 7. Public API / function contracts (when non-obvious)

Only for functions where the name and types don't fully describe the contract:

```python
def calculate_sentiment_score(text: str, window: int = 30) -> float:
    """
    Returns a score from -1.0 (bearish) to 1.0 (bullish).
    window: number of trading days for rolling average.
    Raises ValueError if text is empty or window < 1.
    """
```

---

## When NOT to Comment

### Restating what the code says

```python
# BAD
user_count = len(users)  # Get the length of users list

# BAD
if is_active:  # Check if active
    process()
```

### Obvious variable declarations

```typescript
// BAD
const MAX_RETRIES = 3  // Maximum number of retries
const userId = user.id  // The user's ID
```

### Every function regardless of clarity

```php
// BAD — this function name already says everything
// Get all active patients
public function getActivePatients(): Collection
{
    return Patient::active()->get();
}
```

### Compensating for bad names

```python
# BAD — comment exists because the name is terrible
# x is the number of failed login attempts
if x > 5:
    lock_account()

# GOOD — rename it
if failed_login_attempts > 5:
    lock_account()
```

### Explaining control flow that reads naturally

```java
// BAD
// If the user is an admin, allow access
if (user.hasRole("ADMIN")) {
    grantAccess();
}
```

### Commented-out code

```python
# BAD — never commit commented-out code
# old_method = calculate_v1(data)
result = calculate_v2(data)
```

Git history exists. If the old code matters, reference the commit hash in a comment. If it doesn't, delete it.

---

## Language-Specific Rules

### PHP / Laravel (CREAMS)
- DocBlocks only on non-obvious public methods and complex queries
- Single-line comments for inline clarifications
- **No** `/** @return Collection */` on a function literally named `getPatients()`

### Python / FastAPI (RinggitSense, Sen2Nal)
- Docstrings on public functions with non-obvious contracts or ML-specific behaviour
- Type hints + good names replace most comments
- **Required:** financial calculation assumptions, ML model limitations, PDPA-sensitive operations

### TypeScript / React (Auto-Recruit, Portfolio, RinggitSense frontend)
- JSDoc only on exported functions/hooks that aren't self-evident
- No inline comments on standard React patterns (`useState`, `useEffect`, etc.)
- **Required:** non-obvious performance optimisations, browser compatibility workarounds

### Java / Spring Boot (Portfolio)
- Javadoc on public service methods with complex contracts
- No Javadoc on trivial getters/setters
- **Required:** transaction boundary decisions, security annotations rationale

---

## Density Target

A well-commented file has comments on **5–15% of lines** on average.

If you're approaching 30%+, stop and ask:
1. Are these comments explaining HOW? → Rewrite the code.
2. Are the names bad? → Rename.
3. Is the function too complex? → Extract.

---

## Summary Table

| Situation | Comment? |
|---|---|
| WHY a decision was made | ✅ Yes |
| Non-obvious side effect or gotcha | ✅ Yes |
| Workaround with ticket/issue reference | ✅ Yes |
| External algorithm or spec reference | ✅ Yes |
| Bug fix with context | ✅ Yes |
| TODO with owner | ✅ Yes |
| Public API with non-obvious contract | ✅ Yes |
| What the code clearly shows | ❌ No |
| Restating variable/function name | ❌ No |
| Standard language/framework patterns | ❌ No |
| Compensating for a bad name | ❌ No (rename instead) |
| Commented-out code | ❌ No (delete it) |
| Every function by default | ❌ No |
