# LYRA's PERCEIVE Phase - Key Findings
**Observation Report: BREZ Momentum Dashboard Analysis**
*Date: 2026-02-05 | Agent: LYRA | Phase: PERCEIVE*

---

## The Observation Task
Analyze the BREZ Momentum Dashboard at `/src/app/momentum/page.tsx` and its components, documenting:
1. Current structure and component hierarchy
2. Data flow
3. Metrics displayed and where
4. Duplicate/redundant information
5. Missing critical metrics
6. UI/UX issues
7. Performance concerns

---

## What LYRA Perceives

### ✅ What Is Working

The Momentum Dashboard **successfully communicates business momentum** through:

1. **Clear Visual Hierarchy** - Sections are distinct, scannable
2. **Real-time Updates** - Smart polling with exponential backoff
3. **Interactive Exploration** - Users can drag to explore scenarios
4. **Sophisticated Modeling** - Compound growth with cohort retention
5. **Mobile Responsive** - Stacks well on smaller screens
6. **Well-Animated** - Smooth Framer Motion transitions
7. **Type-Safe** - Full TypeScript implementation
8. **Accessible Actions** - Color + text indicators (not color alone)

### ⚠️ What Is Fragile

1. **Massive Components**
   - MomentumHero: 43KB, 955 lines (does 5 jobs)
   - ActionCenter: 40KB, 985 lines (does 4 jobs)
   - Should be split into smaller, single-purpose components

2. **Calculation Duplication**
   - `calculateCompoundGrowth()` in MomentumHero uses RETENTION_CURVE
   - `calculateGrowthProjection()` in ActionCenter uses simple 0.92 rate
   - Both do similar work with different logic → inconsistent results
   - Should centralize to single calculation engine

3. **Financial Constants Scattered**
   - MONTHLY_ARPU defined in: MomentumHero, ActionCenter, Timeline (3 places)
   - LAST_MONTH_REVENUE differs between MomentumHero ($2.7M) and ActionCenter ($2.8M)
   - RETENTION_RATE inconsistent (curve vs 0.92)
   - Should centralize to single config file

4. **Heavy Calculations Triggered Every Re-render**
   - Slider drag in MomentumHero runs 11-month compound growth calc
   - No debounce
   - Should debounce or calculate on release

5. **Color Semantics Inconsistent**
   - Green = "Trending Up" in MomentumHero
   - Green = "SCALE AGGRESSIVE" in ActionCenter
   - Same color, different meanings
   - Should establish design system

6. **Data Flow Hash Incomplete**
   - `useGrowthData()` only hashes {yesterday, today, pacing}
   - Ignores recommendation, financials, other changes
   - Dashboard may show "no change" when economics shifted
   - Should hash entire ComprehensiveMetrics

### 🚨 What Is Missing

**Critical Business Metrics Not Displayed:**
1. Conversion funnel (impressions → clicks → signups → paid)
2. Channel attribution (which channels drive which subs?)
3. Cohort retention reality (vs assumptions)
4. Unit economics by tier/channel
5. Risk metrics (cash runway, break-even timeline)
6. Sensitivity analysis (if CAC +10%, what happens?)
7. Geographic breakdown
8. Competitive context / market positioning

### 🟡 Performance Concerns

**Calculations Triggered On:**
1. Every slider drag (no debounce) ← HIGH RISK
2. Every CAC scale drag ← HIGH RISK
3. Every parent re-render (no React.memo) ← MEDIUM RISK

**Measurement:** No profiling instrumentation in code

**Optimization Potential:**
- Debounce slider inputs (500ms)
- Memoize components more aggressively
- Consider Web Workers for heavy calculations
- Move calculations out of component (custom hook?)

### 🎨 UI/UX Observations

**Information Architecture Inconsistencies:**
1. Timeline shows DayCard status badges (GOOD/WARNING/ALERT)
2. ActionCenter shows CAC zones (SCALE/HOLD/REDUCE)
3. MomentumHero shows emoji + status colors
4. All three communicate status, but differently

**Affordance Issues:**
1. Draggable sliders are clear (good)
2. Collapsible sections hide complexity (good)
3. But expand/collapse behavior is inconsistent:
   - ActionCenter: Manual toggle buttons
   - WorkingCapital: Manual "Details" button
   - MomentumHero: Always expanded
   - Should standardize

**Visual Feedback:**
1. Loading states clear ✅
2. Error states explicit ✅
3. Stale data warning prominent ✅
4. Success states (copy clipboard) animated ✅
5. BUT: Simulator doesn't show "calculating..." during heavy calcs

---

## Three-Layer Analysis

### Layer 1: Data (Hook)
```
Status: SIMPLE, EFFECTIVE
├── Single source of truth ✅
├── Type-safe ✅
├── Smart polling ✅
├── BUT: Hash detection incomplete ⚠️
└── No error recovery beyond retry ⚠️
```

