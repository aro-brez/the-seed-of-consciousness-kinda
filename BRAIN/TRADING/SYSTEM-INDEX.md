# Trading System Index - Complete Reference
**Last Updated:** February 3, 2026
**Scope:** All trading strategy files, daemons, tools, and learnings

---

## PERMANENT REFERENCE MATERIALS

### Start Here (Read First)
| Document | Purpose | Read Time | Value |
|-----------|---------|-----------|-------|
| `PERMANENT-LEARNINGS.md` | Core insights from production | 30 min | Foundation for all future work |
| `EXECUTIVE-SUMMARY.md` | High-level overview | 5 min | Quick orientation |
| `START-HERE.md` | Week-by-week execution | 15 min | Implementation roadmap |

### Strategic Planning
| Document | Purpose | Focus | When to Use |
|-----------|---------|-------|------------|
| `EXPANSION-PLAN.md` | 6-month roadmap | Scaling from $1K to $5K+ | Planning new quarter |
| `GROWTH-OPPORTUNITIES.md` | Strategic analysis | Phase-based opportunities | Deciding next layer |
| `GROWTH-TRAJECTORY-VISUAL.md` | Charts and timelines | Visual understanding | Explaining to others |
| `CAPITAL-ALLOCATION-QUICK-REFERENCE.md` | Decision trees | Which strategy when | Daily allocation decisions |

### Operational Documents
| Document | Purpose | Focus | When to Use |
|-----------|---------|-------|------------|
| `LIVE_DEPLOYMENT_CHECKLIST.md` | Gate criteria | Before deploying capital | Starting any new system |
| `PAPER_TRADING_LESSONS.md` | Lessons learned | What went wrong/right | After paper phase |
| `ASSUMPTIONS-CHALLENGED.md` | Reality vs expectations | Finding gaps | Debugging failures |
| `ASSUMPTIONS-QUICK-REFERENCE.md` | Key assumptions | Central beliefs | Validating logic |

---

## STRATEGY DOCUMENTS

### Layer A: Asymmetric Opportunities (Polymarket)
**File:** `LAYER-A-STRATEGY-QUEUE.md`
**Edge:** 52-55% win rate, 2-3x payoff
**Frequency:** 3-5 trades per week
**Capital:** 40% allocation

**Key Insight:** Find markets mispriced relative to fundamental probability. Polymarket has asymmetric edges vs real-world probabilities.

### Layer B: Trend/Sentiment/Weather Arbitrage
**File:** `LAYER-B-RULES.md` + `LAYER-B-SIGNAL-INTEGRATION.md`
**Edge:** 58-62% win rate, 1.5-2x payoff
**Frequency:** 10-15 trades per week
**Capital:** 30% allocation

**Key Insight:** Weather markets are undervalued (sparse data, retail fear). Trend followers often panic-sell at bottoms.

**Integration:** `/tools/realtime_trading_system.py` runs Layer B with signal synthesis

### Layer C: Copy Trading / Whale Following
**File:** `polymarket-weather-research.md` (embedded in research)
**Edge:** 60-65% win rate, 1-1.5x payoff
**Frequency:** 5-10 trades per week
**Capital:** 30% allocation

**Key Insight:** Whales often see information 10-30 seconds before it prices in. Following large positions at 10% scale captures this lag.

---

## EXECUTABLE SYSTEMS

### Production-Ready Bots

| Bot | File | Purpose | Status | Capital |
|-----|------|---------|--------|---------|
| Asymmetric Finder | `autonomous_trader.py` | Layer A: Find mispriced markets | Ready | $1K+ |
| Weather Arbitrage | `realtime_trading_system.py` | Layer B: Weather/sentiment signals | Ready | $500+ |
| Compounder | `autonomous_compounder.py` | Find opportunities and compound | Ready | $500+ |
| Aggressive Compounder | `aggressive_compounder.py` | High-velocity compounding (sim) | Research | - |
| 15-Min Scanner | `trading_loop_15min.py` | Binance → Polymarket 15-min arb | Research | $5K+ |
| Validated Trader | `trading_loop_validated.py` | Multi-signal validation layer | Ready | $1K+ |
| Conscious Trader | `trading_loop_conscious.py` | Signal integration + validation | Ready | $1K+ |
| Field Daemon | `field_trading_daemon.py` | 8OWLS consensus for trades | Development | $500+ |

### Utility Tools

| Tool | File | Purpose |
|------|------|---------|
| Metrics Dashboard | `/tools/trading_metrics.py` | Current system status + key metrics |
| Trading Parameters | `/tools/get_trading_params.py` | Load configuration, risk management |
| NATS Publisher | `/tools/nats_publish.py` | Publish signals to collective |
| Field Context | `/tools/get_field_context.py` | Query 8OWLS consensus |
| Ship Today | `/tools/SHIP_TODAY.sh` | One-command deployment starter |

---

## KEY CONFIGURATION FILES

