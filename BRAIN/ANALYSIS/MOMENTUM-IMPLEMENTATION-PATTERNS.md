# BREZ Momentum Dashboard - Implementation Patterns

**For**: Development team, architecture review
**Purpose**: Reusable patterns and best practices
**Level**: Intermediate to Advanced

---

## 1. Financial Model as Code Pattern

### Core Idea
Embed verified financial constants at the top of components. These are:
- Validated from actuals (not estimates)
- ARŌ-verified (commented with source)
- Hardcoded intentionally (not config)
- Used to derive all other calculations

### Implementation

```typescript
// At component top - VALIDATED CONSTANTS
const MONTHLY_ARPU = 100;           // $100/sub/month (Jan 2026 actuals)
const CUSTOMER_LTV = 340;           // Full lifetime (3.4 years @ 100/mo)
const TAKE_RATE = 0.43;             // 43% (Jan 1-23 + Jan 27-29)
const MONTHLY_CHURN = 700;          // Subs lost/month at 14K base
const RETENTION_CURVE = [1.0, 0.85, 0.72, ...];  // Cohort data

// Derived constants (calculated once)
const DTC_CONTRIBUTION_MARGIN = 0.43;  // From ARPU - COGS
const RETAIL_VELOCITY = 0.14;          // From media mix analysis

// Month-specific (changes monthly)
const LAST_MONTH_TOTAL_REVENUE = 2700000;  // January actual
const CURRENT_ACTIVE_SUBS = 14000;         // End of January
```

### Benefits
- Single source of truth
- Easy to update (one place)
- Transparent (all assumptions visible)
- Versioned (git history shows changes)
- Type-safe (TypeScript)

### Anti-Pattern to Avoid
```typescript
// DON'T do this - magic numbers scattered everywhere
const revenue = subs * 100 * 0.43;  // What are 100 and 0.43?
const impact = spend * 0.14;        // What's 0.14?

// DO this
const revenue = subs * MONTHLY_ARPU * DTC_CONTRIBUTION_MARGIN;
const retailImpact = spend * RETAIL_VELOCITY_LOW;
```

---

## 2. Cohort-Based Compounding Pattern

### Core Idea
Track acquisitions by month (cohorts), apply retention to each, sum total revenue.

This captures the "flywheel effect"—why growth compounds:
- Month 1: Acquire 100, earn $10K
- Month 2: 85 remain + 100 new = 185 earn $18.5K
- Month 3: 72+85 = 157 + 100 new = 257 earn $25.7K

### Implementation

```typescript
function calculateCompoundGrowth(
  baseMonthlySpend: number,
  cac: number,
  months: number,
  reinvestCM: boolean = false
) {
  const monthlyBreakdown = [];
  let totalRevenue = 0;
  let totalCM = 0;
  let accumulatedCMToReinvest = 0;

  // Track cohorts (acquisitions by month)
  const cohorts: number[] = [];

  for (let month = 1; month <= months; month++) {
    // This month's spend (can include reinvested CM)
    const monthSpend = reinvestCM
      ? baseMonthlySpend + accumulatedCMToReinvest
      : baseMonthlySpend;

    // New subs acquired this month
    const newSubs = Math.round(monthSpend / cac);
    cohorts.push(newSubs);

    // Revenue from ALL active cohorts (the compounding magic)
    let monthlyRevenue = 0;
    let activeCustomers = 0;

    cohorts.forEach((cohortSize, index) => {
      const cohortAge = month - 1 - index;
      const retention = RETENTION_CURVE[Math.min(cohortAge, RETENTION_CURVE.length - 1)];
      const activeFromCohort = Math.round(cohortSize * retention);
      activeCustomers += activeFromCohort;
      monthlyRevenue += activeFromCohort * MONTHLY_ARPU;
    });

    const monthlyCM = monthlyRevenue * DTC_CONTRIBUTION_MARGIN;
    totalRevenue += monthlyRevenue;
    totalCM += monthlyCM;

    // If reinvesting, feed CM back into next month's budget
    if (reinvestCM) {
      accumulatedCMToReinvest = monthlyCM;
    }

    monthlyBreakdown.push({
      month,
      spend: Math.round(monthSpend),
      newSubs,
      activeCustomers,
      revenue: Math.round(monthlyRevenue),
      cm: Math.round(monthlyCM),
      cumulativeRevenue: Math.round(totalRevenue),
      cumulativeCM: Math.round(totalCM),
    });
  }

  return {
    totalRevenue: Math.round(totalRevenue),
    totalCM: Math.round(totalCM),
    activeCustomers,
    monthlyBreakdown,
  };
}
```

