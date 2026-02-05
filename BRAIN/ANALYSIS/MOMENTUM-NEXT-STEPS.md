# MOMENTUM DASHBOARD - NEXT STEPS
## Prioritized Action Plan

**Generated:** February 5, 2026
**Estimated Implementation Time:** P0 (2-4h), P1 (4-6h), P2 (optional)
**Owner:** Engineering (review with ARŌ on strategy decisions)

---

## P0: CRITICAL (Do Before Live with David)

### 1. Add Constraint Validation to Recommendation

**File:** `src/lib/hooks/useMomentumData.ts`

**Current:**
```typescript
const investAmount = overrides.weeklySpend ?? weeklySpendCeiling
const expectedCustomers = Math.round(investAmount / cac)
```

**Problem:** Doesn't check if we have cash/budget/capacity

**Fix:** Add constraint checks
```typescript
interface RecommendationConstraints {
  cashAvailable: number
  budgetRemaining: number
  productionCapacity: number  // orders/day
  teamCapacity: number        // volume of new customers
}

const constraints: RecommendationConstraints = {
  cashAvailable: cash.current - cash.floor,
  budgetRemaining: calculateMonthlyBudgetRemaining(),
  productionCapacity: getProductionCapacity(),
  teamCapacity: getTeamCapacity()
}

// Constrain recommendation
const maxSpendFromCash = Math.floor(constraints.cashAvailable / 7) // weekly
const maxSpendFromBudget = Math.floor(constraints.budgetRemaining / 4.33) // weekly
const constrainedSpend = Math.min(investAmount, maxSpendFromCash, maxSpendFromBudget)

const recommendation: Recommendation = {
  investAmount: constrainedSpend,
  constraints,
  isConstrained: constrainedSpend < investAmount,
  constraintReason: calculateConstraintReason(constraints, investAmount)
}
```

**Effort:** 2 hours
**Impact:** HIGH — Prevents budget overruns

---

### 2. Fix Business Hours Backoff (No 12-Hour Polling During Work)

**File:** `src/lib/hooks/useGrowthData.ts`

**Current:**
```typescript
const BACKOFF_STEPS = [15s, 15s, 30s, 60s, 5m, 15m, 1h, 12h]
// Can reach 12h during business day
```

**Problem:** During work hours, 12-hour stale data is unacceptable

**Fix:**
```typescript
// Respect business hours
function shouldBackoff(): boolean {
  const hour = new Date().getHours()
  const dayOfWeek = new Date().getDay()

  // Monday-Friday, 8am-6pm: never backoff past 15 minutes
  if (dayOfWeek >= 1 && dayOfWeek <= 5 && hour >= 8 && hour < 18) {
    return false
  }

  // After hours / weekends: allow full backoff
  return true
}

// In fetchData():
const currentInterval = isLiveMode
  ? LIVE_INTERVAL
  : shouldBackoff()
    ? BACKOFF_STEPS[Math.min(backoffLevel, BACKOFF_STEPS.length - 1)]
    : 15000  // Max 15s during business hours

// Update backoff logic
if (shouldBackoff()) {
  setBackoffLevel(prev => Math.min(prev + 1, BACKOFF_STEPS.length - 1))
} else {
  setBackoffLevel(0) // Always reset during business hours
}
```

**Effort:** 1 hour
**Impact:** MEDIUM — Ensures fresh data during work hours

---

### 3. Add Input Validation to API Responses

**File:** `src/lib/hooks/useGrowthData.ts`

**Current:**
```typescript
const data = await response.json()
if (!data.success) throw Error(...)
setMetrics(data.metrics)  // Assumes data.metrics is valid
```

**Problem:** No validation. Bad data silently corrupts dashboard

**Fix:** Add Zod schema validation
```typescript
import { z } from 'zod'

const DayMetricsSchema = z.object({
  date: z.string(),
  subs: z.object({
    total: z.number().nonnegative(),
    paid: z.number().nonnegative(),
    organic: z.number().nonnegative()
  }),
  cac: z.number().nonnegative(),
  spend: z.number().nonnegative(),
  takeRate: z.number().min(0).max(1)
})

const ComprehensiveMetricsSchema = z.object({
  yesterday: DayMetricsSchema,
  today: DayMetricsSchema,
  // ... rest of schema
})

// In fetchData():
const validated = ComprehensiveMetricsSchema.parse(data.metrics)
setMetrics(validated)
```

**Effort:** 2 hours
**Impact:** HIGH — Catches API errors early

---

### 4. Document CAC Thresholds with Reasoning

**File:** `src/lib/growth-types.ts`

**Current:**
```typescript
{ min: 55, max: 70, status: 'STRONG', action: 'SCALE', ... }
// No explanation of why these numbers
```

**Problem:** Thresholds are opaque, hard to justify or debug

