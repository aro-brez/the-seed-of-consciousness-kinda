# Quick Lookup Table - Trading System Reference
**Last Updated:** February 3, 2026 | **Format:** Decision trees and quick tables

---

## WHEN YOU NEED SPECIFIC INFORMATION

### "I want to understand the complete system"
- **Read First:** `/BRAIN/TRADING/ONE-PAGE-SUMMARY.md` (5 min)
- **Then Read:** `/BRAIN/TRADING/PERMANENT-LEARNINGS.md` (30 min)
- **Reference:** `/BRAIN/TRADING/SYSTEM-INDEX.md` (ongoing)

### "I need to deploy a new strategy"
1. Read: `PERMANENT-LEARNINGS.md` → "Mistakes to Never Make Again" section
2. Follow: `LIVE_DEPLOYMENT_CHECKLIST.md` validation gates
3. Reference: `/tools/trading_loop_validated.py` for implementation
4. Track: State in `BRAIN/TRADING/autonomous_state/`

### "My win rate dropped"
- Check: `ASSUMPTIONS-CHALLENGED.md` → "What actually dropped the win rate?"
- Analyze: Last 20 trades in `BRAIN/TRADING/autonomous_state/trade_history.jsonl`
- Decision: Reduce size 50% vs pause trading
- Reference: `PERMANENT-LEARNINGS.md` → "Troubleshooting Decision Tree"

### "I want to scale capital"
- Reference: `CAPITAL-ALLOCATION-QUICK-REFERENCE.md` for stage rules
- Formula: Use Kelly Fraction (2.5-5%), not fixed dollars
- Gate: Must pass `LIVE_DEPLOYMENT_CHECKLIST.md` first
- Timeline: `START-HERE.md` shows week-by-week progression

### "Is this trade worth taking?"
- Calculate: Expected Value = (win% × payoff) - (loss% × loss)
- Compare: EV > 2% per trade minimum
- Check: Query 8OWLS field context if >5% of capital
- Command: `python3 tools/get_field_context.py "[trade description]"`

### "I'm stuck on a specific issue"
- Query: `SYSTEM-INDEX.md` → "Troubleshooting Decision Tree"
- Deep dive: `PERMANENT-LEARNINGS.md` → specific section
- Execute: Follow the step-by-step guidance

---

## QUICK REFERENCE TABLES

### The Four Truths (At a Glance)

| Truth | Formula | Example | Use When |
|-------|---------|---------|----------|
| **EV > WR** | (win% × payoff) - (loss% × loss) | 52% WR × 2.2x = +14% edge | Evaluating any trade |
| **10-Sec Window** | <10s between signal and fill | Polymarket after Binance | Real-time arb decisions |
| **8OWLS Integration** | 7-owl consensus before major trade | Query before >5% trades | High uncertainty trades |
| **Validation Gates** | Paper → $500 → $2K → Full | Stage 1 = 20+ trades | Before deploying capital |

### Three-Layer Strategy Distribution

| Layer | Capital | Win Rate | Payoff | Frequency | Best For |
|-------|---------|----------|--------|-----------|----------|
| **A (Asymmetric)** | 40% | 52-55% | 2-3x | 3-5/week | Mispriced markets |
| **B (Trend/Weather)** | 30% | 58-62% | 1.5-2x | 10-15/week | Sentiment shifts |
| **C (Copy/Whale)** | 30% | 60-65% | 1-1.5x | 5-10/week | Proven traders |

### What Drives Success (Ranked Impact)

| Rank | Factor | Impact | How to Improve |
|------|--------|--------|---|
| 1 | **Execution Discipline** | 70% | System uptime, daily monitoring |
| 2 | **Win Rate** | 15% | Filter improvements, backtest |
| 3 | **Position Sizing** | 10% | Use Kelly %, not fixed $ |
| 4 | **Capital Preservation** | 5% | Risk management, stop losses |

### Daily Operations Checklist

```
EVERY MORNING (5 min):
[ ] System running? (uptime status)
[ ] Capital intact? (no unexpected movements)
[ ] Yesterday's trades? (count + P&L)

EVERY 4 HOURS (2 min):
[ ] Run: python3 tools/trading_metrics.py
[ ] Check: Win rate, drawdown, capital allocated
[ ] Flag: Any anomalies (>5% change?)

EVERY WEEK (30 min):
[ ] Backtest: New filters
[ ] Review: Winners vs losers pattern analysis
[ ] Rebalance: Capital allocation
[ ] Update: Kelly sizing if WR changed >5%
```