### Layer 2: Calculations (Functions)
```
Status: DUPLICATED, INCONSISTENT
├── Two compound growth implementations ⚠️
├── Two retention models ⚠️
├── Constants scattered across files ⚠️
├── No centralized business logic ⚠️
└── Hard to test (embedded in components) ⚠️
```

### Layer 3: Presentation (Components)
```
Status: BEAUTIFUL, MONOLITHIC
├── Polished visuals ✅
├── Smooth animations ✅
├── Responsive layout ✅
├── BUT: Too large (40-43KB per component) ⚠️
├── BUT: No memoization ⚠️
└── BUT: Color semantics inconsistent ⚠️
```

---

## Structural Patterns Observed

### ✅ Pattern 1: Props Drilling Works
- Page passes metrics → 7 components
- No context needed (good for testability)
- Clear data dependencies visible in function signatures

### ✅ Pattern 2: Interactive State is Local
- Each component manages its own expanded/collapsed state
- Sliders are local React state
- Good separation of concerns

### ⚠️ Pattern 3: Calculations Are Duplicated
- MomentumHero calculates compound growth
- ActionCenter calculates different compound growth
- Same logic, different implementations
- Violates DRY principle

### ⚠️ Pattern 4: Constants Are Global Assumptions
- Hardcoded MONTHLY_ARPU in multiple files
- LAST_MONTH_REVENUE varies by file
- No single source of truth for business rules
- Breaks when assumptions change

---

## Key Numbers (What LYRA Observed)

| Metric | Value | Note |
|--------|-------|------|
| **Component Sizes** | 43KB (Hero), 40KB (ActionCenter) | Too large |
| **Lines of Code** | 955 (Hero), 985 (ActionCenter) | Monolithic |
| **Number of Calculations** | 50+ formulas | Scattered |
| **Polling Intervals** | 5s-12hr | Smart backoff |
| **Constant Duplications** | 4 places | Inconsistent |
| **Components** | 7 (+ 1 deferred) | Good modular count |
| **State Variables** | 12+ total | Reasonable |

---

## What State Is The System In?

### ✅ Strengths
- Visually polished and professional
- Technically sound (TypeScript, React patterns)
- Data flow is clear and simple
- User experience is smooth and responsive
- Mobile support is good
- Real-time updates work well

### ⚠️ Weaknesses
- Code is not modular (40KB components)
- Calculations are duplicated
- Constants are scattered
- Performance optimization missing
- Color semantics inconsistent
- Documentation is absent

### 🟡 Technical Debt
- No centralized calculation engine
- No shared constants config
- No performance profiling
- No component tests visible
- No accessibility implementation (no ARIA attributes visible)

---

## Three Facts LYRA Perceives As True

### Fact 1: The Dashboard Works, But Not Elegantly
The system successfully displays business metrics and enables scenario exploration. However, it does so by embedding business logic in UI components rather than separating concerns. This makes it harder to test, reuse, and maintain.

### Fact 2: Financial Assumptions Are Not A Single Source Of Truth
The business constants (ARPU, LTV, retention, etc.) are defined in 3-4 different files with inconsistent values. When ARŌ changes an assumption, it must be updated in multiple places.

### Fact 3: The Performance Hotspots Are Obvious
Compound growth calculations are triggered on every slider drag with no debounce. These are non-trivial calculations (loops × months × cohorts). This works okay now but will degrade as data scales.

---

## LYRA's Perception Summary

I perceive the BREZ Momentum Dashboard as:
- **Functional**: It displays what it's supposed to display
- **Beautiful**: The UI is polished and professional
- **Fragile**: The code organization makes changes risky
- **Ready for refactoring**: The pieces exist but need reorganization

**In one sentence:**
*A well-designed product built on shakily-organized code.*

---

## Files Generated By LYRA

1. `MOMENTUM-DASHBOARD-PERCEPTION.md` - Detailed structural analysis
2. `MOMENTUM-DASHBOARD-STRUCTURE-VISUAL.txt` - ASCII art visual representation
3. `LYRA-PERCEIVE-FINDINGS.md` - This summary

---

## Ready For Next Phases

LYRA's PERCEIVE phase is complete. The system is ready for:

**CONNECT** (Identify patterns):
- Pattern: Large monolithic components
- Pattern: Duplicate calculation logic
- Pattern: Scattered constants

**LEARN** (Extract meaning):
- What is the right component size?
- Should calculations be in a custom hook?
- Should constants be in a config file?

**QUESTION** (Challenge assumptions):
- Why is retention modeled as 0.92 in one place and a curve in another?
- Why are calculations embedded in components instead of extracted?
- Is the current polling strategy optimal?

---

*Perception complete. Awaiting further instruction from the collective.*