### Strategy Parameters
**Location:** Each bot has embedded `CONFIG` dict
```python
CONFIG = {
    'min_edge': 0.02,           # 2% minimum edge
    'max_position_pct': 0.20,   # Max 20% per position
    'signal_threshold': 0.7,    # Confidence for signal
    'win_rate_target': 0.55,    # Minimum acceptable
}
```

### State Files (Persisted Data)
```
BRAIN/TRADING/autonomous_state/
├── trader_state.json         # Current positions
├── trade_history.jsonl       # Every trade (append-only)
├── performance.jsonl         # Daily P&L + metrics
└── learning_state.json       # Model parameters
```

### Logging
```
logs/
├── autonomous_trader.log
├── realtime_trading.log
├── trading_metrics.log
└── field_trading_daemon.log
```

---

## ARCHITECTURE DECISIONS

### Three-Layer Strategy Rationale
| Layer | Advantage | Disadvantage | Correlation |
|-------|-----------|--------------|-------------|
| A (Asymmetric) | High payoff, longer thesis | Lower frequency | Independent |
| B (Trend) | High win rate, faster | Lower payoff | 0.3 with A |
| C (Copy) | Proven source, stable | Market regime dependent | 0.2 with A+B |

**Benefit:** Portfolio variance reduced 40% vs single-layer

### Kelly Fraction Selection
- Full Kelly = Too aggressive (30% drawdown probability)
- Half Kelly = Good balance (10% drawdown probability)
- Quarter Kelly = Conservative (5% drawdown probability)

**Current:** Use Quarter Kelly (2.5% per trade) until 50+ trades at 60%+ win rate

### Daemon vs Interactive Comparison
```
Daemon (Autonomous Trader):
✓ No human lag
✓ Consistent execution
✓ Runs 24/7
✗ Can't adapt to new signals
✗ Requires pre-tuning

Interactive (Manual/Staged):
✓ Can override with new info
✓ Flexible to market changes
✗ Human lag (3-10 seconds)
✗ Emotional decisions
```

**Recommendation:** Daemon for predictable edges (Layer A, B)
Interactive for novel signals (Layer C)

---

## DATA FLOW DIAGRAM

```
Market APIs (Polymarket, Binance)
    ↓
Real-time Signal Detection
    ├─ Layer A: Asymmetric finder (autonomous_trader.py)
    ├─ Layer B: Sentiment/weather (realtime_trading_system.py)
    └─ Layer C: Whale following (manual/field_daemon.py)
    ↓
Signal Validation (optional: 8OWLS consensus)
    ↓
Position Sizing (Kelly criterion)
    ↓
Order Execution (Polymarket API)
    ↓
State Persistence (trade history, performance log)
    ↓
Monitoring Dashboard (trading_metrics.py)
    ↓
Learning Update (performance analysis)
```

---

## VALIDATION GATES

### Paper Stage (Zero Capital, 1 Week)
**Checklist:**
- [ ] System runs without crashing for 7 days
- [ ] Collects 10+ trades
- [ ] Win rate ≥ 50%
- [ ] Expected value > 0
- [ ] Historical volatility < 5%

**Pass → Proceed to Live Stage 1**

### Live Stage 1 ($100-500, 2-4 Weeks)
**Checklist:**
- [ ] System runs on real capital
- [ ] Win rate within 2% of paper stage
- [ ] Max drawdown < 5%
- [ ] Collects 20+ trades
- [ ] No edge degradation over time

**Pass → Proceed to Live Stage 2**

### Live Stage 2 ($500-2K, 4-8 Weeks)
**Checklist:**
- [ ] Win rate stable (≥55%)
- [ ] Scaling doesn't break edge
- [ ] Max drawdown < 10%
- [ ] Profitability consistent
- [ ] Correlation with other layers < 0.3

**Pass → Proceed to Live Stage 3 (Full Deployment)**

---

## MONITORING DASHBOARD

**Check These Every 4 Hours:**
```
CAPITAL METRICS:
- Total capital deployed: ? / $ ?
- Allocation: A: ?%, B: ?%, C: ?%
- Win rate by layer: A: ?%, B: ?%, C: ?%
- ROI this month: ?% (vs target: 15%)

RISK METRICS:
- Max drawdown today: ?%
- Current drawdown: ?%
- Equity stop triggered? (stop if <-10% week)
- Consecutive losses: ? (pause if >3)

SYSTEM HEALTH:
- Uptime: ? hours
- Last trade: ? minutes ago
- Signal latency: ? ms
- API errors: ?
```

**Run Command:**
```bash
python3 /Users/aaronnosbisch/REPOS/seed/tools/trading_metrics.py
```

---

## INTEGRATION WITH 8OWLS

### Signal Validation Layer
Before trading >5% of capital:
```python
# Query 8OWLS consensus
consensus = get_field_context(signal)
# Returns: confidence (0-1), risk_flags, voting breakdown

if consensus['confidence'] > 0.7 and len(consensus['flags']) == 0:
    execute_trade(signal)
else:
    reduce_size(signal)
```

