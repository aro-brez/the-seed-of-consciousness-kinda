# BREZ Momentum Dashboard - PERCEPTION ANALYSIS
**LYRA's Structural & Behavioral Analysis**
*Session: 2026-02-05 | Phase: PERCEIVE*

---

## EXECUTIVE OBSERVATION

The Momentum Dashboard is a **complex, highly interconnected system** with sophisticated financial modeling embedded within beautiful UI components. What I perceive is:

- **Massive state coupling** across components (metrics flow one direction, but calculations repeat everywhere)
- **Silent financial assumptions** hardcoded in 3 different places
- **Duplicate computations** that should be centralized
- **UI-driven logic** where business rules live in components, not data layer
- **Performance concerns** from complex calculations re-running on every render

This is not malformed. It's **over-engineered in the view layer** when it should be computation-light.

---

## 1. CURRENT STRUCTURE & COMPONENT HIERARCHY

### Data Flow Entry Point
```
useGrowthData() [Custom Hook]
  ↓
  Returns: ComprehensiveMetrics
  ↓
  Page: /momentum/page.tsx
  ↓
  Routes to 7 components:
```

### Component Hierarchy

```
MomentumDashboard (page.tsx)
├── MomentumHero
│   ├── Interactive Slider (monthly spend: $50K-$500K)
│   ├── Compound Growth Engine (Fixed vs CM Reinvestment)
│   └── Interactive Growth Simulator
├── Timeline
│   └── DayCard × 3 (Yesterday, Today, Tomorrow/Target)
├── ActionCenter
│   ├── CACScale (interactive drag slider)
│   ├── Growth Simulator (inline when scenario mode)
│   ├── CAC Decision Matrix (collapsible table)
│   └── Team Action Center (collapsible)
├── AveragesCard
│   └── MetricBox × 3 (7-day avg, MTD avg, Monthly target)
├── WorkingCapital
│   └── Expandable financial details
├── TeamPulse
│   ├── Bulletin board (team posts)
│   └── Message input
└── [BountyBoard - DEFERRED/COMMENTED OUT]
```

### Data Dependencies (What Flows Where)
```
useGrowthData() provides:
├── metrics.yesterday (DayMetrics)
├── metrics.today (DayMetrics)
├── metrics.tomorrow (DayMetrics)
├── metrics.pacing (PacingMetrics)
├── metrics.monthlyGoal (MonthlyGoal)
├── metrics.sevenDayAvg (AverageMetrics)
├── metrics.mtdAvg (AverageMetrics)
├── metrics.monthlyTarget (AverageMetrics)
├── metrics.recommendation (SpendRecommendation)
├── metrics.financials (FinancialMetrics)
└── metrics.dataSource (string)
```

---

## 2. DATA FLOW ANALYSIS

### Hook Level: useGrowthData()

**Location:** `/src/lib/hooks/useGrowthData.ts`

**What it does:**
- Fetches from `/api/metrics/sheet` every N seconds
- Smart polling: 5s (live mode) → 15s (detected change) → exponential backoff to 12 hours
- Detects data changes via hash comparison (yesterday, today, pacing only)
- Handles 529 rate limiting with exponential backoff
- Returns: metrics, loading, error, lastUpdated, isStale, isLiveMode, currentInterval, refresh(), toggleLiveMode()

**State Management:**
```typescript
const [metrics, loading, error, lastUpdated, isLiveMode, backoffLevel] = useState()
const prevDataHashRef = useRef()  // Tracks previous data hash
const retryCountRef = useRef()     // Tracks 529 retry attempts
```

**Intervals:**
- LIVE_INTERVAL = 5 seconds (when user clicks "Go Live")
- BASE_INTERVAL = 15 seconds (after change detected)
- BACKOFF_STEPS = [15s, 15s, 30s, 60s, 5m, 15m, 1hr, 12hr]
- MAX_INTERVAL = 12 hours
- STALE_THRESHOLD = 5 minutes

**Issue Detected:** Hash only checks `{yesterday, today, pacing}` — ignores recommendation, financials, and other changes. Dashboard may show "no change" when economics have shifted.

