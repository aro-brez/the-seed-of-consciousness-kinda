# LUNA Technical Deep-Dive: Feedback Loop Architecture

**For:** Development team, ARŌ
**Purpose:** Technical details for implementation planning

---

## Data Flow Architecture

### Current State (Read-Only):

```typescript
// 1. Hook initiates fetch
useGrowthData() {
  fetchData() → /api/metrics/sheet
}

// 2. API reads from Sheets
GET /api/metrics/sheet {
  fetch('https://sheets.googleapis.com/v4/spreadsheets/...')
  return { success: true, metrics: {...}, timestamp: now }
}

// 3. Frontend displays
MomentumDashboard {
  const { metrics, loading, error, refresh } = useGrowthData()
  return (<MomentumHero metrics={metrics} onRefresh={refresh} />)
}

// 4. ❌ No write-back
// User can't save anything
```

### Proposed Enhancement (Write-Back):

```typescript
// 1. User submits feedback
<FeedbackForm onSubmit={(feedback) => {
  saveFeedback(feedback)
  publishToCollective(feedback)
  updateSheet(feedback)
}} />

// 2. API writes to Sheets
POST /api/metrics/sheet/edit {
  action: "update",
  range: "FEEDBACK!A1:D10",
  value: userFeedback
}

// 3. Publish to collective
nats_publish({
  channel: "owl.all",
  content: "LUNA: User flagged CAC anomaly - detected spike from $65 to $120"
})

// 4. Update source of truth
Google Sheets updated with user corrections
```

---

## Hook Deep-Dive: useGrowthData

### State Management:
```typescript
const [metrics, setMetrics] = useState<ComprehensiveMetrics | null>(null)
const [loading, setLoading] = useState(true)
const [error, setError] = useState<string | null>(null)
const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
const [isLiveMode, setIsLiveMode] = useState(false)
const [backoffLevel, setBackoffLevel] = useState(0)

// Refs for performance
const prevDataHashRef = useRef<string | null>(null)
const retryCountRef = useRef(0)
```

### Key Constants:
```typescript
const LIVE_INTERVAL = 5000              // 5 seconds
const BASE_INTERVAL = 15000             // 15 seconds
const MAX_INTERVAL = 12 * 60 * 60 * 1000 // 12 hours

// Backoff steps (exponential)
const BACKOFF_STEPS = [
  15000,      // Level 0: 15 seconds
  15000,      // Level 1: 15 seconds (hold)
  30000,      // Level 2: 30 seconds
  60000,      // Level 3: 1 minute
  300000,     // Level 4: 5 minutes
  900000,     // Level 5: 15 minutes
  3600000,    // Level 6: 1 hour
  MAX_INTERVAL // Level 7: 12 hours
]

const STALE_THRESHOLD_MS = 5 * 60 * 1000 // 5 minutes
```

### Fetch Logic with Backoff:
```typescript
const fetchData = useCallback(async (isManualRefresh = false) => {
  try {
    setError(null)

    // 1. Fetch with no-store (bypass cache)
    const response = await fetch('/api/metrics/sheet', {
      cache: 'no-store'
    })

    // 2. Handle rate limiting (529)
    if (response.status === 529) {
      retryCountRef.current += 1
      const retryDelay = getRetryDelay(retryCountRef.current)
      // Exponential backoff: 1s, 2s, 4s, 8s... max 30s
      setTimeout(() => fetchData(isManualRefresh), retryDelay)
      return
    }

    // 3. Reset retry count on success
    retryCountRef.current = 0

    // 4. Check response
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.message || `HTTP ${response.status}`)
    }

    // 5. Parse metrics
    const data = await response.json()
    if (!data.success) {
      throw new Error(data.error || 'Failed to fetch metrics')
    }

    // 6. Check if data changed (using hash)
    const newHash = hashData(data.metrics)
    const dataChanged = prevDataHashRef.current !== newHash
    prevDataHashRef.current = newHash

    // 7. Update backoff level based on change
    if (dataChanged || isManualRefresh) {
      setBackoffLevel(0)  // Data changed → fast polling
    } else {
      setBackoffLevel(prev =>
        Math.min(prev + 1, BACKOFF_STEPS.length - 1)
      )  // No change → slow down
    }

    // 8. Update state
    setMetrics(data.metrics)
    setLastUpdated(new Date())

  } catch (err) {
    setError(err instanceof Error ? err.message : 'Unknown error')
  } finally {
    setLoading(false)
  }
}, [])
```