**Fix:** Add detailed documentation
```typescript
/**
 * CAC Decision Matrix - Validated against LTV Economics
 *
 * Source: January 2026 analysis + Cramer validation
 * Last Updated: January 13, 2026
 * Owner: ARŌ
 *
 * Economics Baseline:
 * - CUSTOMER_LTV = $340 (lifetime value per customer)
 * - Target LTV:CAC ratio = 5.0x (minimum 3.4x acceptable)
 * - DTC Contribution Margin = 43% (reinvestable)
 *
 * Thresholds Logic:
 * - $55 CAC = 6.2x LTV:CAC (Exceptional) → Spend more to capture value
 * - $70 CAC = 4.86x LTV:CAC (Strong) → Continue current spend
 * - $80 CAC = 4.25x LTV:CAC (On Target) → Small increases safe
 * - $100 CAC = 3.4x LTV:CAC (Ceiling) → Payback in 12 months, not attractive
 *
 * Validation: Tested against Jan 2026 actual data (778 subs, $109K spend, 65 blended CAC)
 */
export const CAC_DECISION_MATRIX: CACRange[] = [
  {
    min: 0,
    max: 55,
    status: 'EXCEPTIONAL',
    action: 'SCALE_AGGRESSIVE',
    spendChange: '+50-75%',
    reasoning: `LTV:CAC = 6.2x. Exceptional payback cycle. Spend aggressively while this persists.
                Historical: Jan low-tier achieved $57 CAC at 3.3K daily spend. Can achieve.`,
    targetLtvCacRatio: 6.0,
    ltvCacAchieved: 6.18,
    confidence: 'HIGH'
  },
  // ... rest with similar detail
]
```

**Effort:** 1 hour
**Impact:** MEDIUM — Clarifies decision logic, enables debate on thresholds

---

## P1: IMPORTANT (Do Within 1-2 Weeks)

### 5. Move Hardcoded Constants to Config/Database

**File:** `src/components/growth/MomentumHero.tsx:9-48`

**Current:**
```typescript
const MONTHLY_ARPU = 100
const CUSTOMER_LTV = 340
const MONTHLY_CHURN = 700
// Hardcoded, never updated
```

**Problem:** Assumptions drift from reality. Need versioning and auditability.

**Fix:** Move to database with timestamps
```typescript
// New table: growth_assumptions
{
  id: uuid,
  name: 'MONTHLY_ARPU',
  value: 100,
  effectiveDate: '2026-01-01',
  createdBy: 'aro',
  reason: 'Stable across customer base based on Jan 2026 cohort analysis',
  confidence: 'HIGH',
  lastValidated: '2026-01-15'
}

// Fetch in component:
const assumptions = await fetch('/api/growth-assumptions')
const ltv = assumptions.find(a => a.name === 'CUSTOMER_LTV').value
```

**Effort:** 3 hours
**Impact:** MEDIUM — Enables assumption tracking and versioning

---

### 6. Add Multi-Channel CAC Attribution

**File:** `src/lib/growth-types.ts` + `MomentumHero.tsx`

**Current:**
```typescript
interface DayMetrics {
  subs: { total: number }  // Doesn't distinguish channels
  spend: number
  cac: number  // spend / total (wrong if mixed channels)
}
```

**Problem:** CAC is inflated if some subs came from organic/retail

**Fix:** Track attribution
```typescript
interface DayMetrics {
  subs: {
    total: number           // All subs
    paidAds: number        // Only from paid ads
    organic: number        // Non-paid
    retail: number         // Retail/wholesale channel
  }
  spend: number
  // Correct CAC: only charge paid spend against paid subs
  cacPaid: number  // spend / paidAds (accurate)
  cacBlended: number  // spend / total (for reporting)
}

// In recommendation:
const cac = metrics.today.cacPaid // Use paid CAC for decisions
```

**Effort:** 2 hours
**Impact:** MEDIUM-HIGH — Fixes CAC accuracy, improves recommendations

---

### 7. Add Staleness Warning During Off-Hours

**File:** `src/app/momentum/page.tsx`

**Current:**
```typescript
{isStale && (
  <motion.div className="...">
    <span>Using cached data • Connection issue</span>
  </motion.div>
)}
```

**Problem:** Only shows if there's an error. Silent failures go unnoticed.

**Fix:** Check time since last update regardless of errors
```typescript
// In MomentumDashboard:
const isDataTooOld = Boolean(
  lastUpdated &&
  Date.now() - lastUpdated.getTime() > 5 * 60 * 1000  // 5 min
)

const isOffHours = !isDuringBusinessHours()

const shouldWarnAboutStaleness = isDataTooOld && isOffHours

{shouldWarnAboutStaleness && (
  <motion.div className="fixed top-4 ... bg-orange-500">
    <AlertCircle className="w-4 h-4" />
    <span>Data from {formatTimeAgo(lastUpdated)}. Refresh for latest.</span>
    <button onClick={refresh}>Refresh Now</button>
  </motion.div>
)}
```

