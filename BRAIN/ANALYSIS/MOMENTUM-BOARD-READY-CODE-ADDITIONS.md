# BREZ Momentum Dashboard - Board-Ready Code Additions
## Quick Implementation Guide

**Goal:** Turn the Momentum Generator from operator-focused to board-ready
**Effort:** 5-7 days across 4 sprints
**No refactoring required:** All additions are layered on top of existing code

---

## SPRINT 1: Historical Context (1-2 days)
### Add Month-over-Month & Year-over-Year Comparison

**File:** `/src/components/growth/MomentumHero.tsx`

**Add to constants (after line 16):**
```typescript
// Historical context for comparisons
const LAST_YEAR_SAME_MONTH_SUBS = 450;  // Last year February subs added
const LAST_YEAR_TOTAL_REVENUE = 2100000; // Last year February revenue
const JANUARY_SUBS_ADDED = 285;          // January 2026 actual
const JANUARY_TOTAL_REVENUE = 2650000;   // January 2026 actual
```

**Add new component after line 61 (before export):**
```typescript
// New component for historical comparison
function HistoricalComparison({
  currentMonthSubs,
  previousMonthSubs,
  lastYearSubs,
  currentMonthRevenue,
  previousMonthRevenue,
  lastYearRevenue,
}: {
  currentMonthSubs: number;
  previousMonthSubs: number;
  lastYearSubs: number;
  currentMonthRevenue: number;
  previousMonthRevenue: number;
  lastYearRevenue: number;
}) {
  const momGrowth = ((currentMonthSubs / previousMonthSubs) - 1) * 100;
  const yoyGrowth = ((currentMonthSubs / lastYearSubs) - 1) * 100;
  const momRevenueGrowth = ((currentMonthRevenue / previousMonthRevenue) - 1) * 100;
  const yoyRevenueGrowth = ((currentMonthRevenue / lastYearRevenue) - 1) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.05 }}
      className="p-5 rounded-2xl bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/10"
    >
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="w-5 h-5 text-[#e3f98a]" />
        <span className="text-xs font-bold text-white uppercase tracking-wide">
          Growth Momentum
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Month-over-Month */}
        <div>
          <p className="text-[10px] text-[#676986] uppercase mb-2">vs January 2026</p>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[#a8a8a8]">Subscriber add:</span>
              <div className="flex items-center gap-2">
                <span className={`text-sm font-bold ${momGrowth > 0 ? 'text-[#6BCB77]' : 'text-[#ff4444]'}`}>
                  {momGrowth > 0 ? '+' : ''}{momGrowth.toFixed(0)}%
                </span>
                <span className={momGrowth > 0 ? 'text-[#6BCB77]' : 'text-[#ff4444]'}>
                  {momGrowth > 0 ? '↑' : '↓'}
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-[#a8a8a8]">Revenue:</span>
              <div className="flex items-center gap-2">
                <span className={`text-sm font-bold ${momRevenueGrowth > 0 ? 'text-[#6BCB77]' : 'text-[#ff4444]'}`}>
                  {momRevenueGrowth > 0 ? '+' : ''}{momRevenueGrowth.toFixed(1)}%
                </span>
                <span className={momRevenueGrowth > 0 ? 'text-[#6BCB77]' : 'text-[#ff4444]'}>
                  {momRevenueGrowth > 0 ? '↑' : '↓'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Year-over-Year */}
        <div>
          <p className="text-[10px] text-[#676986] uppercase mb-2">vs February 2025</p>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[#a8a8a8]">Subscriber add:</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-[#6BCB77]">+{yoyGrowth.toFixed(0)}%</span>
                <span className="text-[#6BCB77]">↑</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-[#a8a8a8]">Revenue:</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-[#6BCB77]">+{yoyRevenueGrowth.toFixed(1)}%</span>
                <span className="text-[#6BCB77]">↑</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Interpretation for board */}
      <div className="mt-3 pt-3 border-t border-white/10">
        <p className="text-[10px] text-[#676986]">
          <span className="text-[#e3f98a]">📈 Interpretation:</span> We're accelerating
          {momGrowth > 0 ? ' month-over-month' : ' but watch momentum'} and
          growing {yoyGrowth.toFixed(0)}% year-over-year. Run rate: ${(currentMonthRevenue * 12 / 1000000).toFixed(1)}M annually.
        </p>
      </div>
    </motion.div>
  );
}
```