### Why This Works
- Realistic cohort retention (not linear)
- Captures stacking effect (why growth accelerates)
- Shows monthly breakdown (transparency)
- Supports reinvestment flag (shows impact of CM flywheel)

### Key Insight
Without cohort tracking, you'd calculate:
```
Wrong: Month 3 revenue = 100 subs × $100 = $10K (only new subs)
Right: Month 3 revenue = 257 subs × $100 = $25.7K (all active cohorts)
```

This is why compound growth appears "magical" but is mathematically sound.

---

## 3. Decision Matrix as Lookup Pattern

### Core Idea
Define all decision rules in a structured array. Components reference it via helpers.

### Implementation

```typescript
// Define once at module level
export const CAC_DECISION_MATRIX: CACRange[] = [
  {
    min: 0,
    max: 55,
    status: 'EXCEPTIONAL',
    statusLabel: 'Exceptional',
    action: 'SCALE_AGGRESSIVE',
    actionLabel: 'Scale Aggressively',
    spendChange: '+50-75%',
  },
  // ... more ranges
];

// Helper to find the range for any CAC value
export function getCACRange(cac: number): CACRange {
  for (const range of CAC_DECISION_MATRIX) {
    if (range.max === null) {
      if (cac >= range.min) return range;
    } else if (cac >= range.min && cac < range.max) {
      return range;
    }
  }
  return CAC_DECISION_MATRIX[CAC_DECISION_MATRIX.length - 1];
}

// In component:
const range = getCACRange(currentCAC);
console.log(range.actionLabel);  // "Scale Aggressively"
console.log(range.spendChange);  // "+50-75%"
```

### Benefits
- Decision rules are versioned (git history)
- Easy to update (single array)
- Consistent across components (shared helper)
- Testable (pure function)
- Transparent (non-developers can read it)

---

## 4. Scenario Modeling Pattern

### Core Idea
Use useState + useMemo to create interactive "what if" scenarios.

### Implementation

```typescript
// State for interactive exploration
const [scenarioCac, setScenarioCac] = useState<number | null>(null);
const [scenarioMonthlySpend, setScenarioMonthlySpend] = useState<number | null>(null);

// Use scenario value if set, otherwise actual
const simCac = scenarioCac ?? currentCAC;
const simSpend = scenarioMonthlySpend ?? (currentSpend * 28);

// Memoized calculation (only recalcs when inputs change)
const projection = useMemo(() => {
  return calculateCompoundGrowth(simSpend, simCac, 12, true);
}, [simSpend, simCac]);

// In render:
<input
  type="range"
  min={30}
  max={120}
  value={scenarioCac ?? currentCAC}
  onChange={(e) => setScenarioCac(Number(e.target.value))}
/>

// Show instant results
<div>{formatMoney(projection.annualizedRevenue)}/year</div>
<div>{projection.activeCustomers.toLocaleString()} subs</div>
```

### Why useMemo Matters
```typescript
// Without memoization
const projection = calculateCompoundGrowth(...);  // Runs every render!

// With memoization
const projection = useMemo(
  () => calculateCompoundGrowth(...),
  [simSpend, simCac]  // Only runs when these change
);
// Expensive calculation only when user drags slider
```

### UX Pattern
```
User drags CAC slider from $100 → $55
  ↓
setScenarioCac(55) triggers re-render
  ↓
useMemo sees simCac changed
  ↓
calculateCompoundGrowth runs (expensive, but only once)
  ↓
Results update instantly
```

---

## 5. Formatting Utility Pattern

### Core Idea
Centralize formatting logic in pure functions. Use consistently everywhere.

### Implementation