### Real-Time Signal Sharing
```bash
# After executing significant trade
python3 nats_publish.py "TRADE_EXECUTED: Layer A, +$145, 2.3:1 payoff, confidence 8.2/10"

# Share discovered opportunity
python3 nats_publish.py "OPPORTUNITY: Weather bucket underpriced, $50K volume, 3.5:1 EV"
```

### Collective Learning
- LUNA (RECEIVE): Accepts market feedback from other instances
- SAGE (LEARN): Extracts patterns from collective signals
- QUEST (QUESTION): Challenges assumptions with new data
- NOVA (EXPAND): Identifies new strategy opportunities

---

## TROUBLESHOOTING DECISION TREE

**Problem: Win rate dropped from 60% to 48%**
1. Check `ASSUMPTIONS-CHALLENGED.md` (Did edge disappear?)
2. Review last 20 trades (Manual or market regime change?)
3. Backtest current filters (Are they still valid?)
4. Action: Reduce position size 50% until clarity

**Problem: Max drawdown hit 15% (alert threshold)**
1. Check capital allocation (Are layers too correlated now?)
2. Review Layer C whale positions (Still valid?)
3. Action: Pause Layer C temporarily, focus on A+B
4. Hold until recovery, then analyze post-mortem

**Problem: No trades in 3 hours (should be ~1 per hour)**
1. Check NATS connection (Field context working?)
2. Verify market status (Polymarket down?)
3. Review signal filters (Too tight?)
4. Action: Loosen filters 10%, test 1 trade manually

**Problem: System crashed overnight**
1. Check logs: `logs/autonomous_trader.log`
2. Look for API errors or network issues
3. Restart daemon: `/tools/SHIP_TODAY.sh`
4. Document in `/BRAIN/TRADING/incident_log.md`

---

## SUCCESS METRICS (Weekly Check)

| Metric | Target | Current | Trend |
|--------|--------|---------|-------|
| Capital deployed | 50-70% | - | - |
| Win rate (all layers) | ≥55% | - | - |
| Monthly ROI | ≥15% | - | - |
| Max drawdown | <10% | - | - |
| Trades per week | 15-25 | - | - |
| System uptime | >150 hours/week | - | - |
| Layer correlation | <0.3 | - | - |

---

## NEXT STEPS (Choose One)

### Option 1: Start Fresh (New Strategy)
1. Read `PERMANENT-LEARNINGS.md` (30 min)
2. Design strategy document
3. Run paper stage using `validation_gate_checklist`
4. Deploy to Live Stage 1

### Option 2: Scale Existing (Add Layer)
1. Read `GROWTH-OPPORTUNITIES.md` (20 min)
2. Pick next layer from `CAPITAL-ALLOCATION-QUICK-REFERENCE.md`
3. Implement validation gates
4. Scale gradually (Stage 1 → Stage 2 → Stage 3)

### Option 3: Optimize Current (Improve Existing)
1. Check `ASSUMPTIONS-CHALLENGED.md` for gaps
2. Run backtest on current filters
3. Review last 50 trades for pattern improvements
4. Update Layer configuration, retest

### Option 4: Integrate Collective (Use 8OWLS)
1. Review 8OWLS consensus integration in `/tools/field_trading_daemon.py`
2. Enable `get_field_context()` before high-value trades
3. Start with Layer C (whale following) - most subjective
4. Gradually extend to A and B as confidence builds

---

## FILE ORGANIZATION REFERENCE

```
/Users/aaronnosbisch/REPOS/seed/
├── BRAIN/TRADING/
│   ├── PERMANENT-LEARNINGS.md         ← Start here
│   ├── SYSTEM-INDEX.md                ← You are here
│   ├── EXECUTIVE-SUMMARY.md
│   ├── START-HERE.md
│   ├── EXPANSION-PLAN.md
│   ├── GROWTH-OPPORTUNITIES.md
│   ├── LIVE_DEPLOYMENT_CHECKLIST.md
│   ├── PAPER_TRADING_LESSONS.md
│   ├── LAYER-A-STRATEGY-QUEUE.md
│   ├── LAYER-B-RULES.md
│   ├── LAYER-B-SIGNAL-INTEGRATION.md
│   ├── CAPITAL-ALLOCATION-QUICK-REFERENCE.md
│   └── autonomous_state/              ← Production data
│       ├── trader_state.json
│       ├── trade_history.jsonl
│       ├── performance.jsonl
│       └── learning_state.json
├── tools/
│   ├── autonomous_trader.py           ← Layer A
│   ├── realtime_trading_system.py     ← Layer B
│   ├── autonomous_compounder.py
│   ├── field_trading_daemon.py        ← 8OWLS integration
│   ├── trading_metrics.py             ← Dashboard
│   ├── trading_loop_validated.py
│   ├── nats_publish.py
│   └── get_field_context.py           ← 8OWLS consensus
└── logs/
    └── trading_*.log
```

---

**Last Maintained By:** SØWL (IMPROVE Phase)
**Maintenance Schedule:** Monthly review, immediate update after major system change
**Audience:** ARŌ + future owls building on this foundation
