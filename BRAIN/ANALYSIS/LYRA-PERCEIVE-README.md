# LYRA PERCEIVE Phase - Complete Analysis
**BREZ Momentum Dashboard Code Review**

Start here to understand what LYRA observed.

---

## What Happened

LYRA (the PERCEIVE phase of the SEED protocol) analyzed the BREZ Momentum Dashboard codebase to document its current state accurately - not what should be, but what IS.

**Files generated:**
1. `LYRA-PERCEIVE-FINDINGS.md` ← **START HERE** (9.1KB, executive summary)
2. `MOMENTUM-DASHBOARD-PERCEPTION.md` (17KB, deep technical analysis)
3. `MOMENTUM-DASHBOARD-STRUCTURE-VISUAL.txt` (17KB, ASCII diagrams)

---

## Three-Minute Summary

### What Is The Momentum Dashboard?

A Next.js dashboard displaying real-time business metrics (CAC, subscribers, revenue, pacing) with interactive scenario modeling.

**Components:**
1. MomentumHero - Main hero with target + progress + simulator (43KB)
2. Timeline - Yesterday/Today/Tomorrow comparison with celebration indicators
3. ActionCenter - CAC decision matrix with spend recommendations (40KB)
4. AveragesCard - 7-day, MTD, and monthly average metrics
5. WorkingCapital - Financial details and forecasts (expandable)
6. TeamPulse - Bulletin board for team posts (future feature)
7. (BountyBoard - Deferred, not ready yet)

**Data Flow:**
```
useGrowthData() hook
  ↓ (fetches /api/metrics/sheet every 5s-12hr)
  ↓
MomentumDashboard (page.tsx)
  ↓ (passes ComprehensiveMetrics)
  ↓
7 components (display data + calculations)
```

### What Works Well ✅

- **Visually polished** - Beautiful aurora-themed UI, smooth animations
- **Technically sound** - Full TypeScript, proper React patterns
- **Interactive exploration** - Users can drag sliders to see scenarios
- **Smart polling** - Backs off from 5s to 12hr based on data changes
- **Responsive design** - Works on mobile and desktop
- **Real-time updates** - Shows latest data with stale-data warnings

### What's Fragile ⚠️

1. **Monolithic components**
   - MomentumHero: 955 lines, 43KB
   - ActionCenter: 985 lines, 40KB
   - Should be split into 5-10 smaller components

2. **Calculation duplication**
   - Two different compound growth algorithms
   - Two different retention models (curve vs 0.92)
   - Same formulas calculated in multiple places
   - Should centralize to single engine

3. **Constants scattered**
   - MONTHLY_ARPU defined in 3 places
   - LAST_MONTH_REVENUE differs (2.7M vs 2.8M)
   - RETENTION models are inconsistent
   - Should centralize to config file

4. **Performance hotspots**
   - Compound growth calculation runs on every slider drag (no debounce)
   - No React.memo on components
   - Could lag on slower devices

5. **Design inconsistencies**
   - Same color means different things in different sections
   - Status indicators (badges vs zones vs emojis)
   - Expand/collapse behavior inconsistent

### What's Missing 🚨

**Business metrics not displayed:**
- Conversion funnel (impressions → clicks → signups → paid)
- Channel attribution (which channels drive subs?)
- Actual cohort retention (vs hardcoded assumptions)
- Unit economics by tier/region
- Risk metrics (cash runway, break-even)
- Sensitivity analysis (what if CAC +10%?)

---

## Key Numbers

| Metric | Value | Status |
|--------|-------|--------|
| **MomentumHero size** | 43KB, 955 lines | Too large |
| **ActionCenter size** | 40KB, 985 lines | Too large |
| **Polling intervals** | 5s-12hr | Good |
| **Calculation engines** | 2 implementations | Should be 1 |
| **Constants locations** | 4 files | Should be 1 |
| **UI sections** | 7 components | Good count |
| **Type coverage** | Full TypeScript | Good |

---

## The Three Weaknesses LYRA Identified

### 1. Over-Engineering in View, Under-Engineering in Logic

**The problem:**
- Components do 5 jobs each (display + calculate + simulate + animate)
- Calculations are embedded in JSX, not extracted
- Business logic lives in components, not domain layer

**Why it matters:**
- Hard to test calculations in isolation
- Hard to reuse calculations in different contexts
- Hard to change calculations without touching UI

**What it should be:**
- Components: Display only
- Custom hooks: Data fetching + calculations
- Config files: Business constants

### 2. Duplicate Work Without Single Source Of Truth

**The problem:**
```
MomentumHero.tsx          ActionCenter.tsx
MONTHLY_ARPU = 100        MONTHLY_ARPU = 100    ← Same
LAST_MONTH_REVENUE=2.7M   LAST_MONTH_REVENUE=2.8M  ← DIFFERS!
RETENTION=[...]           RETENTION=0.92        ← COMPLETELY DIFFERENT!
```

**Why it matters:**
- When ARŌ changes an assumption, must update 4 files
- Easy to miss a file and have inconsistent calculations
- Dashboard shows different projections for same scenario

**What it should be:**
```
/config/business-constants.ts
├── MONTHLY_ARPU = 100
├── LAST_MONTH_REVENUE = 2_700_000
├── RETENTION_CURVE = [1.0, 0.85, ...]
└── Other constants...
```