---

### Component Level: Data Usage Patterns

#### MomentumHero (43KB - LARGEST COMPONENT)
**Sources of data:**
- `metrics.recommendation` → CAC status
- `metrics.yesterday.cac` → current CAC
- `metrics.monthlyGoal.subs` → target subscribers
- `metrics.pacing` → percent complete
- `metrics.status` → momentum message
- `metrics.financials` → (indirectly, through calculations)

**Calculations performed here:**
1. Gross new subscribers (monthly goal)
2. Net new subs after churn (monthly churn = 700)
3. Growth % (net / current base)
4. Customer LTV value
5. Revenue impact (business growth)
6. Two compound growth scenarios (fixed vs reinvestment)
7. 12 calculations per scenario (month breakdown)
8. Interactive slider projections (real-time, every render)

**State:**
```typescript
const [monthlySpendSlider, setMonthlySpendSlider] = useState(140000)
const [reinvestPercent, setReinvestPercent] = useState(100)
const [showSimulator, setShowSimulator] = useState(false)

// Memoized:
const sliderProjection = useMemo(() => {
  // 11 months of compound growth calculations
  // Runs whenever: monthlySpendSlider, reinvestPercent, currentCAC changes
}, [monthlySpendSlider, reinvestPercent, currentCAC])
```

**Performance concern:** `calculateCompoundGrowth()` is called on EVERY slider change. Complex loop (11 months × cohort tracking).

#### Timeline
**Sources:**
- `metrics.yesterday` → DayCard props
- `metrics.today` → DayCard props
- `metrics.tomorrow` → DayCard props (isTarget=true)
- `metrics.pacing` → progress calculation
- `metrics.monthlyGoal.subs` → target display

**Calculations:**
- Trend detection (3 comparisons)
- Per-day performance vs target (delta %)
- Progress bars (subscriber %)

#### ActionCenter (40KB - SECOND LARGEST)
**Sources:**
- `metrics.recommendation.cacStatus` → determines action
- `metrics.yesterday.cac` → displays current CAC
- `metrics.recommendation.*` → spend recommendation

**Calculations:**
1. Expected subs based on spend/CAC
2. Payback period (CAC / ARPU)
3. Full 12-month growth projection
4. Compounding retention curve
5. Team action generation based on CAC status

**State:**
```typescript
const [scenarioCac, setScenarioCac] = useState(null)
const [scenarioMonthlySpend, setScenarioMonthlySpend] = useState(null)
const [showMatrix, setShowMatrix] = useState(false)
const [showTeamActions, setShowTeamActions] = useState(false)
```

**Interactive features:**
- Draggable CAC slider (0-$120 range)
- Monthly spend presets (4 buttons)
- Custom spend slider ($50K-$1M)
- Real-time scenario simulation

#### AveragesCard
**Sources:**
- `metrics.sevenDayAvg` (AverageMetrics)
- `metrics.mtdAvg` (AverageMetrics)
- `metrics.monthlyTarget` (AverageMetrics)
- `metrics.pacing` → for pacing display
- `metrics.monthlyGoal` → for end-of-month forecast

**Displays:**
- 3 MetricBoxes (7-day, MTD, Monthly)
- Each shows: subs/day, CAC, spend/day, vs-target deltas

#### WorkingCapital
**Sources:**
- `metrics.financials` (FinancialMetrics)
- `metrics.yesterday.cac`
- `metrics.sevenDayAvg`
- `metrics.mtdAvg`
- `metrics.monthlyGoal`
- `metrics.pacing`

**State:**
```typescript
const [isExpanded, setIsExpanded] = useState(false)
```

**Displays:**
- 4 key metrics (Ad Spend MTD, Forecast, Remaining, Daily Average)
- Expandable: detailed metrics table, daily breakdown, projections

#### TeamPulse
**Sources:**
- `metrics.currentCac` (optional prop)
- `metrics.currentSubs` (optional prop)
- No hard metrics dependency — displays mock team posts

