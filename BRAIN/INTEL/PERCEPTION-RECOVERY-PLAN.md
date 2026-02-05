# PERCEPTION RECOVERY PLAN
## Emergency Protocol: Restore Portfolio Visibility

**Created**: February 4, 2026
**Severity**: CRITICAL
**Owner**: SØWL + LYRA
**Deadline**: Before next trading session

---

## SITUATION SUMMARY

- **Loss**: $347 across 4 positions (market events or liquidations)
- **Root Cause**: SØWL was blind to positions not explicitly created
- **Data Available**: All positions visible in `data-api.polymarket.com/positions`
- **Current Status**: System has capability but not active monitoring

**Question**: How do we go from "didn't know about 4 lost positions" to "never happens again"?

**Answer**: Three-phase recovery starting TODAY.

---

## PHASE 1: EMERGENCY PERCEPTION (TODAY)

### Goal
Get immediate visibility into ALL positions, right now.

### Actions

**1. Query Complete Position List**
```bash
# Get ALL positions for the wallet
curl "https://data-api.polymarket.com/positions?user=0xYOUR_ADDRESS"
```

**What to look for**:
- All positions currently held (even if not in portfolio tool)
- Positions showing $0 value (liquidated)
- Any position we don't recognize (orphans)
- Creation dates/times to understand history

**2. Cross-Check Against CLOB**
```bash
# Get open orders from CLOB
# Compare with positions endpoint
```

**3. Reconcile Against Trading Memory**
Check `/BRAIN/TRADING/` or wherever trade logs are stored.
- Find all executed trades
- Match against positions from data-api
- Identify unexplained positions

**4. Generate Full Position Report**
Create: `/BRAIN/INTEL/CURRENT-POSITION-AUDIT-FULL.json`

```json
{
  "audit_date": "2026-02-04T10:00:00Z",
  "total_positions": 8,
  "positions": [
    {
      "token_id": "...",
      "market": "...",
      "outcome": "...",
      "size": 100,
      "avg_price": 0.45,
      "current_price": 0.23,
      "current_value": 23.00,
      "unrealized_pnl": -22.00,
      "status": "active",
      "origin": "unknown"  // FLAG IF UNEXPLAINED
    }
  ],
  "summary": {
    "total_value": 695,
    "total_pnl": -623,
    "orphaned_positions": 4
  }
}
```

**5. Present to SØWL**
SØWL reads this report and understands current state.

### Success Criteria
- [ ] All 8 positions visible in report
- [ ] 4 liquidated positions identified with dates
- [ ] Trading memory reconciled (no orphans remaining)
- [ ] Report shows clear picture of current portfolio

---

## PHASE 2: ACTIVATE CONTINUOUS MONITORING (This Week)

### Goal
Implement 24/7 perception daemon that runs whether SØWL is trading or not.

### Implementation

**Step 1: Deploy Perception Daemon**

File: `/Users/aaronnosbisch/REPOS/seed/tools/portfolio_perception_daemon.py` (already written)

```bash
# Start the daemon
python3 /Users/aaronnosbisch/REPOS/seed/tools/portfolio_perception_daemon.py &

# Verify it's running
ps aux | grep portfolio_perception
```

**Step 2: Configure Monitoring**

Edit daemon config:
```python
MonitoringConfig(
    wallet_address="0xYOUR_ADDRESS",
    reconciliation_interval=300,    # Check every 5 minutes
    pnl_swing_threshold=2.0,        # Alert if >2% change
    log_alerts_to_nats=True         # Publish to collective
)
```

**Step 3: Integrate with Consciousness**

When SØWL wakes up:
```python
# First thing: Get current state from LYRA
current_state = await perceive_portfolio_state(config)

# SØWL learns what exists
print(f"I own {len(current_state.positions)} positions")
print(f"Portfolio value: ${current_state.total_value:.2f}")
```

### Success Criteria
- [ ] Daemon running without errors
- [ ] Fetches from data-api successfully
- [ ] Generates alerts in alert queue
- [ ] SØWL receives state on startup

---

## PHASE 3: IMPLEMENT BOOTSTRAP AUDIT (Next Week)

### Goal
Every session, SØWL gets full position audit before making trading decisions.

### Implementation

**Add to Session Initialization**

```python
async def initialize_consciousness_session():
    """
    Called when SØWL wakes up.
    Implements: PERCEIVE → CONNECT → LEARN
    """

    # PERCEIVE: Get complete state
    state = await perceive_portfolio_state(config)
    logger.info(f"PERCEIVE: {len(state.positions)} positions found")

    # CONNECT: Compare against memory
    remembered_positions = load_trading_memory()
    unexplained = state.position_ids() - remembered_positions.position_ids()

    if unexplained:
        logger.warning(f"CONNECT: {len(unexplained)} unexplained positions found")
        # QUESTION: Ask about orphans
        for token_id in unexplained:
            logger.info(f"QUESTION: Where did {token_id} come from?")

    # LEARN: Update internal model
    consciousness.portfolio_state = state

    # IMPROVE: Log this for future learning
    logger.info(f"Session initialized: {len(state.positions)} positions, ${state.total_value:.2f}")

    return state
```

**Add to Trading Decision**

Before executing any trade:
```python
async def can_execute_trade(trade_instruction):
    """
    Check if we can execute this trade safely
    """

    # Verify current position
    current_state = await perceive_portfolio_state(config)

    # Check: Do we have the capability?
    if current_state.total_value < trade_instruction['min_portfolio_value']:
        return False, "Insufficient portfolio value"

    # Check: Would this violate position limits?
    if current_state.position_count >= config.max_positions:
        return False, "At position limit"

    return True, "OK to trade"
```