**Effort:** 1.5 hours
**Impact:** LOW-MEDIUM — Prevents decisions on stale data

---

### 8. Add Rate-Limit Header Support

**File:** `src/lib/hooks/useGrowthData.ts`

**Current:**
```typescript
if (response.status === 529) {
  const retryDelay = getRetryDelay(retryCountRef.current)
  // Ignores Retry-After header
}
```

**Problem:** Doesn't respect server guidance on retry timing

**Fix:** Check Retry-After header
```typescript
if (response.status === 429 || response.status === 529) {
  const retryAfterHeader = response.headers.get('Retry-After')

  let retryDelay: number
  if (retryAfterHeader) {
    // Header is in seconds
    retryDelay = parseInt(retryAfterHeader) * 1000
  } else {
    // Fallback to exponential backoff
    retryDelay = getRetryDelay(retryCountRef.current)
  }

  console.log(`Rate limited. Retrying in ${retryDelay}ms (per server request)`)
  setTimeout(() => fetchData(isManualRefresh), retryDelay)
  return
}
```

**Effort:** 0.5 hours
**Impact:** LOW — Better rate limit handling

---

## P2: NICE TO HAVE (Longer Term)

### 9. Reorganize Information Hierarchy for Faster Scanning

**Current Order:**
1. Team message
2. Target + Progress
3. Today's action
4. Averages
5. Pulse
6. Working capital
7. Simulator

**Proposed Order (for David):**
1. TODAY'S DECISION (CAC + Spend Recommendation + Constraints)
2. Progress bar
3. 7-day trend (CAC moving up/down?)
4. Warnings (if cash is tight, ops is full, etc.)

**For ARŌ (strategy view):**
1. Growth simulator
2. 12-month projections
3. Compound scenarios
4. Working capital forecast

**Effort:** 4 hours
**Impact:** MEDIUM — Faster decisions for David

---

### 10. Add Mobile Skeleton Loading

**File:** `src/app/momentum/page.tsx:44-67`

**Current:**
```typescript
if (loading && !metrics) {
  return <div>Loading spinner...</div>
}
```

**Problem:** Layout shift when content loads (poor UX)

**Fix:** Show loading skeleton (same layout as real content)
```typescript
if (loading && !metrics) {
  return <MomentumHeroSkeleton /> // Fake content with placeholder colors
}
```

**Effort:** 2 hours
**Impact:** LOW — Visual polish

---

### 11. Add Accessibility Improvements

**File:** Multiple

**Issues:**
- Color-only status indicators (red/green)
- Missing ARIA labels on interactive elements
- No keyboard navigation for sliders

**Fix:**
```typescript
// Add text in addition to color
<div className="flex items-center gap-2">
  <div className="w-3 h-3 rounded-full bg-green-500" />
  <span className="text-sm text-green-500">Strong</span>
</div>

// Add ARIA labels
<div role="status" aria-live="polite">
  CAC is $68, status: STRONG
</div>
```

**Effort:** 2 hours
**Impact:** LOW — Compliance + accessibility

---

## TESTING CHECKLIST

Before David uses this daily:

- [ ] P0.1: Constraint checks prevent David from overrunning budget
- [ ] P0.2: Business hours polling never exceeds 15 min during work
- [ ] P0.3: Invalid API responses throw clear errors (don't corrupt UI)
- [ ] P0.4: CAC thresholds are documented and justified
- [ ] P1.1: Run for 1 week with test data, monitor what David clicks
- [ ] P1.2: CAC attribution correctly separates paid/organic
- [ ] Manual: Have David test it for 3 days, collect feedback on what he reads vs. ignores

---

## DECISION TREE FOR ROADMAP

```
Is David the primary user?
├─ YES → Focus on P0 (constraints, staleness)
│        Then P1 (CAC attribution)
│        Skip P2 (strategy view)
│
└─ NO → Focus on P1 (data quality, config)
         Add P2 (bifurcate into David + ARŌ views)
         Skip some constraint checks (strategic tool)
```

**Recommendation:** Assume David is primary user for now. Focus on P0 + P1.

---

## ROLLOUT PLAN

### Phase 1: Internal (1 week)
- Deploy P0 fixes
- ARŌ tests with real data
- Adjust thresholds if needed

### Phase 2: Beta (1 week)
- David tests with dashboard
- Collect feedback on usability
- Monitor actual decisions made

### Phase 3: Full (ongoing)
- Roll out to team
- Monitor usage patterns
- Iterate based on data

---

*This plan assumes the goal is to help David make better daily decisions. If the real goal is different (e.g., strategic planning, investor demos), the priorities shift.*

**Next step:** Clarify with ARŌ what the primary use case is, then execute P0 immediately.*