### Hash Function (Change Detection):
```typescript
const hashData = (data: ComprehensiveMetrics): string => {
  return JSON.stringify({
    y: data.yesterday,   // Yesterday's metrics
    t: data.today,       // Today's metrics
    p: data.pacing       // Pacing/progress
  })
}
```

**Why not full hash?** Only hashes changed-frequently fields to avoid recalculating for cosmetic updates.

### Auto-Refresh with Dynamic Interval:
```typescript
// Calculate current interval
const currentInterval = isLiveMode
  ? LIVE_INTERVAL  // 5 seconds if live mode
  : BACKOFF_STEPS[Math.min(backoffLevel, BACKOFF_STEPS.length - 1)]

// Set up interval
useEffect(() => {
  const intervalWithJitter = addJitter(currentInterval)
  const interval = setInterval(() => fetchData(), intervalWithJitter)
  return () => clearInterval(interval)
}, [fetchData, currentInterval])

// Jitter function
function addJitter(interval: number): number {
  return interval + Math.random() * 500
}
```

### Return Value:
```typescript
return {
  metrics,              // ComprehensiveMetrics | null
  loading,              // boolean
  error,                // string | null
  lastUpdated,          // Date | null
  isStale,              // boolean (error && metrics && < 5min old)
  isLiveMode,           // boolean
  currentInterval,      // number (ms)
  refresh,              // () => Promise<void> (manual refresh)
  toggleLiveMode        // () => void
}
```

---

## API Route: /api/metrics/sheet

### Fetch Flow:
```typescript
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const department = searchParams.get("department") || "exec"

  try {
    // 1. Get unified metrics (from Sheets + calculation)
    const metrics = await getUnifiedMetrics()

    // 2. Generate department-specific insight
    const oneThing = generateDynamicOneThing(metrics, department)

    // 3. Return with timestamp
    return NextResponse.json({
      success: true,
      metrics,
      oneThing,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error("Metrics API error:", error)
    return NextResponse.json(
      { success: false, error: "Failed to fetch metrics" },
      { status: 500 }
    )
  }
}
```

### Error Handling:
```typescript
// Missing credentials
if (!GOOGLE_SHEETS_API_KEY || !GOOGLE_SHEETS_SPREADSHEET_ID) {
  throw new Error('Missing Google Sheets credentials')
}

// API call failed
const response = await fetch(url)
if (!response.ok) {
  const error = await response.text()
  throw new Error(`Google Sheets API error: ${error}`)
}
```

### Data Sources:
```typescript
// From Forecast Sheet - February:
// K: Spend Actual
// N: Sales Actual
// Q: Subscription Sales (Actual)
// S: Non Subscription Sales
// T: Non Subscription Actual

// Then computed:
const cac = spend / totalOrders        // Blended CAC
const takeRate = revenue / totalSpend  // Take rate %
const pacing = mtdSubs / dailyTarget   // % of monthly target
```

---

## API Route: /api/metrics/sheet/edit (Unused)

### Structure:
```typescript
// Get fresh access token
async function getAccessToken(): Promise<string> {
  const response = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    body: new URLSearchParams({
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,
      refresh_token: REFRESH_TOKEN,
      grant_type: 'refresh_token'
    })
  })
  return data.access_token
}

// Update a single cell
async function updateCell(
  accessToken: string,
  range: string,
  value: string | number
): Promise<void> {
  const url = `https://sheets.googleapis.com/v4/spreadsheets/${SPREADSHEET_ID}/values/${range}?valueInputOption=USER_ENTERED`

  await fetch(url, {
    method: 'PUT',
    headers: { 'Authorization': `Bearer ${accessToken}` },
    body: JSON.stringify({
      values: [[value]]
    })
  })
}

// Update multiple cells
async function batchUpdate(
  accessToken: string,
  updates: Array<{ range: string; value: string | number }>
): Promise<void> {
  // POST /values:batchUpdate with array of updates
}