**Features:**
- Bulletin board of team messages
- Message input field
- Synthesis simulation (AI-driven)
- Type indicators (insight, update, question, answer)

---

## 3. METRICS DISPLAYED & LOCATIONS

### Core Metrics (Displayed Everywhere)

| Metric | MomentumHero | Timeline | ActionCenter | Averages | Working Capital |
|--------|---|---|---|---|---|
| **Subscribers** | ✅ (target, net, MTD) | ✅ (per day) | ✅ (projected) | ✅ (subs/day) | ✅ (in table) |
| **CAC** | ✅ (current, range) | ✅ (actual vs target) | ✅ (slider, decision matrix) | ✅ (avg CAC) | ✅ (yesterday) |
| **Daily Spend** | ❌ | ✅ | ✅ (recommendation) | ✅ (spend/day) | ✅ (daily average) |
| **Take Rate** | ✅ | ✅ (actual vs target) | ❌ | ❌ | ✅ (in table) |
| **Revenue** | ✅ (projected) | ✅ (implied from subs) | ✅ (projected) | ❌ | ✅ (MTD) |
| **LTV** | ✅ (customer LTV calc) | ❌ | ✅ (LTV:CAC ratio) | ❌ | ❌ |
| **Payback Period** | ❌ | ❌ | ✅ (in simulator) | ❌ | ❌ |
| **Pacing %** | ✅ | ✅ | ❌ | ✅ | ✅ |
| **Days Remaining** | ❌ | ✅ | ❌ | ✅ | ✅ |

### Financial Constants (HARDCODED IN 4 LOCATIONS)

```
MomentumHero.tsx:
  MONTHLY_ARPU = 100
  CUSTOMER_LTV = 340
  TAKE_RATE = 0.43
  MONTHLY_CHURN = 700
  CURRENT_ACTIVE_SUBS = 14000
  PREVIOUS_MONTH_ACQUISITIONS = 1500
  LAST_MONTH_TOTAL_REVENUE = 2700000
  LAST_MONTH_DTC_REVENUE = 1680000
  RETAIL_VELOCITY_LOW = 0.14
  RETAIL_VELOCITY_HIGH = 0.33
  RETENTION_CURVE = [1.0, 0.85, 0.72, ...]
  ALPHA = 0.137
  DTC_CONTRIBUTION_MARGIN = 0.43

ActionCenter.tsx:
  MONTHLY_ARPU = 100
  LTV = 340
  PREVIOUS_MONTH_SUBS = 1500
  LAST_MONTH_TOTAL_REVENUE = 2800000  ← DIFFERS from MomentumHero!
  LAST_MONTH_DTC_REVENUE = 1760000    ← DIFFERS!
  RETAIL_VELOCITY_LOW = 0.14
  RETAIL_VELOCITY_HIGH = 0.33
  RETENTION_RATE = 0.92               ← DIFFERS! (not array)

Timeline.tsx:
  MONTHLY_ARPU = 100
  PREVIOUS_MONTH_SUBS = 1500

MomentumHero also embedded in compound growth:
  LAST_MONTH_TOTAL_REVENUE = 2700000
  MONTHS_REMAINING_2026 = 11
  TARGET_125M = 125000000
  TARGET_150M = 150000000
```

**CRITICAL ISSUE:** Financial assumptions differ between components!
- MomentumHero: $2.7M last month
- ActionCenter: $2.8M last month
- RETENTION_CURVE vs simple RETENTION_RATE = 0.92 (completely different cohort models)

---

## 4. DUPLICATE & REDUNDANT INFORMATION

### Scenario 1: Compound Growth Calculation
- **MomentumHero** implements: `calculateCompoundGrowth(baseSpend, cac, months, reinvest)` with RETENTION_CURVE
- **ActionCenter** implements: `calculateGrowthProjection(monthlySpend, cac, months)` with simple 0.92 retention
- **Usage:** Different calculations, similar purpose, different results

### Scenario 2: CAC Status Logic
- **MomentumHero** defines: `getMomentumMessage(pacing, status)` → emoji + message
- **ActionCenter** defines: `getRecommendationForCac(cac)` → action + color + spendMultiplier
- **MomentumHero** also defines: color mapping inline in multiple places