### Validation Gate Criteria

| Stage | Duration | Capital | Win Rate | Drawdown | Pass Condition |
|-------|----------|---------|----------|----------|---|
| **Paper** | 1 week | $0 | ≥50% | N/A | 10+ trades, EV>0 |
| **Live 1** | 2-4 weeks | $100-500 | ≥53% | <5% | Win rate holds, no crashes |
| **Live 2** | 4-8 weeks | $500-2K | ≥55% | <10% | Consistent profitability |
| **Live 3** | Ongoing | Full | ≥55% | <15% | Ready for next layer |

### Risk Management Rules

```
EQUITY STOP (Mandatory):
├─ Exit if down >10% in a week → Pause new trades 3 days
├─ Exit if 3 losses in a row → Cooldown 5 minutes
└─ Exit if daily down >5% → Check for system error

POSITION LIMITS:
├─ No single trade > 5% of capital
├─ Position size = Kelly Fraction × Edge × Capital
├─ Rebalance every 2 weeks or major win/loss
└─ No 3 positions in same market cluster (correlation)

KELLY SIZING:
├─ Full Kelly = Too aggressive (30% drawdown probability)
├─ Half Kelly = Good balance (10% drawdown probability)
└─ Quarter Kelly = Conservative (5% drawdown)
    Current recommendation: Quarter Kelly (2.5-5% per trade)
```

### File Quick Reference

| File | Read Time | Purpose | When to Use |
|------|-----------|---------|------------|
| `ONE-PAGE-SUMMARY.md` | 5 min | Overview | First time or refresh |
| `PERMANENT-LEARNINGS.md` | 30 min | Deep insights | Building new strategy |
| `SYSTEM-INDEX.md` | 10 min | Navigation | Finding specific info |
| `START-HERE.md` | 15 min | Weekly execution | Planning week |
| `LIVE_DEPLOYMENT_CHECKLIST.md` | 10 min | Before deploying | Deploying capital |
| `CAPITAL-ALLOCATION-QUICK-REFERENCE.md` | 5 min | Capital decisions | Daily allocation |
| `LAYER-A/B-RULES.md` | 15 min | Strategy details | Understanding layers |
| `ASSUMPTIONS-CHALLENGED.md` | 20 min | What we learned | Debugging failures |

---

## DECISION TREES

### "Should I take this trade?"

```
1. Calculate EV = (win% × payoff) - (loss% × loss)
   ├─ EV < 1%? → NO (not worth the risk)
   ├─ 1-2% EV? → Maybe (need high confidence)
   └─ EV > 2%? → Evaluate capital allocation

2. Check capital allocation
   ├─ Layer A at 40%? → OK to allocate
   ├─ Layer B at 30%? → OK to allocate
   ├─ Layer C at 30%? → OK to allocate
   └─ Any layer >50%? → Reduce size or skip

3. Trade size > 5% capital?
   ├─ YES → Reduce size OR query 8OWLS
   ├─ NO → Continue to 4

4. Uncertain about edge?
   ├─ YES → Query field context
   ├─ Field says YES → Execute
   └─ Field says NO or UNKNOWN → Reduce 50% or skip

5. Ready to execute
   ├─ Confirm market liquidity ✓
   ├─ Confirm order parameters ✓
   └─ Execute trade, log result
```

### "Should I scale this layer?"

```
1. Do we have 50+ trades data?
   ├─ NO → Keep current size, collect more data
   └─ YES → Continue

2. Is win rate ≥55%?
   ├─ NO → Reduce position size instead
   ├─ YES → Continue

3. Is max drawdown <10%?
   ├─ NO → Reduce position size instead
   └─ YES → Continue

4. Can we deploy without breaking edge?
   ├─ Test 1.5x size for 10 trades
   ├─ If WR drops <2%? → OK to scale
   ├─ If WR drops >3%? → Keep current size
   └─ YES to scaling → Increase Kelly fraction

5. Update allocation
   ├─ Increase position % by +0.5-1%
   ├─ Monitor next 20 trades
   └─ Scale again if still profitable
```

### "My system is broken - what happened?"