// Read a range
async function readRange(
  accessToken: string,
  range: string
): Promise<string[][]> {
  // GET /values/{range}
  // Returns 2D array
}
```

### POST Handler:
```typescript
export async function POST(request: NextRequest) {
  const body = await request.json()
  const { action, range, value, updates } = body
  const accessToken = await getAccessToken()

  switch (action) {
    case 'update':
      await updateCell(accessToken, range, value)
      return { success: true, message: `Updated ${range}` }

    case 'batch':
      await batchUpdate(accessToken, updates)
      return { success: true, message: `Updated ${updates.length} cells` }

    case 'read':
      const data = await readRange(accessToken, range)
      return { success: true, data }

    default:
      return { error: 'Unknown action' }
  }
}
```

### Current Usage: ❌ Never called from frontend

### How to Use (When Enabled):
```typescript
// Example 1: User corrections
const updateCAC = async (newCAC: number) => {
  const response = await fetch('/api/metrics/sheet/edit', {
    method: 'POST',
    body: JSON.stringify({
      action: 'update',
      range: 'FORECAST!BU33',  // CAC cell
      value: newCAC
    })
  })
  return response.json()
}

// Example 2: Batch write (multiple cells)
const saveDailyActuals = async (spend, subs) => {
  const response = await fetch('/api/metrics/sheet/edit', {
    method: 'POST',
    body: JSON.stringify({
      action: 'batch',
      updates: [
        { range: 'DAILY!K15', value: spend },
        { range: 'DAILY!Q15', value: subs }
      ]
    })
  })
  return response.json()
}

// Example 3: Read range
const readForecast = async () => {
  const response = await fetch('/api/metrics/sheet/edit', {
    method: 'POST',
    body: JSON.stringify({
      action: 'read',
      range: 'FORECAST!K1:T30'
    })
  })
  return response.json()
}
```

---

## Proposed Enhancement: FeedbackForm Component

### Component Structure:
```typescript
'use client'

import { useState } from 'react'
import { AlertCircle, Flag, Send } from 'lucide-react'

interface Feedback {
  type: 'correction' | 'anomaly' | 'update_request' | 'note'
  metric: string // 'cac', 'subs', 'spend', etc
  oldValue?: number | string
  newValue?: number | string
  reason: string
  timestamp: Date
  userId?: string
}

export function FeedbackForm({ onSubmit }: { onSubmit: (feedback: Feedback) => void }) {
  const [feedbackType, setFeedbackType] = useState<Feedback['type']>('correction')
  const [metric, setMetric] = useState('')
  const [reason, setReason] = useState('')
  const [oldValue, setOldValue] = useState('')
  const [newValue, setNewValue] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      const feedback: Feedback = {
        type: feedbackType,
        metric,
        reason,
        timestamp: new Date(),
        ...(feedbackType === 'correction' && { oldValue, newValue })
      }

      // 1. Save to backend
      const response = await fetch('/api/feedback', {
        method: 'POST',
        body: JSON.stringify(feedback)
      })

      if (response.ok) {
        // 2. Publish to collective
        await fetch('/api/nats/publish', {
          method: 'POST',
          body: JSON.stringify({
            channel: 'owl.all',
            content: `${feedbackType.toUpperCase()}: ${metric} - ${reason}`
          })
        })

        // 3. Optional: Update Sheets
        if (feedbackType === 'correction') {
          await updateSheets(metric, newValue)
        }

        // 4. Notify user
        onSubmit(feedback)

        // Reset form
        setReason('')
        setOldValue('')
        setNewValue('')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="p-4 border rounded-lg">
      <h3 className="font-bold mb-4">Report Issue / Correction</h3>

      <select value={feedbackType} onChange={(e) => setFeedbackType(e.target.value as any)}>
        <option value="correction">Data Correction</option>
        <option value="anomaly">Anomaly Flag</option>
        <option value="update_request">Request Update</option>
        <option value="note">Team Note</option>
      </select>

      <select value={metric} onChange={(e) => setMetric(e.target.value)}>
        <option value="">Select Metric</option>
        <option value="cac">CAC</option>
        <option value="subs">Subscriptions</option>
        <option value="spend">Ad Spend</option>
        <option value="take_rate">Take Rate</option>
      </select>

      {feedbackType === 'correction' && (
        <>
          <input
            type="number"
            placeholder="Old Value"
            value={oldValue}
            onChange={(e) => setOldValue(e.target.value)}
          />
          <input
            type="number"
            placeholder="New Value"
            value={newValue}
            onChange={(e) => setNewValue(e.target.value)}
          />
        </>
      )}

      <textarea
        placeholder="Reason / Details"
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        required
      />

      <button
        type="submit"
        disabled={isSubmitting}
        className="px-4 py-2 bg-[#e3f98a] text-[#0a0a0f] rounded-lg font-bold"
      >
        {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
      </button>
    </form>
  )
}
```

### Backend for Feedback:
```typescript
// POST /api/feedback
export async function POST(request: NextRequest) {
  const feedback = await request.json()

  try {
    // 1. Validate
    const validated = FeedbackSchema.parse(feedback)

    // 2. Save to database
    const saved = await db.feedback.create(validated)

    // 3. Optionally update Sheets
    if (feedback.type === 'correction') {
      await updateSheetCell(feedback.metric, feedback.newValue)
    }

    // 4. Return
    return NextResponse.json({
      success: true,
      feedbackId: saved.id
    })

  } catch (error) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 400 }
    )
  }
}
```

---

## Environment Variables Needed

### Current:
```bash
GOOGLE_SHEETS_API_KEY=<key>
GOOGLE_SHEETS_SPREADSHEET_ID=<id>
GOOGLE_CLIENT_ID=<id>
GOOGLE_CLIENT_SECRET=<secret>
GOOGLE_REFRESH_TOKEN=<token>
```

### For Feedback Enhancement:
```bash
# Database
DATABASE_URL=postgresql://...

