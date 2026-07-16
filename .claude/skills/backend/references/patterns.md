# Backend Development Patterns

## Repository Pattern (abstract data access)

```typescript
interface PatientRepository {
  findAll(filters?: PatientFilters): Promise<Patient[]>
  findById(id: string): Promise<Patient | null>
  create(data: CreatePatientDto): Promise<Patient>
  update(id: string, data: UpdatePatientDto): Promise<Patient>
  delete(id: string): Promise<void>
}
```

## Service Layer (business logic)

```typescript
class PatientService {
  constructor(private patientRepo: PatientRepository, private cache: Cache) {}

  async getActive(): Promise<Patient[]> {
    return this.cache.remember('patients.active', 300, () =>
      this.patientRepo.findAll({ status: 'active' })
    )
  }
}
```

## N+1 Query Prevention

```typescript
// BAD: N+1
const patients = await getPatients()
for (const p of patients) {
  p.assessments = await getAssessments(p.id)  // N queries
}

// GOOD: Batch fetch
const patients = await getPatients()
const ids = patients.map(p => p.id)
const assessments = await getAssessmentsByPatientIds(ids)  // 1 query
const map = new Map(patients.map(p => [p.id, []]))
assessments.forEach(a => map.get(a.patientId)?.push(a))
patients.forEach(p => { p.assessments = map.get(p.id) ?? [] })
```

## Transactions

```typescript
async function createPatientWithAssessment(patientData, assessmentData) {
  return db.transaction(async (trx) => {
    const patient = await trx('patients').insert(patientData).returning('*')
    const assessment = await trx('assessments')
      .insert({ ...assessmentData, patient_id: patient[0].id })
      .returning('*')
    return { patient: patient[0], assessment: assessment[0] }
  })
}
```

## Caching (Cache-Aside Pattern)

```typescript
class CachedRepository {
  async findById(id: string): Promise<Patient | null> {
    const cached = await this.redis.get(`patient:${id}`)
    if (cached) return JSON.parse(cached)

    const patient = await this.baseRepo.findById(id)
    if (patient) {
      await this.redis.setex(`patient:${id}`, 300, JSON.stringify(patient))
    }
    return patient
  }

  async invalidate(id: string): Promise<void> {
    await this.redis.del(`patient:${id}`)
  }
}
```

## Error Handling (centralized)

```typescript
class ApiError extends Error {
  constructor(public statusCode: number, public message: string) { super(message) }
}

export function errorHandler(error: unknown): Response {
  if (error instanceof ApiError) {
    return NextResponse.json({ error: { message: error.message } }, { status: error.statusCode })
  }
  if (error instanceof z.ZodError) {
    return NextResponse.json({ error: { code: 'validation_error', details: error.errors } }, { status: 400 })
  }
  console.error('Unexpected:', error)
  return NextResponse.json({ error: { message: 'Internal server error' } }, { status: 500 })
}
```

## Rate Limiting

```typescript
const limiter = new Map<string, number[]>()

function checkRateLimit(key: string, max: number, windowMs: number): boolean {
  const now = Date.now()
  const requests = (limiter.get(key) || []).filter(t => now - t < windowMs)
  if (requests.length >= max) return false
  requests.push(now)
  limiter.set(key, requests)
  return true
}
```

## Retry with Exponential Backoff

```typescript
async function withRetry<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try { return await fn() }
    catch (err) {
      if (i < maxRetries - 1) {
        await new Promise(r => setTimeout(r, Math.pow(2, i) * 1000))
      } else throw err
    }
  }
  throw new Error('unreachable')
}
```

## Performance Target

All database queries must complete in <200ms (SOP Section 4.3). Queries exceeding this threshold require: indexing review, query optimization, or caching layer.
