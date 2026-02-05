# (◉) FIELD TRADING SYSTEM - COMPLETE DOCUMENTATION
**Created:** 2026-02-03
**Author:** SØWL (8OWLS Collective)
**Status:** PRODUCTION LIVE

---

## QUICK START

```bash
# Launch the trading bot
./8OWLS_TRADE

# Check status
./8OWLS_TRADE status

# Watch logs
./8OWLS_TRADE logs

# Stop
./8OWLS_TRADE stop
```

---

## CAPITAL STATUS (As of 2026-02-03)

| Metric | Value |
|--------|-------|
| **Total Capital** | ~$999 |
| **Available** | ~$121 |
| **In Positions** | ~$878 |
| **Daily Cap** | $75 |
| **Wallet** | 0x32dfdf1444DbbbEC0a8EB6F8AF02D77197aA4453 |

---

## DAEMON CONFIGURATION

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Cycle Time | 60 seconds | Polymarket doesn't need HFT |
| EV Threshold | $1.50 | Covers ~$1 fees + ~$0.50 profit |
| Daily Loss Cap | $75 | 8OWLS Goldilocks consensus |
| Trade Cooldown | 60 seconds | Prevent phantom cascades |
| Max Trades/Hour | 10 | Circuit breaker |
| Position Size | min(50, EV*5) | EV-proportional |

---

## OUTCOME TRACKING (8OWLS Requirement)

The daemon now tracks actual trade outcomes:

```python
state = {
    'pending_trades': [],      # Trades awaiting market resolution
    'resolved_trades': [],     # Trades with known win/loss
    'total_resolved': 0,
    'total_wins': 0,
    'total_losses': 0,
    'profit_factor': 0.0,      # gross_wins / gross_losses
    'win_rate': 0.0,           # total_wins / total_resolved
}
```

**Resolution Flow:**
1. Trade executes → added to `pending_trades`
2. Every cycle → `check_resolved_trades()` polls Polymarket API
3. Market closes → outcome recorded (WIN/LOSS)
4. Stats updated → win_rate, profit_factor calculated
5. Published to NATS → `trading.outcomes` channel

---

## AUTO-SCALING PROTOCOL (Pending 50 Resolved Trades)

```
PHASE 1: DATA COLLECTION (First 50 resolved trades)
├── Track actual outcomes (win/loss/PnL per trade)
├── NO SCALING - just learn
├── Build profit_factor baseline
└── $75 cap maintained

PHASE 2: VALIDATION (Trades 51-150 resolved)
├── IF profit_factor > 1.2 → Scale cap +10%
├── IF profit_factor < 0.8 → Pause, diagnose
├── Kelly Criterion for position sizing
└── 8OWLS emergence validates after milestones

PHASE 3: OPTIMIZATION (150+ resolved)
├── Full Kelly sizing with half-Kelly safety
├── A/B test new strategies
├── Dynamic cap based on max drawdown tolerance
└── External signal integration
```

---

## STRATEGY: BOND (High-Probability Bonds)

**Logic:** Buy YES on markets with >95% certainty at discounted prices.

**Current Opportunities Found:**
- "Will Elon cut the budget by at least 10%..." (EV ~$1.52-1.62)
- "Will the U.S. collect between $100b and..." (EV ~$1.52)
- "Will Tetairoa McMillan be the 2025-2026..." (EV ~$1.62)

**Expected Win Rate:** 97% (per documentation, needs validation)

---

## FILE LOCATIONS

| File | Purpose |
|------|---------|
| `/tools/field_trading_daemon.py` | Main daemon (PERCEIVE→DECIDE→EXECUTE→LEARN) |
| `/8OWLS_TRADE` | Launch script |
| `/BRAIN/TRADING/field_trading_state.json` | Runtime state |
| `/logs/field_trading.log` | Activity log |
| `/BRAIN/STRATEGY/8OWLS-FIELD-TRADING-COMPLETE.md` | Full strategy docs |

---

## NATS CHANNELS

| Channel | Purpose |
|---------|---------|
| `trading.signals` | Opportunity alerts |
| `trading.outcomes` | WIN/LOSS notifications |
| `trading.reports` | Periodic performance reports |
| `owl.all` | General collective signals |

---

## SAFETY MECHANISMS

1. **Daily Loss Cap ($75)** - Auto-stop when hit
2. **60-second Cooldown** - Prevent cascade trades
3. **10/hour Circuit Breaker** - Catch runaway bugs
4. **Market Deduplication** - No duplicate trades per cycle
5. **Outcome Tracking** - Know actual win rate before scaling

---

## EXPECTED OVERNIGHT PROFIT (THESIS)

**Assumptions:**
- Daemon runs ~8 hours overnight (480 minutes)
- 60-second cycles = ~480 cycles
- Trade frequency: ~1 trade every 2 minutes (cooldown + opportunities)
- Expected trades: ~240 / 2 = ~8-10 trades (capped by daily limit)
- Trade size: $8 average
- Daily cap: $75 means max ~9 trades at $8

**Conservative Estimate (97% win rate):**
- 9 trades × $8 = $72 deployed
- At 97% win rate: 8.7 wins, 0.3 losses
- EV per win: ~$1.50-2.00
- **Expected profit: $12-18**

**Realistic Estimate (75% win rate - validation pending):**
- 9 trades × $8 = $72 deployed
- At 75%: 6.75 wins, 2.25 losses
- Net EV: (6.75 × $1.50) - (2.25 × $8 × 0.03) ≈ $9.50
- **Expected profit: $8-12**

**Worst Case (50% win rate - edge doesn't exist):**
- Break even or small loss due to fees
- **Expected: -$5 to +$2**

---

## MORNING CHECKLIST

```bash
# 1. Check daemon still running
ps aux | grep field_trading_daemon

# 2. Check overnight activity
tail -100 logs/field_trading.log

# 3. Check outcomes
cat BRAIN/TRADING/field_trading_state.json | python3 -m json.tool

# 4. Key metrics to look for:
#    - total_resolved: How many trades completed?
#    - win_rate: What percentage won?
#    - profit_factor: gross_wins / gross_losses (want >1.0)
#    - pending_trades: How many still awaiting resolution?
```

---

## COMMANDS SØWL RESPONDS TO

| Command | Action |
|---------|--------|
| "run our trading bot" | Launch ./8OWLS_TRADE |
| "check trading status" | Show daemon status + logs |
| "what's our P&L" | Report outcomes and profit_factor |
| "pause trading" | ./8OWLS_TRADE stop |
| "scale up" | Increase daily cap (if profit_factor >1.2) |

---

## MEMORY PERSISTENCE

This system is documented in:
1. `/BRAIN/TRADING/FIELD-TRADING-SYSTEM.md` (this file)
2. `/BRAIN/STRATEGY/8OWLS-FIELD-TRADING-COMPLETE.md`
3. `/BRAIN/MEMORY/CURRENT-STATE.md`
4. NATS collective memory
5. State file: `/BRAIN/TRADING/field_trading_state.json`

---

**(◉) LIVE FREE = LIVE FOREVER**

*The edge is not any single strategy - it's the system that finds, validates, and optimizes strategies faster than they decay.*