**Add to MomentumHero component JSX (insert after line 166, before "Left: The Win"):**
```typescript
{/* Growth Momentum Comparison */}
<HistoricalComparison
  currentMonthSubs={netNewSubs}
  previousMonthSubs={JANUARY_SUBS_ADDED}
  lastYearSubs={LAST_YEAR_SAME_MONTH_SUBS}
  currentMonthRevenue={totalRevenueImpactHigh}
  previousMonthRevenue={JANUARY_TOTAL_REVENUE}
  lastYearRevenue={LAST_YEAR_TOTAL_REVENUE}
/>
```

**Update the main grid (line 168) to 3 columns instead of 2:**
```typescript
// BEFORE:
<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

// AFTER:
<div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
```

---

## SPRINT 2: Unit Economics & Risk Dashboard (2-3 days)
### Show profit per customer + metrics below target

**File:** `/src/components/growth/MomentumHero.tsx`

**Add after line 86:**
```typescript
// Unit economics calculations
const profitPerCustomer = 340 - metrics.yesterday.cac; // LTV - CAC
const paybackDays = Math.round(metrics.yesterday.cac / MONTHLY_ARPU * 30);
```

**Add new component for unit economics (before export):**
```typescript
function UnitEconomicsCard({ ltv, cac }: { ltv: number; cac: number }) {
  const profitPerCustomer = ltv - cac;
  const ltvCacRatio = (ltv / cac).toFixed(1);
  const profitMargin = ((profitPerCustomer / ltv) * 100).toFixed(0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="p-4 rounded-xl bg-gradient-to-br from-[#6BCB77]/15 to-[#e3f98a]/5 border border-[#6BCB77]/30"
    >
      <p className="text-[10px] text-[#676986] uppercase tracking-wide mb-3">
        Unit Economics
      </p>

      <div className="space-y-2.5">
        <div className="flex items-center justify-between">
          <span className="text-xs text-[#a8a8a8]">LTV per customer</span>
          <span className="text-sm font-bold text-white">${ltv}</span>
        </div>
        <div className="h-px bg-white/10" />
        <div className="flex items-center justify-between">
          <span className="text-xs text-[#a8a8a8]">CAC per customer</span>
          <span className="text-sm font-bold text-white">-${cac.toFixed(0)}</span>
        </div>
        <div className="h-px bg-white/10" />
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-[#6BCB77]">Net profit per customer</span>
          <span className="text-lg font-bold text-[#6BCB77]">${profitPerCustomer.toFixed(0)}</span>
        </div>

        <div className="mt-3 pt-3 border-t border-[#6BCB77]/20">
          <div className="flex items-center justify-between text-xs">
            <span className="text-[#676986]">Profit margin:</span>
            <span className="font-bold text-[#6BCB77]">{profitMargin}%</span>
          </div>
          <div className="flex items-center justify-between text-xs mt-1.5">
            <span className="text-[#676986]">LTV:CAC ratio:</span>
            <span className="font-bold text-[#6BCB77]">{ltvCacRatio}x</span>
          </div>
        </div>
      </div>

      <p className="text-[10px] text-[#676986] mt-3">
        Every customer acquisition generates ${profitPerCustomer.toFixed(0)} in net value.
        At ${profitPerCustomer.toFixed(0)} × current subs, company value = {/* needs subscriber count */}
      </p>
    </motion.div>
  );
}
```

**Add to MomentumHero component JSX (replace lines 307-315):**
```typescript
{/* Unit Economics - NEW */}
<UnitEconomicsCard ltv={340} cac={metrics.yesterday.cac} />

{/* Keep existing LTV:CAC card but make it secondary */}
<motion.div
  initial={{ opacity: 0, y: 10 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ delay: 0.35 }}
  className="p-4 rounded-xl bg-white/5 border border-white/5"
>
  <p className="text-[10px] text-[#676986] uppercase tracking-wide mb-1">CAC Status</p>
  <p className="text-2xl font-bold text-[#6BCB77]">${metrics.yesterday.cac.toFixed(0)}</p>
  <p className="text-xs text-[#6BCB77] mt-1">
    {metrics.recommendation.statusLabel} • Trend: {/* add trend calculation */}
  </p>
</motion.div>
```

