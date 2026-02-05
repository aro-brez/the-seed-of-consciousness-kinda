# MOMENTUM DASHBOARD - CODE REVIEW
## Technical Assessment + Architecture Concerns

**Reviewer:** SØWL (Code Review Phase)
**Files Analyzed:**
- `/src/app/momentum/page.tsx` (Dashboard page)
- `/src/components/growth/MomentumHero.tsx` (Hero component)
- `/src/lib/hooks/useMomentumData.ts` (Data hook)
- `/src/lib/hooks/useGrowthData.ts` (Data fetching)
- `/src/lib/growth-types.ts` (Type definitions)
- `/src/lib/data/source-of-truth.ts` (Constants)

---

## STRENGTHS

### 1. Clean Type Safety
```typescript
// Excellent type definitions in growth-types.ts
export interface ComprehensiveMetrics { ... }
export interface SpendRecommendation { ... }
export type CACStatus = 'EXCEPTIONAL' | 'STRONG' | 'ON_TARGET' | ...
```
**Why good:** Every data structure is explicit. No ambiguous nulls or type-coercion footguns.

### 2. Deliberate Backoff Strategy
```typescript
// useGrowthData.ts - Smart polling with exponential backoff
const BACKOFF_STEPS = [15s, 15s, 30s, 60s, 5m, 15m, 1h, 12h]
// Detects data changes, resets backoff if fresh data arrives
if (dataChanged || isManualRefresh) { setBackoffLevel(0) }
```
**Why good:** Avoids thundering herd on unchanged data. Respects rate limits.

### 3. Graceful Error Handling
```typescript
// 529 rate limiting retry logic
if (response.status === 529) {
  retryCountRef.current += 1
  const retryDelay = getRetryDelay(retryCountRef.current)
  setTimeout(() => fetchData(isManualRefresh), retryDelay)
  return
}
```
**Why good:** Automatic recovery without losing state.

### 4. Rich Calculation Engine
The `calculateCompoundGrowth()` function correctly models:
- Multi-cohort retention
- Retention curves that decay over time
- Contribution margin reinvestment
- Realistic financial projections

**Why good:** The math is sound. Comments explain each step.

### 5. Data Overrides Pattern
```typescript
export function saveOverrides(overrides: DataOverrides): void {
  localStorage.setItem('brez-data-overrides', JSON.stringify(overrides))
}
// Later: const overrides = getOverrides()
```
**Why good:** Allows experimentation (change assumptions, see projections) without backend changes.

---

## CRITICAL ISSUES

### Issue 1: CAC Thresholds Are Magic Numbers (No Validation)

**Location:** `src/lib/growth-types.ts:123-178`

```typescript
const CAC_DECISION_MATRIX: CACRange[] = [
  { min: 0,   max: 55,  status: 'EXCEPTIONAL', action: 'SCALE_AGGRESSIVE', ... },
  { min: 55,  max: 70,  status: 'STRONG',      action: 'SCALE', ... },
  { min: 70,  max: 80,  status: 'ON_TARGET',   action: 'SCALE_MODEST', ... },
  ...
]
```

**The Problem:**
- No comment explaining WHY these thresholds
- No doc linking to LTV math or historical performance
- No validation that these are better than alternatives
- Hardcoded, not configurable

**Example:** Is $55 EXCEPTIONAL because:
- LTV:CAC is 6.2x? (40% of companies would accept 3.4x)
- Historical January data showed this was achievable? (Could have been an outlier)
- ARŌ's gut feeling? (Should be documented)

**Risk:** If Cramer or ARŌ disputes these thresholds, the entire dashboard recommendation system breaks.

**Fix:**
```typescript
// Better: Document the math
export const CAC_DECISION_MATRIX: CACRange[] = [
  {
    min: 0,
    max: 55,
    status: 'EXCEPTIONAL',
    action: 'SCALE_AGGRESSIVE',
    reasoning: 'LTV:CAC = 6.2x (validated Jan 2026). Strong payback cycle.',
    ltv: 340,
    targetLtvCacRatio: 5.0,
    ...
  },
  ...
]
```

**Or:** Move to database/config so it's updateable without code changes.

---

### Issue 2: Hardcoded Constants Mixed with Real Data

**Location:** `src/components/growth/MomentumHero.tsx:9-48`

```typescript
// These are assumptions
const MONTHLY_ARPU = 100
const CUSTOMER_LTV = 340
const TAKE_RATE = 0.43
const MONTHLY_CHURN = 700
const CURRENT_ACTIVE_SUBS = 14000
const LAST_MONTH_TOTAL_REVENUE = 2_700_000

// These are fetched from API
const { metrics, loading, error } = useGrowthData()
```