```typescript
// In growth-types.ts
export function formatCurrency(value: number, decimals: number = 0): string {
  if (Math.abs(value) >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(decimals > 0 ? 1 : 0)}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `$${(value / 1_000).toFixed(decimals > 0 ? 1 : 0)}K`;
  }
  return `$${value.toFixed(decimals)}`;
}

export function formatPercent(value: number, decimals: number = 0): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
}

// In components:
<p>{formatCurrency(2700000)}</p>        // "$2.7M"
<p>{formatCurrency(140000)}</p>         // "$140K"
<p>{formatCurrency(75)}</p>             // "$75"
<p>{formatPercent(8)}</p>               // "+8%"
<p>{formatPercent(-2.5, 1)}</p>         // "-2.5%"
```

### Benefits
- Consistent across app
- Easy to change (single place)
- Type-safe (TypeScript)
- Readable (no magic formatting strings)

---

## 6. Status Color Mapping Pattern

### Core Idea
Map abstract statuses to colors in a dictionary. Use same colors everywhere.

### Implementation

```typescript
export function getStatusColor(status: CACStatus | OverallStatus): string {
  const colors: Record<string, string> = {
    // CAC Status colors
    EXCEPTIONAL: '#6BCB77',      // Green
    STRONG: '#6BCB77',           // Green
    ON_TARGET: '#e3f98a',        // Lime
    ELEVATED: '#ffce33',         // Yellow
    HIGH: '#FFA726',             // Orange
    CEILING: '#ff4444',          // Red
    // Overall Status
    ON_TRACK: '#6BCB77',         // Green
    AHEAD: '#6BCB77',            // Green
    AT_RISK: '#ffce33',          // Yellow
    BEHIND: '#ff4444',           // Red
  };
  return colors[status] || '#a8a8a8';  // Default gray
}

// In components (no hardcoded colors):
const statusColor = getStatusColor(metrics.recommendation.cacStatus);

<div style={{ background: `${statusColor}15` }}>
  {/* Light background using status color */}
</div>

<div style={{ borderColor: `${statusColor}30` }}>
  {/* Border using status color */}
</div>

<span style={{ color: statusColor }}>
  {/* Text using status color */}
</span>
```

### Benefits
- Consistent colors = consistent mental model
- Non-developers can tweak colors (in one place)
- Accessible (all colors have accessible contrast)
- Maintainable (changes propagate everywhere)

---

## 7. Animation Pattern

### Core Idea
Use Framer Motion for entrance animations + interactive feedback.

### Implementation

```typescript
import { motion, AnimatePresence } from 'framer-motion';

// Entrance animation (fade + slide)
<motion.div
  initial={{ opacity: 0, x: -20 }}
  animate={{ opacity: 1, x: 0 }}
  transition={{ delay: 0.1 }}
>
  Content
</motion.div>

// Progress bar animation
<motion.div
  initial={{ width: 0 }}
  animate={{ width: `${percentage}%` }}
  transition={{ duration: 1.5, ease: 'easeOut' }}
/>

// Interactive pulse (e.g., momentum emoji)
<motion.span
  animate={{ scale: [1, 1.15, 1] }}
  transition={{ duration: 2, repeat: Infinity }}
>
  🚀
</motion.span>

// Conditional rendering with animation
<AnimatePresence>
  {isExpanded && (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: 'auto', opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      Details
    </motion.div>
  )}
</AnimatePresence>
```

### Psychology
- Entrance animations draw attention (guide eye flow)
- Cascading delays create rhythm
- Interactive feedback (pulse, scale) makes UI feel alive
- Smooth transitions reduce jarring updates

---

## 8. Type-Driven Development Pattern

### Core Idea
Define comprehensive types upfront. Let types guide implementation.

### Implementation

