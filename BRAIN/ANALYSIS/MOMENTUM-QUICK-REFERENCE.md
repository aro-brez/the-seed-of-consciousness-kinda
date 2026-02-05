# BREZ Momentum Dashboard - Quick Reference

**For**: ARŌ, product team, engineering
**Purpose**: One-page summary of critical learnings
**Updated**: 2026-02-05

---

## Financial Core

| Metric | Value | Notes |
|--------|-------|-------|
| Monthly ARPU | $100 | Per subscriber per month |
| Customer LTV | $340 | Full lifetime value |
| DTC Take Rate | 43% | Stable Jan 1-29 |
| DTC Contrib. Margin | 43% | Available for reinvestment |
| Retail Contrib. Margin | 30% | Lower, but channels synergize |
| Monthly Churn | 700 subs | At 14K base = net negative |
| Retail Velocity | 14-33% | Of DTC ad spend |

## CAC Decision Matrix (The Spine)

| CAC Range | Status | Action | Spend Change |
|-----------|--------|--------|--------------|
| $0-55 | EXCEPTIONAL | Scale Aggressively | +50-75% |
| $55-70 | STRONG | Scale | +30-50% |
| $70-80 | ON_TARGET | Scale Modest | +10-20% |
| $80-90 | ELEVATED | Hold | Monitor 1-2 days |
| $90-100 | HIGH | Reduce | -10-20% |
| $100+ | CEILING | Reduce Significant | -30-40% |

**Core Rule**: Below $55 = aggressive opportunity. Above $100 = approaching loss (LTV/CAC < 3.4x).

## Retention Curve (Why Compounding Works)

Cohort retention by month post-acquisition:
```
Month 0: 100% (initial)
Month 1: 85%
Month 2: 72%
Month 3: 65%
Month 4: 58%
Month 5: 52%
Month 6: 48%
Month 12: 41%
```

**Why it matters**: Each month, you keep 58-65% of prior subs + gain new ones = stacking effect.

## Compound Growth: The Flywheel

**Without CM reinvestment** (fixed $140K/month):
- 3 months: $1.2M revenue, ~3K subs
- 6 months: $2.4M revenue, ~5K subs
- 12 months: $5.2M revenue, ~9K subs

**With CM reinvestment** (all 43% margin fed back):
- 3 months: $1.4M revenue, ~3.5K subs
- 6 months: $3.6M revenue, ~7K subs
- 12 months: $12M revenue, ~18K subs

**Multiplier**: 2.3x faster growth with reinvestment.

## Critical Equations

```
Payback Period (days) = CAC ÷ MONTHLY_ARPU × 30
                      = CAC ÷ $100 × 30

LTV:CAC Ratio = $340 ÷ CAC
              (Must be > 3x; ideal > 5x)

Net Sub Growth = Gross Subs - Churn
               = 1,827 - 700 = 1,127

Business Growth % ≈ Net Sub Growth %
                  (Plus 14-33% from retail velocity)

Cash Required = 3 × Monthly Spend + (Monthly Spend × Payback Days/30)
```

## What Actually Moves the Needle

1. **CAC Efficiency** - Everything else follows
2. **Churn Reduction** - We're net negative; this is THE problem
3. **Margin Reinvestment** - Not reinvesting CM = leaving growth on table
4. **Retention** - Cohort curves prove 40%+ long-term retention = sustainable base
5. **Volume/Spread** - Retail velocity adds 14-33% on top of direct spend

## Assumptions to Monitor

- **ARPU=$100**: Validates slowly, can change with pricing
- **Take Rate=43%**: Stable except at high spend (degrades)
- **Retention Curve**: Specific to current product; improves with improvements
- **CAC=$55-70**: Validates daily, fluctuates 15-25%
- **Churn=700/mo**: THE wildcard; improves with product, seasonality

## Dangerous Assumptions

- Linear extrapolation (not true; cohort compounding)
- Fixed CAC across all spend levels (CAC creeps up at scale)
- No supply constraints (can we actually acquire at projected volumes?)
- No creative fatigue (does ad performance degrade?)
- No market saturation (what's the TAM?)

## UI Patterns That Work

1. **Momentum messaging** changes with pacing (day 1-3 vs day 25)
2. **Interactive sliders** show "$X spend → $Y outcome" instantly
3. **Scenario comparison** (fixed vs. reinvestment) forces clarity on assumptions
4. **Color coding** (green/yellow/red) works without reading text
5. **Cohort breakdown** (yesterday + 7-day + MTD) shows trends
6. **Working capital display** prevents cash crunches

## What to Preserve in Any Refactor

- CAC decision matrix (empirically validated)
- Retention curve (cohort data)
- Compound growth calculation (flywheel math)
- LTV:CAC guardrails
- Honesty about net vs. gross growth
- Interactive scenario modeling

## What to Improve

- Add **churn attribution** (what's causing it?)
- Add **channel-specific CAC** (not universal)
- Add **supply constraints** (realistic volume limits)
- Add **forecast accuracy** (are we predicting well?)
- Add **anomaly detection** (is today unusual?)
- Better separation of financial model from UI

## Files to Know

| File | Purpose |
|------|---------|
| `MomentumHero.tsx` | Main story + scenario simulator |
| `ActionCenter.tsx` | Spend recommendation + CAC matrix |
| `GrowthLevers.tsx` | Growth opportunities |
| `WorkingCapital.tsx` | Financial tracking |
| `growth-types.ts` | Type definitions + decision matrix |

---

## Bottom Line

The Momentum Dashboard works because it's built on **honest financial math**:

- Shows NET growth (not gross)
- Acknowledges churn as the real problem
- Uses cohort-based compounding (not linear)
- Ties everything to CAC efficiency
- Lets users play with scenarios to understand tradeoffs
- Provides clear actions (Scale/Hold/Reduce)

The flywheel only works if margins are reinvested. Without that, growth caps out.

**Next build on**: Churn reduction (biggest lever), channel attribution, supply constraints.