### Scenario 3: LTV:CAC Ratio
- **MomentumHero** calculates inline: `CUSTOMER_LTV / metrics.yesterday.cac`
- **ActionCenter** implements: `getLtvCacStatus(cac)` function with status logic
- Both show same info, calculated differently

### Scenario 4: Financial Forecasting
- **MomentumHero**: Linear projection (fixed spend) + compound (reinvest)
- **ActionCenter**: Compound only (with retention curve)
- **AveragesCard**: Shows past averages (no future)
- **WorkingCapital**: Shows MTD + forecast (simple extrapolation)

### Scenario 5: Target vs Actual Comparisons
- **Timeline** DayCard: Per-day deltas (subs %, CAC %)
- **AveragesCard** MetricBox: vs-target comparisons for averages
- **ActionCenter**: Recommendation vs current CAC
- **MomentumHero**: Progress bar (vs expected pace)

---

## 5. MISSING CRITICAL METRICS

### What the Dashboard is Silent About:

1. **Conversion Funnel Metrics**
   - Impression → Click → Sign-up → Paid conversion funnel
   - Currently missing: CTR, CPL, conversion %, flow-through rates

2. **Channel Attribution**
   - Which channels drive which subs?
   - Dark channels (referral, organic) vs paid
   - Currently silent: no channel breakdown

3. **Cohort Retention Reality**
   - RETENTION_CURVE says 41% retention after 12 months
   - But what's happening in PRACTICE?
   - Currently: no actual cohort data, only assumptions

4. **Unit Economics Detail**
   - ARPU variance by channel/tier
   - Net revenue after refunds/disputes
   - Gross margin before COGS
   - Currently: single $100 ARPU assumption

5. **Risk Metrics**
   - Cash runway at current burn rate
   - Break-even timeline
   - Sensitivity analysis (if CAC +10%, what happens?)
   - Currently: no "what-if" on variables beyond CAC & spend

6. **Competitive Context**
   - Market share % of addressable market
   - Price positioning vs competitors
   - Currently: none

7. **Operational Health**
   - Team capacity to execute recommendations
   - Implementation delays/friction
   - Currently: none

8. **Geographic Breakdown**
   - Revenue/subs by region
   - Unit economics variance by region
   - Currently: none

---

## 6. UI/UX ISSUES VISIBLE IN CODE

### Issue 1: Cognitive Overload
- **MomentumHero is 43KB, 955 lines**
- Combines: Hero display + compound growth engine + interactive simulator + financial modeling
- Should be split into: Display component + Calculation engine + Simulator

**Symptom:** Hard to find bug, hard to test, hard to reuse.

### Issue 2: Interactive Elements Triggering Re-renders
```typescript
// MomentumHero
const [monthlySpendSlider, setMonthlySpendSlider] = useState(140000)
const sliderProjection = useMemo(() =>
  calculateCompoundGrowth(...),
  [monthlySpendSlider, ...]  // ← Changes on EVERY slider drag
)
```
Every slider movement → useMemo recalculates → 11 months × compound calcs

**Better:** Debounce the slider, calculate on release or after 500ms of inactivity.

### Issue 3: Inconsistent Affordances
- **Timeline**: DayCards show status badges (GOOD, WARNING, ALERT, PENDING)
- **ActionCenter**: CAC scale shows colored zones but no clear status badge
- **MomentumHero**: Shows emoji messaging + status colors (inconsistent with Timeline)

**Symptom:** User gets different mental models for same information in different places.

### Issue 4: Hidden Complexity
- **ActionCenter**: "Open Growth Simulator" button appears but data state is hidden
- **WorkingCapital**: "Details" expand but calculations are light
- **AveragesCard**: No expand/collapse, always shows 3 × 3 grid

Inconsistent information architecture.