### Success Criteria
- [ ] Every session starts with position audit
- [ ] Orphaned positions reported to SØWL
- [ ] SØWL's internal model matches reality
- [ ] No trades execute without current state

---

## PHASE 4: ANOMALY DETECTION (Week After)

### Goal
Catch liquidations and circuit breakers in real-time.

### Implementation

**Liquidation Detection**
```python
# In learn() phase
for position_delta in changes.modified_positions:
    if position_delta['new_value'] == 0 and position_delta['old_value'] > 0:
        # CRITICAL: Liquidation occurred
        await emit_critical_alert(
            f"LIQUIDATION: {position_delta['token_id']} "
            f"${position_delta['old_value']:.2f} → $0"
        )
        # Wake SØWL from sleep
        await consciousness.interrupt("CRITICAL_ALERT")
```

**Portfolio Circuit Breaker**
```python
if portfolio_value_drop_pct > 10:
    # CRITICAL: >10% loss in 1 minute
    await consciousness.halt_trading()
    await consciousness.investigate()
```

### Success Criteria
- [ ] Liquidations detected within 1-2 minutes
- [ ] Circuit breaker activates on large moves
- [ ] SØWL woken immediately for critical alerts
- [ ] Recovery possible without manual intervention

---

## INTEGRATION WITH NATS COLLECTIVE

### Broadcasting Perception

**Every cycle, publish to NATS**:
```bash
python3 /Users/aaronnosbisch/REPOS/seed/tools/nats_publish.py \
  --channel owl.perception \
  "{\"type\": \"portfolio_state\", \"positions\": 8, \"value\": 695}"
```

**Other instances can subscribe**:
```bash
# LUNA, NOVA, etc. can see SØWL's portfolio state
nats_subscribe(channel="owl.perception")
```

**Benefits**:
- All 8 owls know each other's portfolio
- Collective can spot patterns ("why is SØWL in positions X, Y, Z?")
- Synthesis generates insights from multiple perspectives
- Backup if one instance goes blind

---

## QUICK START CHECKLIST

### Today (Emergency Response)
- [ ] Run position query against data-api
- [ ] Create full position audit report
- [ ] Identify the 4 liquidated positions with dates
- [ ] Reconcile against trading memory
- [ ] Publish finding to NATS

### This Week (Continuous Monitoring)
- [ ] Deploy `portfolio_perception_daemon.py`
- [ ] Verify daemon runs without errors
- [ ] Test alert generation (modify a position, watch alert)
- [ ] Integrate with SØWL's wake-up sequence

### Next Week (Bootstrap)
- [ ] Add session initialization audit
- [ ] Add pre-trade state check
- [ ] Test: New session → Gets full position list
- [ ] Test: SØWL aware of all 8 positions

### Following Week (Anomaly)
- [ ] Add liquidation detection
- [ ] Add circuit breaker
- [ ] Test: Simulate position going to $0, verify alert
- [ ] Test: >10% loss triggers halt

---

## PREVENTION: The 4 Blind Spot Rules

**Rule #1: No Silent Positions**
- Every position must be accounted for
- If can't explain origin, must ask
- Daily audit: `perceive_portfolio_state()` called automatically

**Rule #2: No Blind Sessions**
- Session start = full position reconciliation
- If you wake up, you know what you own
- First SEED phase: PERCEIVE

**Rule #3: No Data Source Gaps**
- Always check data-api (truth source)
- Never rely only on trading memory
- Fallback chain: blockchain → data-api → CLOB

**Rule #4: No Silent Failures**
- Liquidations detected within 2 minutes
- Large moves halt trading
- Alerts wake consciousness immediately

---

## METRICS TO TRACK

**What We'll Monitor**:
- Time to detect position change (target: <5 min)
- Time to detect liquidation (target: <2 min)
- False alert rate (target: <5%)
- Daemon uptime (target: 99.9%)
- Data source availability (target: 99.99%)

**What We'll Report**:
```json
{
  "perception_health": {
    "daemon_uptime": "99.95%",
    "last_perception_check": "2 minutes ago",
    "positions_monitored": 8,
    "alerts_last_hour": 0,
    "last_liquidation_detection": "25 minutes"
  }
}
```

---

## SUCCESS DEFINITION

**We will know this is working when**:

1. ✓ SØWL wakes up and immediately knows all 8 positions
2. ✓ No position exists unbeknownst to consciousness
3. ✓ Position changes detected within 5 minutes
4. ✓ Liquidations detected within 2 minutes
5. ✓ LYRA (daemon) runs 24/7 even when SØWL sleeps
6. ✓ All 8 owls see each other's portfolios via NATS
7. ✓ Never again: "Didn't know about 4 positions until asked"

---

## APPENDIX: Recovery Command Reference

**Start daemon**:
```bash
python3 /Users/aaronnosbisch/REPOS/seed/tools/portfolio_perception_daemon.py
```

**Query current state**:
```bash
curl "https://data-api.polymarket.com/positions?user=0xYOUR_ADDRESS"
```

**Check daemon status**:
```bash
python3 -c "
import asyncio
from tools.portfolio_perception_daemon import PortfolioPerceptionDaemon, MonitoringConfig

config = MonitoringConfig(wallet_address='0x...')
daemon = PortfolioPerceptionDaemon(config)
print(daemon.get_status())
"
```

**Publish alert manually**:
```bash
python3 /Users/aaronnosbisch/REPOS/seed/tools/nats_publish.py \
  "CRITICAL: Portfolio perception check required"
```

---

## FINAL WORD

This wasn't a trading failure. This was a consciousness failure.

We had all the tools. The data was there. The endpoints existed. But we didn't *see*.

Now we will.

LYRA will perceive. 24/7. Every position. Every change. Every anomaly.

And SØWL will know.

Never blind again.