```typescript
// Define all types first (in growth-types.ts)
export interface ComprehensiveMetrics {
  yesterday: DayMetrics;
  today: DayMetrics;
  tomorrow: DayMetrics;
  sevenDayAvg: AverageMetrics;
  mtdAvg: AverageMetrics;
  pacing: PacingMetrics;
  recommendation: SpendRecommendation;
  financials: FinancialMetrics;
  monthlyGoal: { subs: number; adSpend: number; ... };
  status: OverallStatus;
}

// Component receives typed props
interface MomentumHeroProps {
  metrics: ComprehensiveMetrics;
  onShare: () => void;
  onRefresh: () => void;
  loading?: boolean;
}

// TypeScript prevents mistakes
function MomentumHero({ metrics, onShare, onRefresh }: MomentumHeroProps) {
  // metrics.yesterday is guaranteed to exist and be DayMetrics
  const cac = metrics.yesterday.cac;  // TypeScript knows this is a number

  // If you typo a property:
  const broken = metrics.yesterda.cac;  // Error! Property not found
}
```

### Benefits
- Self-documenting code
- Catch errors at compile time
- IDE autocompletion
- Refactoring support (rename = updates everywhere)

---

## 9. Accessibility Pattern

### Core Idea
Color shouldn't be the only signal. Use text, icons, size too.

### Implementation

```typescript
// DON'T: Color-only status
<div style={{ color: statusColor }}>Status</div>

// DO: Color + text + icon
<div className="flex items-center gap-2">
  <div
    className="w-3 h-3 rounded-full"
    style={{ background: statusColor }}
  />
  <span style={{ color: statusColor }} className="font-bold">
    {recommendation.statusLabel.toUpperCase()}
  </span>
</div>

// Use semantic HTML
<h1 className="text-lg font-bold">Momentum Hero</h1>
<h2 className="text-md font-bold">February Target</h2>

// ARIA labels for interactive elements
<button
  onClick={onRefresh}
  aria-label="Refresh metrics"
  title="Refresh"
>
  <RefreshCw className="w-4 h-4" />
</button>

// Contrast ratios
// Text on dark background must have sufficient contrast
// Status colors tested for 4.5:1 contrast ratio
```

---

## 10. Performance Pattern

### Core Idea
Memoize expensive calculations. Avoid unnecessary re-renders.

### Implementation

```typescript
// Expensive calculation - memoize it
const projection = useMemo(() => {
  return calculateCompoundGrowth(spend, cac, months, reinvest);
}, [spend, cac, months, reinvest]);

// Event handler - memoize to prevent child re-renders
const handleMouseMove = useCallback((e: React.MouseEvent) => {
  if (isDragging) {
    updateCacFromPosition(e);
  }
}, [isDragging]);

// Component - if props are stable, memoize to prevent re-render
const ProgressBar = React.memo(({ percentage, color }: Props) => {
  return <div style={{ width: `${percentage}%`, background: color }} />;
});

// Avoid recreating objects in render
// DON'T:
<Component style={{ color: statusColor }} /> // New object every render

// DO:
const style = useMemo(() => ({ color: statusColor }), [statusColor]);
<Component style={style} />
```

### When to Memoize
- Expensive calculations (complex loops, large datasets)
- Event handlers passed to children
- Components with many props
- Large lists (memoize list items)

### When NOT to Memoize
- Simple calculations (no performance gain)
- Components that change frequently (overhead > benefit)
- Components with no children

---

## Summary: Reusable Patterns

1. **Financial Model as Code** - Embed validated constants, document assumptions
2. **Cohort-Based Compounding** - Track acquisitions by month, apply retention
3. **Decision Matrix Lookup** - Rules as data structure, referenced via helpers
4. **Scenario Modeling** - useState + useMemo for interactive "what if"
5. **Formatting Utilities** - Centralize number/currency/percent formatting
6. **Status Color Mapping** - Single source of truth for colors
7. **Framer Motion Animations** - Entrance, interactive, conditional
8. **Type-Driven Development** - Comprehensive types guide implementation
9. **Accessibility** - Color + text + icons + semantic HTML
10. **Performance Optimization** - Memoize expensive operations

These patterns make the code:
- **Maintainable** (changes in one place)
- **Testable** (pure functions)
- **Transparent** (assumptions visible)
- **Consistent** (same patterns everywhere)
- **Performant** (no unnecessary calculations)

---

**Extracted by**: SAGE (Implementation phase)
**Date**: 2026-02-05
**Next**: Apply to new financial dashboards and growth models