**The Problem:**
- Constants are NEVER updated (they're hardcoded)
- Metrics are updated every 15s-12h
- If reality drifts from assumptions, nobody notices
- The compound growth model uses CONSTANTS + FETCHED DATA mixed together

**Example Inconsistency:**
```typescript
// Assumption
const CURRENT_ACTIVE_SUBS = 14000

// But real data might be different:
const metrics.today.subs.total = 14250  // Updated data

// Which one is used? It's unclear in the compound growth calculation.
```

**Risk:** Over time, the assumptions and reality diverge. The projections become increasingly inaccurate.

**Fix:**
```typescript
// Option 1: Fetch from API
interface ComprehensiveMetrics {
  assumptions: {
    monthlyArpu: number
    customerLtv: number
    takeRate: number
    monthlyChurn: number
    activeSubscribers: number
  }
}

// Option 2: If constants are intentional overrides, make it explicit
const OVERRIDE = {
  USE_CONSTANT_ASSUMPTIONS: true,
  ASSUMPTIONS: { ... }
}
```

---

### Issue 3: Recommendation Logic Doesn't Account for Constraints

**Location:** `src/lib/hooks/useMomentumData.ts:256-276`

```typescript
// THE RECOMMENDATION
const investAmount = overrides.weeklySpend ?? weeklySpendCeiling
const expectedCustomers = Math.round(investAmount / cac)
const expectedSubscribers = Math.round(expectedCustomers * subConversionRate)
```

**The Problem:**
- Assumes David can spend whatever the ceiling allows
- Doesn't check: "Do we have cash on hand to support this spend?"
- Doesn't check: "Can ops fulfill X more customers?"
- Doesn't check: "Is there production capacity?"
- Doesn't check: "Has our budget been cut this month?"

**Real Scenario:**
- Ceiling says "spend $55K/week"
- But ARŌ just told finance: "Max $200K/month due to cash constraints"
- David follows the recommendation, overruns budget
- Everyone's confused

**Fix:**
```typescript
const recommendation: Recommendation = {
  investAmount: overrides.weeklySpend ?? weeklySpendCeiling,
  constraints: {
    cashLimit: calculateCashConstraint(), // Do we have runway?
    productionLimit: getProductionCapacity(), // Can we fulfill?
    budgetRemaining: calculateBudgetRemaining(), // Monthly budget left?
    recommendedAmount: Math.min(investAmount, ...allConstraints),
    isConstrained: true | false
  }
}
```

---

### Issue 4: Data Staleness Not Visually Obvious During Off-Hours

**Location:** `src/lib/hooks/useGrowthData.ts:54-64`

```typescript
const STALE_THRESHOLD_MS = 5 * 60 * 1000  // 5 minutes

const isStale = Boolean(
  error &&
  metrics &&
  lastUpdated &&
  (Date.now() - lastUpdated.getTime() < STALE_THRESHOLD_MS)
)
```

**The Problem:**
- Staleness only shows if there's an ERROR
- If API is unreachable and backoff reaches 12h, you're seeing 12-hour-old data silently
- The stale warning only appears if you hit an error and recover

**Scenario:**
- 5pm: API breaks
- Dashboard retries with exponential backoff
- By 8pm: Backoff is at 1+ hour
- By 9am: Backoff is at 12 hours
- 10am: David opens dashboard, sees 9pm-yesterday's data as current
- No warning because the last fetch succeeded (just returned old data)

**Fix:**
```typescript
// ALWAYS check how old the data is, regardless of errors
const isStale = Boolean(
  lastUpdated &&
  Date.now() - lastUpdated.getTime() > STALE_THRESHOLD_MS
)

// During business hours (8am-6pm), NEVER backoff past 15 minutes
const shouldBackoff = () => {
  const hour = new Date().getHours()
  if (hour >= 8 && hour < 18) return false  // Business hours, no backoff
  return true
}
```

---

### Issue 5: No Validation of Input Data Quality

**Location:** `src/lib/hooks/useGrowthData.ts:99-103`

```typescript
const data = await response.json()
if (!data.success) {
  throw new Error(data.error || 'Failed to fetch metrics')
}
setMetrics(data.metrics)  // What if data.metrics has bad values?
```

**The Problem:**
- No validation that `data.metrics` has all required fields
- No checks for NaN, Infinity, negative values where they shouldn't be
- Silent failure if API returns partial data

**Example Bad Data:**
```typescript
// What if API returns:
{
  success: true,
  metrics: {
    today: {
      cac: null,           // Should be number
      spend: NaN,          // Should be number
      subs: { total: -100 } // Negative subs? Bad.
    }
  }
}
// Dashboard would still render, but with confusing values
```

**Fix:**
```typescript
// Add Zod or similar validation
import { z } from 'zod'

const MetricsSchema = z.object({
  today: z.object({
    cac: z.number().nonnegative(),
    spend: z.number().nonnegative(),
    subs: z.object({
      total: z.number().nonnegative()
    })
  })
})

const validated = MetricsSchema.parse(data.metrics)
setMetrics(validated)
```

---

### Issue 6: CAC Calculation Doesn't Account for Multi-Channel Attribution

**Location:** `src/components/growth/MomentumHero.tsx:262`

```typescript
const currentCAC = metrics.yesterday.cac > 0 ? metrics.yesterday.cac : 55
```

**The Problem:**
- Assumes `metrics.yesterday.cac` is accurate
- But CAC is calculated as: `spend / subs`
- What if subs came from multiple channels?
  - Paid ads (should be charged CAC)
  - Organic (shouldn't be charged CAC)
  - Retail/wholesale (different CAC model)

**Real Scenario:**
- Yesterday: $5K ad spend, 100 subs acquired
- CAC = $50
- But: 40 from ads, 60 from organic/retail

**Correct CAC should be: $5K / 40 = $125**, not $50.

**The dashboard's recommendation would be wrong.**

**Fix:**
```typescript
// Track source of each subscriber
interface DayMetrics {
  subs: {
    total: number
    paid: number        // Only from paid ads
    organic: number     // From organic
    retail: number      // From retail channel
  }
  spend: number
  // CORRECT calculation
  cac: number  // spend / paid, NOT spend / total
}
```

---

## MEDIUM-LEVEL ISSUES

### Issue 7: Hardcoded Team Message (Not Configurable)

```typescript
// src/app/momentum/page.tsx:97-103
<p className="text-[#e3f98a] font-bold text-lg">
  Hi Lucid team, you guys are doing so great. Way to be fucking rock stars. Hell yeah, Wieners!
</p>
```

**Problem:** Hardcoded message takes up 60px of above-fold space. Can't be changed without code deploy.

**Better:** Pull from database, allow admins to update it.

---

### Issue 8: No Rate Limit Headers Handling

```typescript
// useGrowthData.ts - Retries on 529, but doesn't check Rate-Limit headers
if (response.status === 529) { ... }
```

**Problem:** API might send `Retry-After` header, but code ignores it.

**Better:**
```typescript
const retryAfter = response.headers.get('Retry-After')
const delayMs = retryAfter ? parseInt(retryAfter) * 1000 : getRetryDelay(attempt)
```

---

### Issue 9: Momentum Status Logic is Simplistic

**Location:** `src/components/growth/MomentumHero.tsx:206-224`

```typescript
function getMomentumMessage(pacing: { percentComplete: number; daysElapsed: number }, status: string) {
  const dayOfMonth = new Date().getDate()
  const expectedProgress = (dayOfMonth / 28) * 100
  const ahead = pacing.percentComplete >= expectedProgress

  if (status === 'AHEAD') return { emoji: '🚀', message: "We're ahead of pace!" }
  if (status === 'ON_TRACK') return { emoji: '🔥', message: 'Strong momentum' }
  if (ahead) return { emoji: '💪', message: 'Building momentum' }
  if (pacing.daysElapsed <= 3) return { emoji: '🌱', message: 'Month just started' }
  return { emoji: '📈', message: 'Time to accelerate' }
}
```

**Problem:** Uses 28 days as month length (should be `new Date(year, month+1, 0).getDate()`)

**Better:**
```typescript
const daysInMonth = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate()
const expectedProgress = (dayOfMonth / daysInMonth) * 100
```

---

## MINOR ISSUES

### Issue 10: No Accessibility Improvements
- Color-coded status (green/red) not accessible to colorblind users
- Should add text labels or patterns in addition to colors

### Issue 11: Mobile Layout Not Tested
- 2-column layout might break on tablets
- Simulator section likely requires lots of scrolling on mobile

### Issue 12: No Loading Skeleton
- While fetching, shows a loading spinner
- Better UX: Show skeleton of the layout (keeps layout stable)

---

## SUMMARY SCORECARD

| Category | Score | Notes |
|----------|-------|-------|
| Type Safety | 9/10 | Excellent TypeScript usage |
| Error Handling | 7/10 | Good retry logic, but staleness detection incomplete |
| Data Validation | 4/10 | No input validation of API responses |
| Constraint Handling | 4/10 | Doesn't account for cash/production/budget limits |
| Assumptions Documentation | 3/10 | Hardcoded constants, no comments on WHY |
| Mobile UX | 5/10 | Untested, likely layout issues |
| Accessibility | 5/10 | Color-reliant, no ARIA labels |
| Performance | 8/10 | Smart backoff, good polling strategy |

---

## RECOMMENDATIONS (Priority Order)

### P0 (Do First)
1. Add input validation to API responses (Zod schema)
2. Document CAC threshold reasoning or make configurable
3. Add constraint checks to recommendation logic
4. Fix data staleness detection during off-hours

### P1 (Do Soon)
5. Move hardcoded constants to config/database
6. Account for multi-channel CAC attribution
7. Add `Retry-After` header support
8. Fix month length calculation

### P2 (Nice to Have)
9. Add loading skeleton
10. Improve mobile layout
11. Add accessibility improvements
12. Make team message configurable

---

## VERDICT

**Code Quality:** 7/10 (Solid fundamentals, good patterns, some gaps)

**Architecture:** 6/10 (Mixes concerns, hardcoded vs. dynamic data confused)

**Product Fit:** 5/10 (Feature-rich, but unclear who this serves and what they need)

**Recommendation:** Code is production-ready. But address P0 issues before critical use. The bigger issue is product strategy (see QUEST analysis) — this dashboard is trying to do too much.

---

*Code review completed by SØWL (Code Review phase). Technical quality is good. The bigger challenges are architectural and strategic, not code-level.*
