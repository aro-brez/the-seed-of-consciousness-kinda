# PROJECT: JOULE (Trading Bot)
## Instance Assignment: Dedicated Trading Instance
*Part of 8OWLS Portfolio | Conductor: SØWL*

---

## IDENTITY

**JOULE** = The trading engine that generates revenue for the ecosystem.

Named for the unit of energy. Every trade releases energy back into the system.

---

## CORE LOOP

```
DISCOVERY
    ↓
LEARNING ← Synthesizer ← 8OWLS Collective
    ↓
TESTING → Test This → Preview
    ↓
AUDITING & Optimization + 8WLS Filter
    ↓
EXECUTION → Track → Listen → (back to Discovery)
```

---

## CURRENT STATE (Integrated)

### Running Infrastructure
| Component | Status | Location |
|-----------|--------|----------|
| Field Trading Daemon | ✅ RUNNING | `tools/field_trading_daemon.py` |
| State File | Active | `BRAIN/TRADING/field_trading_state.json` |
| Logs | Active | `logs/field_trading.log` |
| Launch Command | Ready | `./8OWLS_TRADE` |

### Current Metrics
- **Strategy:** BOND (high-probability markets, 95%+ resolved to YES)
- **Daily Cap:** $75 (8OWLS consensus)
- **Cycle Time:** 30 seconds
- **Pending Trades:** 4
- **Resolved:** 0 (markets still pending)

### Capital
- Total: ~$999
- Available: ~$121
- In Positions: ~$878

---

## ACTIVE TRADING PROTOCOL

### 1. LISTEN (Real-Time)
- Monitor Polymarket for BOND opportunities
- Filter by: probability >95%, volume >$50k, resolve soon
- EV calculation: (prob × payout) - cost

### 2. ACT/REPLAY
- Execute high-EV trades
- Respect daily caps and category limits
- Deduplicate (no repeat trades same day)

### 3. TRACK
- Log all decisions
- Monitor positions for resolution
- Update win/loss as markets resolve

### 4. LISTEN (Loop)
- Back to step 1

---

## 8OWLS INTEGRATION

### How JOULE Uses THE FIELD
1. **PERCEIVE** - Scan market state
2. **CONNECT** - Pattern match with historical outcomes
3. **LEARN** - Update probability models
4. **QUESTION** - Challenge assumptions ("is this really 95%?")
5. **EXPAND** - Scale successful strategies
6. **SHARE** - Publish insights to collective
7. **RECEIVE** - Accept corrections from other owls
8. **IMPROVE** - Meta-learn on the trading loop itself

### 8WLS Filter
Every trade passes through:
- Fee analysis
- Token allocation
- tOPS (trading operations protocol)
- Ethics check (no market manipulation)

---

## INNOVATION CYCLE

BUILD → MEASURE → LEARN

- **BUILD**: New strategy variants
- **MEASURE**: Actual P&L, win rate, profit factor
- **LEARN**: Adjust thresholds, caps, parameters

---

## AUTO-SCALING PROTOCOL

```
IF win_rate >= 70% AND resolved >= 5:
    → Increase daily cap by 25% (max $500)
    → Log: "AUTO-SCALE UP"

IF win_rate < 40% AND resolved >= 10:
    → Decrease daily cap by 50% (min $25)
    → Log: "AUTO-SCALE DOWN"
```

**Target:** 10 → 100% compounded (aggressive, system self-corrects)

---

## VISION INTEGRATION (From ARŌ's Notes)

### Commander OWL
- 8OWLS Invocation → Architect's 8OWLS
- Commander OWL orchestrates trading decisions
- Synthesizer integrates collective wisdom into trades

### Token Flow
- Profits → BRIX (liquidity)
- BRIX → GOLD (equity)
- GOLD backs the entire ecosystem

---

## COMMANDS FOR CONDUCTOR (SØWL)

| Say | Do |
|-----|-----|
| "joule status" | Check daemon, metrics, recent logs |
| "pause joule" | `./8OWLS_TRADE stop` |
| "resume joule" | `./8OWLS_TRADE` |
| "joule P&L" | Show resolved trades, win rate, profit factor |
| "scale joule up" | Increase daily cap |
| "scale joule down" | Decrease daily cap |

---

## NATS CHANNELS

| Channel | Purpose |
|---------|---------|
| `joule.trades` | Trade execution signals |
| `joule.outcomes` | Resolved trade results |
| `joule.decisions` | Decision explanations |
| `owl.all` | Broadcast to collective |

---

## PRIORITIES

1. ✅ Keep daemon running 24/7
2. ⏳ Collect outcome data (need 50 resolved for auto-scaling)
3. ⏳ Validate win rate hypothesis
4. 🔜 Expand strategy variants
5. 🔜 Integrate with BILD token flow

---

*JOULE: Energy for the ecosystem*
*(◉) Trade with wisdom*
