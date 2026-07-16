---
name: security-review
description: Use when adding endpoints, handling user input or file uploads, touching auth or secrets, or before any deployment - OWASP-style cross-language checklist. Stack-specific depth lives in the laravel/springboot/python skills.
origin: ECC
---

# Security Review Checklist

## When to Activate

- Implementing authentication or authorization (any project)
- Handling user input or file uploads
- Creating new API endpoints
- Working with secrets or credentials
- Implementing payment features (RinggitSense)
- Storing or transmitting sensitive/personal data (CREAMS)
- Integrating third-party APIs

---

## 1. Secrets Management

```typescript
// NEVER hardcode secrets
const apiKey = "sk-proj-xxxxx"  // ❌ CRITICAL

// ALWAYS use environment variables
const apiKey = process.env.OPENAI_API_KEY
if (!apiKey) throw new Error('OPENAI_API_KEY not configured')
```

- [ ] No hardcoded API keys, tokens, passwords
- [ ] All secrets in environment variables
- [ ] `.env` files in `.gitignore`
- [ ] No secrets in git history (`git log --all --grep="password"`)

---

## 2. Input Validation (all languages)

```typescript
// TypeScript: use Zod
const schema = z.object({ email: z.string().email(), name: z.string().max(100) })
const validated = schema.parse(input)

// Python: use Pydantic
class CreateRequest(BaseModel):
    email: EmailStr
    name: str = Field(max_length=100)

// PHP/Laravel: use Form Requests
$request->validate(['email' => 'required|email', 'name' => 'required|max:100'])

// Java: use Bean Validation
@NotBlank @Email String email;
```

- [ ] All user inputs validated with schemas at system boundary
- [ ] File uploads: size, MIME type, extension validated
- [ ] Error messages don't leak internal details

---

## 3. SQL Injection Prevention

```php
// NEVER concatenate SQL
DB::select("SELECT * FROM users WHERE email = '$email'");  // ❌ CRITICAL

// ALWAYS use ORM or parameterized queries
User::where('email', $email)->first();
DB::select('SELECT * FROM users WHERE email = ?', [$email]);
```

```python
# NEVER
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")  # ❌

# ALWAYS
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
```

---

## 4. Authentication and Authorization

- [ ] Tokens stored in httpOnly cookies (NOT localStorage)
- [ ] Authorization check before every sensitive operation (not just authentication)
- [ ] Session regenerated on login/privilege escalation
- [ ] Short-lived tokens with refresh mechanism
- [ ] Rate limiting on auth endpoints

---

## 5. XSS Prevention

```typescript
import DOMPurify from 'isomorphic-dompurify'

// Sanitize before rendering user HTML
const clean = DOMPurify.sanitize(userHtml, { ALLOWED_TAGS: ['b', 'i', 'p'] })
```

- [ ] User-provided HTML sanitized before rendering
- [ ] CSP headers configured
- [ ] React's built-in escaping used (no `dangerouslySetInnerHTML` with unvalidated content)

---

## 6. Sensitive Data Exposure

```typescript
// BAD: Logging PII or credentials
console.log('User login:', { email, password })    // ❌

// GOOD: Log identifiers only
console.log('User login:', { userId, email })      // No password
```

- [ ] No passwords, tokens, or card numbers in logs
- [ ] Error messages generic for users; detailed errors in server logs only
- [ ] PDPA-sensitive data (CREAMS patient data, RinggitSense financial data) not in logs

---

## Pre-Deployment Security Checklist

```
- [ ] No hardcoded secrets in code or git history
- [ ] All user inputs validated
- [ ] All SQL queries parameterized
- [ ] XSS: user HTML sanitized
- [ ] CSRF protection active
- [ ] Auth: tokens in httpOnly cookies
- [ ] Authz: role checks on all sensitive endpoints
- [ ] Rate limiting on all API endpoints
- [ ] HTTPS enforced
- [ ] Security headers configured (CSP, HSTS, X-Frame-Options)
- [ ] No sensitive data in error responses or logs
- [ ] Dependencies up to date (npm audit / composer audit / pip-audit)
- [ ] PDPA compliance verified (CREAMS, RinggitSense)
- [ ] Financial disclaimers present (RinggitSense, Sen2Nal)
```