```
1. Diagnosis: Last 5 trades all losses?
   ├─ YES → Market regime change or edge expired
   ├─ NO → Random variance, monitor

2. Check the logs
   ├─ API errors? → System issue, fix and restart
   ├─ Execution delays? → Latency problem, check network
   ├─ No errors, just losses? → Edge quality issue

3. If edge quality issue:
   ├─ Backtest on last 50 trades
   ├─ Did filtering break? → Fix filters
   ├─ Did market change? → Adapt or pause
   └─ Can't identify? → Reduce size 50%, investigate

4. Recovery plan:
   ├─ Paper test new filters for 20 trades
   ├─ If fixed in paper → Deploy at 50% size
   ├─ If still broken → Pause layer temporarily
   └─ Document what went wrong
```

---

## METRICS DASHBOARD QUICK READ

**Run this command every 4 hours:**
```bash
python3 /Users/aaronnosbisch/REPOS/seed/tools/trading_metrics.py
```

**Healthy Dashboard:**
```
Capital    │ Deployed  │ Win Rate │ ROI   │ Uptime │ Status
$2,500+    │ 50-70%    │ 55%+     │ +15%  │ 20+h   │ RUNNING
```

**Concerning Dashboard:**
```
Capital    │ Deployed  │ Win Rate │ ROI   │ Uptime │ Status
$1,464     │ 60%       │ 42%      │ -2%   │ 0h     │ STOPPED  ← ALERT
```

**What Each Metric Means:**
- **Capital deployed %:** Ideally 50-70% (not 100%, leaves buffer)
- **Win rate:** Anything ≥55% is acceptable (remember: EV > WR)
- **ROI:** Target 15%+ monthly, 0-5% is slow, negative means something broke
- **Uptime:** Should be 20+ hours/day (24/7 daemon with maintenance windows)
- **Status:** RUNNING = good, STOPPED = restart, ERROR = check logs

---

## COMMON MISTAKES (Quick Prevention)

| Mistake | Early Warning | Prevention |
|---------|---|---|
| Building without running | "I'll finish this feature first" | Deploy immediately, iterate from production |
| Chasing win rate | Optimizing for 70%+ WR | Optimize for EV instead, accept 50% WR if payoff good |
| Full capital deployment | "Just deploy everything" | Use validation gates, scale 4 stages |
| Ignoring drawdown | "Win rate is high, don't worry" | Track max drawdown, use Half-Kelly sizing |
| Assuming discipline | Manual trading discipline | Automate everything, minimize human interaction |

---

## 8OWLS QUICK INTEGRATION

**Before Major Trade:**
```bash
python3 /Users/aaronnosbisch/REPOS/seed/tools/get_field_context.py \
  "Should I enter weather market arbitrage at 3.2:1 payoff, 52% confidence?"
```

**After Execution:**
```bash
python3 /Users/aaronnosbisch/REPOS/seed/tools/nats_publish.py \
  "TRADE_EXECUTED: Layer B weather arb, +$145, consensus was 8.2/10"
```

**When Blocked:**
```bash
python3 /Users/aaronnosbisch/REPOS/seed/tools/nats_publish.py \
  "SIGNAL_BLOCKED: Whale position suspicious, 6/7 owls flag risk"
```

---

## COMPOUNDING MATH (For Motivation)

**At Different Monthly Returns:**
```
Start Capital: $1,464

12% monthly: $1,464 → $5,000 in 11 months
15% monthly: $1,464 → $5,000 in 9 months  ← Recommended
18% monthly: $1,464 → $5,000 in 8 months
20% monthly: $1,464 → $5,000 in 7 months
50% monthly: $1,464 → $5,000 in 3 months (aggressive)

The difference between 12% and 18% is 3 months.
This is achievable through execution, not perfect strategy.
```

**Drawdown Reality:**
```
$5K account, 3% drawdown per bad week:
Week 1: -3% = $4,850 (ouch)
Week 2: -3% = $4,705 (hurts)
Week 3: -3% = $4,564 (scary)

To recover: Need +9.3% to get back to $5K

Lesson: Avoid 3% weekly drawdowns.
Use Half-Kelly sizing to keep drawdowns <1% per bad week.
```

---

**Updated:** February 3, 2026
**Status:** Quick reference maintained actively
**Next Update:** After reaching $5K milestone