# Feedback storage
FEEDBACK_TABLE=feedback

# NATS
NATS_URL=nats://192.168.5.108:4222

# Analytics
SENTRY_DSN=... (optional, for error tracking)
```

---

## Implementation Roadmap

### Phase 1: Enable Write-Back (Week 1)
- [ ] Test `/api/metrics/sheet/edit` endpoint
- [ ] Create `FeedbackForm` component
- [ ] Add POST `/api/feedback` route
- [ ] Hook feedback form to dashboard

### Phase 2: Data Validation (Week 2)
- [ ] Create Zod schemas for metrics
- [ ] Add validation layer to API
- [ ] Show validation errors to user
- [ ] Log validation failures

### Phase 3: Audit Trail (Week 2-3)
- [ ] Create feedback table in DB
- [ ] Log all changes with who/what/when
- [ ] Add audit view to dashboard
- [ ] Enable recovery/rollback

### Phase 4: Collaboration (Week 3)
- [ ] Add comments component
- [ ] Enable anomaly flagging
- [ ] Publish to collective via NATS
- [ ] Show team feedback on dashboard

### Phase 5: Better Error Communication (Week 4)
- [ ] Display rate limit status
- [ ] Show data freshness details
- [ ] Add specific recovery actions
- [ ] Implement error tracking with Sentry

---

## Testing Strategy

### Unit Tests:
```typescript
describe('useGrowthData', () => {
  it('should detect data changes and reset backoff', async () => {
    // Setup
    const { result } = renderHook(() => useGrowthData())

    // Initial fetch
    await waitFor(() => expect(result.current.metrics).toBeDefined())

    // Verify backoff level 0 after change
    expect(result.current.currentInterval).toBe(15000)
  })

  it('should increase backoff when data unchanged', async () => {
    // Setup with mock that returns same data
    const { result } = renderHook(() => useGrowthData())

    // Wait for multiple fetches
    await waitFor(() => expect(result.current.currentInterval).toBeGreaterThan(15000))
  })
})
```

### Integration Tests:
```typescript
describe('Feedback Flow', () => {
  it('should save feedback and update Sheets', async () => {
    // Submit feedback
    const response = await fetch('/api/feedback', {
      method: 'POST',
      body: JSON.stringify(testFeedback)
    })

    // Verify saved
    expect(response.ok).toBe(true)

    // Verify Sheets updated
    const sheetValue = await readSheetCell('FEEDBACK!A1')
    expect(sheetValue).toBe(testFeedback.newValue)
  })
})
```

---

**Created by LUNA (RECEIVE Phase)**
**For development implementation**
**Part of 8OWLS Collective Intelligence**