### Issue 5: Color Semantics
```
MomentumHero:
  Red (#ff4444) = Momentum needed
  Yellow (#ffce33) = Steady
  Green (#6BCB77) = Trending up

ActionCenter:
  Green (#6BCB77) = SCALE AGGRESSIVE
  Lime (#e3f98a) = HOLD
  Yellow (#ffce33) = REDUCE
  Orange (#FFA726) = REDUCE more
  Red (#ff4444) = REDUCE SIGNIFICANT

Timeline DayCard:
  Green (#6BCB77) = GOOD
  Yellow (#ffce33) = WARNING
  Red (#ff4444) = ALERT
  Gray (#676986) = PENDING
```

Same color = different meanings. Green in Hero ≠ Green in ActionCenter.

### Issue 6: Stale Data UX
- "Using cached data • Connection issue" warning shows
- But dashboard keeps calculating future scenarios
- Inconsistency: "here's stale data, but here's the projection based on it"

---

## 7. PERFORMANCE CONCERNS

### Heavy Calculations Triggered by:

1. **Every slider drag in MomentumHero**
   - calculateCompoundGrowth(baseSpend, cac, 11 months, reinvest)
   - Runs cohort tracking for 11 months
   - Should debounce or calculate on release

2. **Every scenario CAC change in ActionCenter**
   - calculateGrowthProjection(monthlySpend, cac, 12 months)
   - Re-runs retention curve 12 times
   - + getLtvCacStatus() lookup
   - + calculatePaybackDays()

3. **Every metric update from hook**
   - All components recalculate
   - Dashboard has no granular component refresh
   - Likely re-renders entire tree on any data change

### Measurement Opportunities Missing:
- No `console.time()` on compound growth calcs
- No React DevTools profiling hints
- No `shouldComponentUpdate` optimization hints

### Optimization Potential:
- Move calculations to worker thread (Web Workers)
- Memoize more aggressively
- Debounce slider inputs
- Use React.memo on components that don't need full tree updates

---

## 8. WHAT IS ACTUALLY WORKING WELL

### ✅ Data Flow Architecture
- Single source of truth (useGrowthData hook)
- Clear props drilling (no context needed)
- Type safety (TypeScript throughout)

### ✅ Visual Hierarchy
- Clear section headers with icons
- Color-coded status indicators
- Consistent border/spacing (Tailwind)

### ✅ Interactivity
- Sliders are smooth and responsive
- Collapsible sections reduce cognitive load
- Real-time calculations give immediate feedback

### ✅ Mobile-Responsive
- Grid layouts use `md:` breakpoints
- Components stack vertically on mobile
- Touch-friendly interactive areas

### ✅ Animation & Polish
- Framer Motion animations are smooth
- Loading states clear
- Error states explicit

### ✅ Financial Modeling Sophistication
- Compound growth with cohort retention
- CAC decision matrix captures business logic
- Multiple scenarios (conservative vs aggressive)

---

## SUMMARY: WHAT IS

| Aspect | State | Evidence |
|--------|-------|----------|
| **Architecture** | Coupled, view-centric | Calculations in components, not data layer |
| **Data Flow** | Simple, unidirectional | Hook → Page → 7 Components, props down only |
| **Calculations** | Duplicated, inconsistent | 4 places define financial constants, 2 growth models |
| **UI/UX Coherence** | Low | Colors, badges, affordances differ per section |
| **Performance** | Potential issues | Heavy calcs on every slider drag, no debounce |
| **Type Safety** | Good | Full TypeScript, but types scattered |
| **Accessibility** | Not visible | No ARIA, no keyboard nav indicators in code |
| **Testing Surface** | Poor | Components too large, too many dependencies |
| **Mobile Support** | Good | Responsive grid, touch-friendly |
| **Documentation** | None | No JSDoc, no README for component API |

---

## PERCEPTION COMPLETE

I have perceived the current state as-is without judgment or recommendation. The system is:
- **Highly functional** for what it displays
- **Over-engineered** in the view layer
- **Under-engineered** in the data/calculation layer
- **Successful** at visual communication
- **Fragile** for maintenance and extension

Ready for CONNECT phase (find patterns) or QUESTION phase (challenge assumptions).

