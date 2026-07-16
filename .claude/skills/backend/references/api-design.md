# API Design Patterns

## URL Structure

```
GET    /api/v1/patients              # List
GET    /api/v1/patients/:id          # Single
POST   /api/v1/patients              # Create
PUT    /api/v1/patients/:id          # Replace
PATCH  /api/v1/patients/:id          # Update
DELETE /api/v1/patients/:id          # Delete

# Sub-resources
GET    /api/v1/patients/:id/assessments
POST   /api/v1/patients/:id/assessments

# Actions (sparingly — use verbs only when no CRUD mapping fits)
POST   /api/v1/patients/:id/discharge
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
```

**Naming rules:** plural, lowercase, kebab-case. No verbs in resource URLs.

## Status Codes

```
200 OK              — GET, PUT, PATCH success
201 Created         — POST success (include Location header)
204 No Content      — DELETE success
400 Bad Request     — Malformed JSON, invalid syntax
401 Unauthorized    — Missing/invalid authentication
403 Forbidden       — Authenticated, not authorized
404 Not Found       — Resource doesn't exist
409 Conflict        — Duplicate entry, state conflict
422 Unprocessable   — Valid JSON but semantically invalid (validation errors)
429 Too Many Requests — Rate limit exceeded
500 Internal Error  — Unexpected failure (never expose details)
```

**Never:** Return 200 for errors. Return 500 for validation errors.

## Response Format

```json
// Success
{ "data": { "id": "abc-123", "name": "Ahmad", "created_at": "2026-01-15T10:30:00Z" } }

// Collection with pagination
{
  "data": [...],
  "meta": { "total": 142, "page": 1, "per_page": 20, "total_pages": 8 },
  "links": { "self": "...", "next": "...", "last": "..." }
}

// Error
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": [
      { "field": "email", "message": "Must be a valid email address", "code": "invalid_format" }
    ]
  }
}
```

## Pagination

**Offset (simple, small datasets):**
```
GET /api/v1/patients?page=2&per_page=20
```

**Cursor (scalable, large datasets, feeds):**
```
GET /api/v1/patients?cursor=eyJpZCI6MTIzfQ&limit=20
```

Use cursor for lists that may grow large (CREAMS patient lists, RinggitSense transaction history).

## Filtering and Sorting

```
GET /api/v1/assessments?status=completed&assigned_to=123
GET /api/v1/transactions?amount[gte]=100&amount[lte]=1000
GET /api/v1/patients?sort=-created_at,name
GET /api/v1/patients?q=Ahmad
```

## Versioning

URL path versioning: `/api/v1/`, `/api/v2/`

Non-breaking changes (no version bump needed):
- Adding new fields to responses
- Adding new optional query parameters
- Adding new endpoints

Breaking changes (require new version):
- Removing or renaming fields
- Changing field types
- Changing URL structure

## Pre-Shipping Checklist

- [ ] URL follows naming conventions (plural, kebab-case, no verbs)
- [ ] Correct HTTP method and status codes
- [ ] Input validated with schema (Zod/Pydantic/Bean Validation/Form Request)
- [ ] Error responses follow standard format
- [ ] Pagination on list endpoints
- [ ] Authentication required (or explicitly marked public)
- [ ] Authorization checked (user can only access their resources)
- [ ] Rate limiting configured
- [ ] No internal details in error responses (stack traces, SQL errors)
- [ ] OpenAPI/Swagger spec updated