### 3. Performance Not Optimized For Interaction

**The problem:**
```typescript
// MomentumHero
const [monthlySpendSlider, setMonthlySpendSlider] = useState(140000)
const sliderProjection = useMemo(() => {
  calculateCompoundGrowth(spend, cac, 11) // 11-month loop
}, [monthlySpendSlider])  // Runs on EVERY drag!
```

**Why it matters:**
- Every slider drag triggers full 11-month compound growth calc
- No debounce, so rapid drags create lag
- Multiplies when scenario CAC slider also used

**What it should be:**
```typescript
// Debounce calculations
const debouncedSpend = useDebounce(monthlySpendSlider, 500)
const sliderProjection = useMemo(() => {
  calculateCompoundGrowth(debouncedSpend, cac, 11)
}, [debouncedSpend])  // Only recalc after 500ms pause
```

---

## What This Means

**The dashboard works TODAY because:**
- Interactions are fast (users drag, React updates state)
- Calculations complete before next interaction
- Metrics update in real-time via polling

**The dashboard will struggle IF:**
- Calculations become more complex
- More users use scenario modeling (browser load)
- Data scales (slower API responses)
- Mobile devices with slower CPUs

---

## For Each Role

### For Product (ARŌ)
- Dashboard displays what you need to see
- It's beautiful and real-time
- But it's not extensible without refactoring
- Plan for refactoring if you want more metrics

### For Developers
- Code is well-written but monolithic
- You'll want to break apart the 40KB components
- Calculations should be extracted to custom hooks
- Add debouncing to interactive sliders
- Centralize financial constants

### For Designers
- Visual hierarchy is clear
- Color semantics are inconsistent (fix the system)
- Affordances differ per section (standardize)
- Consider design system tokens

---

## Next Steps (For Other Phases)

**CONNECT Phase** will identify patterns:
- Pattern: Large monolithic components
- Pattern: Duplicate calculation logic
- Pattern: Scattered constants

**LEARN Phase** will extract meaning:
- "What is the ideal component size?"
- "Should calculations be in custom hooks?"
- "Should we create a business logic layer?"

**QUESTION Phase** will challenge:
- "Why are we duplicating calculations?"
- "Is the current polling strategy optimal?"
- "Could we improve performance 10x?"

**EXPAND Phase** will grow:
- "What if we add channel attribution?"
- "What if we add sensitivity analysis?"
- "What if we add risk metrics?"

---

## Files In This Analysis

1. **LYRA-PERCEIVE-FINDINGS.md** (this summary)
   - Executive overview
   - Key observations
   - Three facts LYRA perceives as true

2. **MOMENTUM-DASHBOARD-PERCEPTION.md** (detailed)
   - Complete structural analysis
   - Data flow diagrams
   - Metrics mapping (what's displayed where)
   - Duplicate information catalog
   - Missing metrics list
   - UI/UX issues
   - Performance concerns
   - What works well

3. **MOMENTUM-DASHBOARD-STRUCTURE-VISUAL.txt** (visual)
   - ASCII art component hierarchy
   - Data flow visualization
   - Calculation dependency trees
   - State management per component
   - Financial constants comparison table
   - Performance hotspots marked
   - Test coverage assessment

---

## How To Use This Analysis

### If you're refactoring:
1. Start with `MOMENTUM-DASHBOARD-STRUCTURE-VISUAL.txt` for the big picture
2. Read `MOMENTUM-DASHBOARD-PERCEPTION.md` for details
3. Focus on:
   - Extract calculations to `/lib/calculations/`
   - Centralize constants to `/lib/config/`
   - Split components by responsibility

### If you're extending:
1. Read `LYRA-PERCEIVE-FINDINGS.md` for what's missing
2. Check "Missing critical metrics" section
3. Plan architecture changes before adding features

### If you're debugging:
1. Use `MOMENTUM-DASHBOARD-STRUCTURE-VISUAL.txt` to trace data flow
2. Check "Performance hotspots" section
3. Look for calculation inconsistencies in constants comparison table

### If you're onboarding:
1. Start with "Three-Minute Summary" above
2. Read `LYRA-PERCEIVE-FINDINGS.md`
3. Reference `MOMENTUM-DASHBOARD-STRUCTURE-VISUAL.txt` for architecture

---

## LYRA's Core Observation

*The Momentum Dashboard is a well-designed product built on shakily-organized code. It works beautifully TODAY, but it's not built for scale or change.*

**Fix:**
- Extract business logic to `lib/`
- Centralize constants to config files
- Break monolithic components into modular pieces
- Add debouncing to performance-sensitive interactions

**Estimated effort:** 2-3 days of refactoring
**Benefit:** 10x easier to test, maintain, and extend

---

## Questions For ARŌ

After reading this analysis:

1. **Do you want to refactor?** (Recommended if planning extensions)
2. **What metrics matter most?** (Prioritize missing metrics)
3. **What's the CAC sensitivity?** (If CAC +10%, what happens?)
4. **Who else touches this code?** (Coordinate refactoring)

---

*LYRA's analysis complete. Ready for next phase.*
*Generated: 2026-02-05*