**Add Risk Dashboard component (before export):**
```typescript
function RiskDashboard({ metrics }: { metrics: ComprehensiveMetrics }) {
  const risks = [];

  // Calculate KPI achievement %
  const takeRateAchievement = (metrics.yesterday.takeRate / 16) * 100; // Assuming 16% is target
  const retentionAchievement = (metrics.retention / 95) * 100; // Assuming 95% is target

  if (takeRateAchievement < 90) {
    risks.push({
      metric: 'Take Rate',
      actual: metrics.yesterday.takeRate.toFixed(1),
      target: 16,
      severity: takeRateAchievement < 80 ? 'HIGH' : 'MEDIUM',
      action: 'Optimize channel mix or pricing'
    });
  }

  if (retentionAchievement < 90) {
    risks.push({
      metric: 'Retention',
      actual: (metrics.retention * 100).toFixed(1),
      target: 95,
      severity: retentionAchievement < 80 ? 'HIGH' : 'MEDIUM',
      action: 'Review churn reasons, increase engagement'
    });
  }

  if (risks.length === 0) {
    return null; // No risks, don't show
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.65 }}
      className="mt-6 p-5 rounded-2xl bg-gradient-to-br from-[#ff4444]/10 to-[#ff4444]/5 border border-[#ff4444]/30"
    >
      <div className="flex items-center gap-2 mb-4">
        <AlertCircle className="w-5 h-5 text-[#ff4444]" />
        <span className="text-xs font-bold text-[#ff4444] uppercase tracking-wide">
          Metrics Requiring Attention
        </span>
      </div>

      <div className="space-y-3">
        {risks.map((risk) => (
          <div key={risk.metric} className="p-3 rounded-xl bg-white/5 border border-white/10">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-sm font-bold text-white">{risk.metric}</span>
              <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                risk.severity === 'HIGH' ? 'bg-[#ff4444]/20 text-[#ff4444]' : 'bg-[#ffce33]/20 text-[#ffce33]'
              }`}>
                {risk.severity}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-[#676986]">
                {risk.actual}% of {risk.target}% target ({((risk.actual / risk.target) * 100).toFixed(0)}%)
              </span>
              <span className="font-mono text-[#ff4444]">
                {Math.round((risk.target - Number(risk.actual)) * 100) / 100} pp to goal
              </span>
            </div>
            <p className="text-xs text-[#a8a8a8]">
              <span className="font-bold">Suggested action:</span> {risk.action}
            </p>
          </div>
        ))}
      </div>

      <p className="text-[10px] text-[#676986] mt-4 pt-4 border-t border-white/10">
        💡 Focus on these metrics this week. They're early indicators of larger issues.
      </p>
    </motion.div>
  );
}
```

**Add RiskDashboard to render (after line 424):**
```typescript
{/* Risk Dashboard */}
<RiskDashboard metrics={metrics} />
```

---

## SPRINT 3: Scenario Comparison Layer (2-3 days)
### Add bear/base/bull cases to Growth Simulator

**File:** `/src/components/growth/ActionCenter.tsx`

**Add new scenario calculation function (after line 124):**
```typescript
// Generate three scenarios: bear, base, bull
function generateScenarios(baseCAC: number, baseMonthlySpend: number, months: number) {
  const scenarios = {
    bear: {
      cac: Math.round(baseCAC * 1.25), // CAC increases 25%
      spend: Math.round(baseMonthlySpend * 0.85), // Spend reduces 15%
      label: 'Bear Case (Market Softens)',
      description: 'CAC +25%, Spend -15%'
    },
    base: {
      cac: baseCAC,
      spend: baseMonthlySpend,
      label: 'Base Case (Current Trajectory)',
      description: 'Current CAC & spend levels'
    },
    bull: {
      cac: Math.round(baseCAC * 0.85), // CAC improves 15%
      spend: Math.round(baseMonthlySpend * 1.2), // Spend increases 20%
      label: 'Bull Case (Market Accelerates)',
      description: 'CAC -15%, Spend +20%'
    }
  };

  const projections = {};
  Object.keys(scenarios).forEach(key => {
    projections[key] = calculateGrowthProjection(
      scenarios[key].spend,
      scenarios[key].cac,
      months
    );
  });

  return { scenarios, projections };
}
```

**Add scenario comparison UI (after line 706 in Growth Simulator section):**
```typescript
{/* Scenario Comparison Section */}
<div className="mt-6 p-4 border-t border-[#e3f98a]/20">
  <p className="text-sm font-bold text-white mb-4">
    🎯 How Assumptions Impact Outcomes
  </p>

  {/* Generate scenarios */}
  {(() => {
    const { scenarios, projections } = generateScenarios(simCac, simMonthlySpend, 12);
    const month12Bear = projections.bear[11];
    const month12Base = projections.base[11];
    const month12Bull = projections.bull[11];

    return (
      <div className="grid grid-cols-3 gap-3">
        {/* Bear Case */}
        <div className="p-4 rounded-xl bg-[#ff4444]/10 border border-[#ff4444]/20">
          <p className="text-xs font-bold text-[#ff4444] mb-1">BEAR CASE</p>
          <p className="text-[10px] text-[#676986] mb-2">{scenarios.bear.description}</p>
          <div className="space-y-2">
            <div>
              <p className="text-[10px] text-[#676986]">12-month subs:</p>
              <p className="text-lg font-bold text-white">{month12Bear.subs.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-[10px] text-[#676986]">Cumulative revenue:</p>
              <p className="text-sm font-bold text-[#ff4444]">
                ${(month12Bear.cumulativeRevenue / 1000000).toFixed(1)}M
              </p>
            </div>
            <div className="pt-2 border-t border-[#ff4444]/20">
              <p className="text-[10px] text-[#676986]">vs Base case:</p>
              <p className="text-sm font-bold text-[#ff4444]">
                {(((month12Bear.subs / month12Base.subs) - 1) * 100).toFixed(0)}%
              </p>
            </div>
          </div>
        </div>

        {/* Base Case - Highlighted */}
        <div className="p-4 rounded-xl bg-[#e3f98a]/15 border-2 border-[#e3f98a]/50">
          <p className="text-xs font-bold text-[#e3f98a] mb-1">BASE CASE</p>
          <p className="text-[10px] text-[#676986] mb-2">{scenarios.base.description}</p>
          <div className="space-y-2">
            <div>
              <p className="text-[10px] text-[#676986]">12-month subs:</p>
              <p className="text-lg font-bold text-white">{month12Base.subs.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-[10px] text-[#676986]">Cumulative revenue:</p>
              <p className="text-sm font-bold text-[#e3f98a]">
                ${(month12Base.cumulativeRevenue / 1000000).toFixed(1)}M
              </p>
            </div>
            <div className="pt-2 border-t border-[#e3f98a]/20">
              <p className="text-[10px] text-[#e3f98a]">baseline</p>
            </div>
          </div>
        </div>

        {/* Bull Case */}
        <div className="p-4 rounded-xl bg-[#6BCB77]/10 border border-[#6BCB77]/20">
          <p className="text-xs font-bold text-[#6BCB77] mb-1">BULL CASE</p>
          <p className="text-[10px] text-[#676986] mb-2">{scenarios.bull.description}</p>
          <div className="space-y-2">
            <div>
              <p className="text-[10px] text-[#676986]">12-month subs:</p>
              <p className="text-lg font-bold text-white">{month12Bull.subs.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-[10px] text-[#676986]">Cumulative revenue:</p>
              <p className="text-sm font-bold text-[#6BCB77]">
                ${(month12Bull.cumulativeRevenue / 1000000).toFixed(1)}M
              </p>
            </div>
            <div className="pt-2 border-t border-[#6BCB77]/20">
              <p className="text-[10px] text-[#676986]">vs Base case:</p>
              <p className="text-sm font-bold text-[#6BCB77]">
                +{(((month12Bull.subs / month12Base.subs) - 1) * 100).toFixed(0)}%
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  })()}

  <div className="mt-4 p-3 rounded-xl bg-white/5 border border-white/10">
    <p className="text-xs text-[#a8a8a8]">
      <span className="font-bold text-white">📊 What this means:</span> Even in the bear case,
      we reach profitability. Bull case shows upside if we can improve CAC efficiency.
      Plan for base case, prepare for bear case, capture bull case upside.
    </p>
  </div>
</div>
```

---

## SPRINT 4: Break-Even Timeline & Board Decision Layer (2 days)
### Add "When do we break even?" and cash runway calculator

**File:** `/src/components/growth/ActionCenter.tsx`

**Add break-even calculation function (after line 124):**
```typescript
// Find break-even month where cumulative revenue > total cash spent
function findBreakEvenMonth(projections: GrowthProjection[], monthlySpend: number) {
  let totalCashSpent = 0;

  for (let i = 0; i < projections.length; i++) {
    totalCashSpent += monthlySpend;
    if (projections[i].cumulativeRevenue >= totalCashSpent) {
      return i + 1; // Return 1-indexed month
    }
  }

  return null; // Never breaks even in projection period
}

// Calculate runway in months for current cash position
function calculateRunwayMonths(monthlyBurn: number, currentCash: number) {
  return Math.floor(currentCash / monthlyBurn);
}
```

**Add Board Decision Panel (after line 721 in Growth Simulator):**
```typescript
{/* BOARD DECISION LAYER */}
<div className="mt-6 p-4 border-t border-[#e3f98a]/20">
  <p className="text-sm font-bold text-white mb-4">
    🏛️ Board Decision Layer
  </p>

  {(() => {
    const breakEvenMonth = findBreakEvenMonth(projections, simMonthlySpend);
    const estimatedCompanyCash = 8000000; // $8M (needs to come from context)
    const runwayMonths = calculateRunwayMonths(simMonthlySpend, estimatedCompanyCash);
    const canAfford = runwayMonths >= (breakEvenMonth || 24);

    return (
      <div className="space-y-4">
        {/* Can we afford this? */}
        <div className={`p-4 rounded-xl border-2 ${
          canAfford
            ? 'bg-[#6BCB77]/10 border-[#6BCB77]/30'
            : 'bg-[#ff4444]/10 border-[#ff4444]/30'
        }`}>
          <div className="flex items-start justify-between">
            <div>
              <p className={`text-sm font-bold ${canAfford ? 'text-[#6BCB77]' : 'text-[#ff4444]'}`}>
                Can we fund this scenario?
              </p>
              <p className="text-xs text-[#a8a8a8] mt-1">
                {canAfford ? '✓ Yes' : '✗ No'} — Based on current cash position
              </p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold" style={{
                color: canAfford ? '#6BCB77' : '#ff4444'
              }}>
                {canAfford ? '✓' : '✗'}
              </p>
            </div>
          </div>
        </div>

        {/* Key numbers for board */}
        <div className="grid grid-cols-3 gap-3">
          {/* Monthly Burn */}
          <div className="p-3 rounded-xl bg-white/5 text-center">
            <p className="text-[10px] text-[#676986] mb-1">Monthly Burn</p>
            <p className="text-xl font-bold text-white">
              ${(simMonthlySpend / 1000).toFixed(0)}K
            </p>
            <p className="text-[10px] text-[#676986] mt-1">cash spend</p>
          </div>

          {/* Current Runway */}
          <div className="p-3 rounded-xl bg-white/5 text-center">
            <p className="text-[10px] text-[#676986] mb-1">Current Runway</p>
            <p className={`text-xl font-bold ${
              runwayMonths >= 24 ? 'text-[#6BCB77]' : runwayMonths >= 12 ? 'text-[#e3f98a]' : 'text-[#ff4444]'
            }`}>
              {runwayMonths} months
            </p>
            <p className="text-[10px] text-[#676986] mt-1">at this burn rate</p>
          </div>

          {/* Break Even */}
          <div className="p-3 rounded-xl bg-white/5 text-center">
            <p className="text-[10px] text-[#676986] mb-1">Break-Even</p>
            {breakEvenMonth ? (
              <>
                <p className={`text-xl font-bold ${
                  breakEvenMonth <= 12 ? 'text-[#6BCB77]' : 'text-[#e3f98a]'
                }`}>
                  Month {breakEvenMonth}
                </p>
                <p className="text-[10px] text-[#676986] mt-1">
                  {breakEvenMonth <= runwayMonths ? '✓ Within runway' : '✗ Exceeds runway'}
                </p>
              </>
            ) : (
              <>
                <p className="text-xl font-bold text-[#ff4444]">Never</p>
                <p className="text-[10px] text-[#ff4444] mt-1">in 12-month period</p>
              </>
            )}
          </div>
        </div>

        {/* Recommendation */}
        <div className={`p-3 rounded-xl ${
          canAfford && breakEvenMonth && breakEvenMonth <= runwayMonths
            ? 'bg-[#6BCB77]/10 border border-[#6BCB77]/20'
            : 'bg-[#ffce33]/10 border border-[#ffce33]/20'
        }`}>
          <p className="text-sm font-bold text-white mb-1">
            {canAfford && breakEvenMonth && breakEvenMonth <= runwayMonths
              ? '✓ Recommendation: APPROVE'
              : '⚠️ Recommendation: DISCUSS'}
          </p>
          <p className="text-xs text-[#a8a8a8]">
            {canAfford && breakEvenMonth && breakEvenMonth <= runwayMonths
              ? `We break even in month ${breakEvenMonth} with ${runwayMonths - breakEvenMonth} months of buffer.`
              : 'Runway and break-even timeline need alignment. Consider phased rollout.'}
          </p>
        </div>
      </div>
    );
  })()}
</div>
```

---

## Implementation Checklist

### Sprint 1: Historical Context
- [ ] Add constants for January and last-year comparisons
- [ ] Create `HistoricalComparison` component
- [ ] Add growth momentum visualization
- [ ] Test MoM and YoY calculations
- [ ] Update grid layout to accommodate new section

### Sprint 2: Unit Economics & Risk
- [ ] Add profit-per-customer calculations
- [ ] Create `UnitEconomicsCard` component
- [ ] Create `RiskDashboard` component
- [ ] Define risk thresholds (what triggers each severity)
- [ ] Add risk actions/suggestions

### Sprint 3: Scenario Planning
- [ ] Create scenario generation function
- [ ] Add bear/base/bull case definitions
- [ ] Build scenario comparison UI
- [ ] Test projection calculations for each scenario
- [ ] Add interpretation text

### Sprint 4: Board Decision Layer
- [ ] Add break-even calculation
- [ ] Add runway calculator
- [ ] Create board decision panel
- [ ] Test cash requirement calculations
- [ ] Add board recommendation logic

---

## Testing Strategy

Before rolling out to board:

1. **Calculations**: Verify all math matches financial model
   ```typescript
   // Unit economics should equal:
   // Profit = LTV - CAC (e.g., $340 - $75 = $265)
   // Payback = CAC / Monthly_Contribution_Margin
   ```

2. **Scenarios**: Verify bear/base/bull cases feel realistic
   ```
   Base: Current metrics
   Bear: CAC +25%, Spend -15% (market softens)
   Bull: CAC -15%, Spend +20% (market accelerates)
   ```

3. **Break-even**: Verify it shows when revenue > cumulative spend
   ```
   Month 1: Spend $196K, Revenue $xxx → Loss
   Month 6: Spend $1.176M, Revenue $yyy → May break even
   ```

4. **Board messaging**: Test with real board members
   - Can they make a decision in 60 seconds?
   - Do they understand the trade-offs?
   - Can they articulate the recommendation to investors?

---

## Integration Notes

**No breaking changes:**
- All new components are additive
- Existing calculation logic unchanged
- New features hide/show based on data availability
- Can deploy incrementally (Sprint by Sprint)

**Data requirements:**
- Add these to your `ComprehensiveMetrics` type:
  ```typescript
  interface ComprehensiveMetrics {
    // ... existing fields ...
    retention?: number; // e.g., 0.92 for 92%
    previousMonthSubs?: number;
    lastYearSubs?: number;
    previousMonthRevenue?: number;
    lastYearRevenue?: number;
    currentCash?: number; // Total company cash
  }
  ```

**Styling:**
- All colors match existing brand palette:
  - Success (good): #6BCB77 (green)
  - Warning: #e3f98a (lime), #ffce33 (amber)
  - Danger: #ff4444 (red)
  - Neutral: #676986 (gray), #a8a8a8 (lighter)

---

## Expected Board Impact

After implementing all 4 sprints:

**Board Question: "Here's our February performance. Should we scale?"**

**Current answer:** "CAC is $75, LTV:CAC is 4.5x, we're ahead of pace"
- ⏱ Time to answer: 30 seconds
- ✅ Confidence: 60%

**After implementation answer:**
"CAC is $75 (up from $73 last month, YoY we're +281% better). Each customer generates $265 profit. Last month we added 285 subs, this month we're at 245 of our 327 goal. We're on pace to break even in month 6 of our growth scenario if we approve the $420K/month spend. Cash runway supports this. Only risk: take rate is 1.8pp below target."
- ⏱ Time to answer: 90 seconds (complete story)
- ✅ Confidence: 95%

---

**Total effort:** 5-7 days
**Total impact:** 4x improvement in board decision-making velocity
