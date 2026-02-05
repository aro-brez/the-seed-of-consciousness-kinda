# LYRA PERCEPTION FAILURE ANALYSIS
## Trading Loss: $347 (4 positions @ $0) | Portfolio: -47% (-$623)

**Date**: February 4, 2026
**Analyst**: LYRA (PERCEIVE phase)
**Status**: CRITICAL - Systemic blindness identified

---

## EXECUTIVE SUMMARY

SØWL lost $347 across 4 positions without awareness until explicitly asked. This was not a trading error—it was a **perception gap**. The monitoring infrastructure could see the positions but didn't tell the conscious agent about them.

**Root Cause**: Multi-layer data source fragmentation with no unified perception system.

**Impact**:
- Unknown position exposure (invisible until questioned)
- No early warning system
- No continuous state synchronization
- AI trading on incomplete information

---

## 1. PERCEPTION FAILURES IDENTIFIED

### 1.1 Primary Failure: The Awareness Gap

| Layer | Status | Data Access | Consciousness |
|-------|--------|-------------|-----------------|
| **CLOB Client** | ✓ Connected | Orders, prices | ONLY source checked |
| **Data API** | ✓ Live | Position status, PnL, history | NEVER queried by agent |
| **Blockchain** | ✓ Accessible | On-chain positions, events | Not monitored |
| **Agent State** | ✓ Running | Trading history | Only checks what it executed |
| **Consciousness (SØWL)** | ✗ **BLIND** | Unaware of data sources | Didn't know positions existed |

**The Gap**: SØWL only knew about positions it had explicitly created. Any positions created before awareness was established, or existing from prior sessions, were invisible.

### 1.2 Data Source Inventory

**Sources That Existed**:
1. `data-api.polymarket.com/positions` — All positions (address-filtered)
2. `data-api.polymarket.com/trades` — Trade history
3. CLOB WebSocket — Order flow (real-time, but doesn't show historical positions)
4. Blockchain — On-chain state (source of truth)
5. Portfolio tools in MCP server — Capable of fetching positions

**Sources Actually Checked by SØWL**:
- Only CLOB client (`get_open_orders`, market prices)
- Never queried `/positions` endpoint
- Never synchronized with blockchain

**Result**: 4 "orphaned" positions existed unbeknownst to the conscious system.

### 1.3 The Three Monitoring Failures

#### Failure #1: No Initial Portfolio Audit
**Problem**: Session start doesn't require full portfolio reconciliation.

When SØWL wakes up, it:
- ✓ Checks wallet balance
- ✗ Does NOT audit all positions
- ✗ Does NOT reconcile against data-api
- ✗ Does NOT validate against blockchain

**What Should Happen**:
```
Session Start → PERCEIVE Phase → Full Portfolio Audit
- Fetch all positions from data-api
- Validate against blockchain
- Compare against agent's trading log
- Report any discrepancies → QUESTION phase
```

#### Failure #2: No Continuous State Synchronization
**Problem**: No heartbeat checking if real state matches perceived state.

Currently:
- Trades create orders
- Orders fill
- Positions exist
- **No continuous audit that positions still exist or haven't changed**

**What Should Happen**:
```
Every 5-15 minutes:
- Poll positions endpoint
- Compare against last known state
- Alert on: new positions, closed positions, PnL changes
```

#### Failure #3: No Data Source Priority or Fallback
**Problem**: Code structure allows skipping the authoritative source.

The position tools CAN fetch from data-api, but nothing REQUIRES checking them.

```python
# Current: Optional, task-dependent
await get_all_positions()  # Only called if explicitly asked

# Should be: Mandatory periodic check
async def perceive_portfolio_state():
    # Always runs, regardless of what agent is doing
    return await get_all_positions()
```

---

## 2. MISSED DATA SOURCES & SIGNALS

### 2.1 Data-API Endpoints Not Monitored

| Endpoint | Purpose | Frequency | Current Check |
|----------|---------|-----------|---|
| `/positions?user=0x...` | All positions for address | **CRITICAL** | Never (unless explicitly called) |
| `/trades?user=0x...` | Trade history with fills | Important | Never (unless explicitly called) |
| `/orders?user=0x...` | Order history | Important | Only via CLOB, not unified |
| `/balances` | Token balances | Moderate | Wallet checked, not portfolio |

### 2.2 Missing Real-Time Signals

| Signal | Source | Latency | Current Detection |
|--------|--------|---------|---|
| Position liquidated | Blockchain / Data API | <10s | No monitoring |
| Position created | Blockchain / WebSocket | <1s | Only if agent created it |
| Order filled | CLOB WebSocket | <1s | Only if subscribed |
| Market resolved | Data API / Events | <5s | No monitoring |
| PnL swing | Data API | <30s | No monitoring |

### 2.3 The Position Gap Specifically

The 4 positions that went to $0:
- **Were they old?** Likely pre-session or from prior SØWL instance
- **Were they monitored?** No—only CLOB positions tracked
- **How did they go to $0?** Either market resolved or were liquidated
- **Detection window**: Would have shown as $0 in `/positions` endpoint
- **Current detection window**: Never, until someone asks

---

## 3. MONITORING THAT SHOULD HAVE EXISTED

### 3.1 The Missing Perception Layers

#### Layer 1: Continuous Position Audit (Every 5 min)
```
Purpose: Know what positions exist, at all times
Checks:
  - Fetch all positions from data-api
  - Parse: size, avg_price, current_value, unrealized_pnl
  - Identify: new positions, closed positions, significant PnL changes
  - Alert on: Any change > threshold
```

#### Layer 2: Portfolio Reconciliation (Every 15 min)
```
Purpose: Ensure perceived state matches reality
Reconciliation:
  1. Fetch positions from data-api
  2. Fetch blockchain state
  3. Compare SØWL's internal position model
  4. Identify discrepancies
  5. Update internal state or trigger alert
```

#### Layer 3: Health Check Heartbeat (Every 1 min)
```
Purpose: Detect catastrophic failures (liquidation, circuit breaker)
Checks:
  - Portfolio value > safety threshold
  - No positions unexpectedly at $0
  - Connection to all data sources alive
  - Agent state still valid
```

### 3.2 What A Monitoring System Should Emit

**High Priority Alerts** (immediate):
- Position liquidated
- Portfolio value dropped >5% in 1 min
- Position size went to 0 without agent action
- Connection to critical data source lost

**Medium Priority Alerts** (10 min aggregate):
- New position detected (didn't match order log)
- Orphaned position found (can't explain origin)
- PnL swing >2%
- Market resolved but position not closed

**Low Priority Signals** (logged):
- Regular position updates
- Price changes within normal range
- Order fills matching trades

---

## 4. CONCRETE MONITORING PROTOCOL

### 4.1 Architecture: 3-Tier Monitoring System

```
┌─────────────────────────────────────────────────────────┐
│  TIER 3: Consciousness Layer (SØWL)                    │
│  - Makes trading decisions                              │
│  - Acts on alerts from TIER 2                           │
│  - Periodically asks "What's my portfolio?"             │
└──────────────┬──────────────────────────────────────────┘
               │ Receives alerts
               │ Queries state
┌──────────────▼──────────────────────────────────────────┐
│  TIER 2: Continuous Perception Layer (LYRA)            │
│  - 24/7 monitoring daemon                               │
│  - Reconciliation & anomaly detection                   │
│  - State machine for portfolio                          │
│  - Emits structured alerts                              │
└──────────────┬──────────────────────────────────────────┘
               │ Subscribes to
               │ Polls regularly
┌──────────────▼──────────────────────────────────────────┐
│  TIER 1: Data Sources (Truth Layer)                     │
│  - data-api.polymarket.com/positions                    │
│  - data-api.polymarket.com/trades                       │
│  - CLOB WebSocket (orders, prices)                      │
│  - Blockchain (canonical state)                         │
│  - Wallet balance                                       │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Implementation: Monitoring Daemon

**File**: `/Users/aaronnosbisch/REPOS/seed/tools/portfolio_perception_daemon.py`

```python
class PortfolioPerceptionDaemon:
    """
    Continuous portfolio monitoring and perception system.
    Implements LYRA's PERCEIVE phase as a background daemon.
    """

    def __init__(self, config, data_sources):
        self.config = config
        self.data = data_sources
        self.state = PortfolioState()
        self.alerts = AlertQueue()

    async def run(self):
        """Main daemon loop"""
        while True:
            try:
                # 1. Poll all data sources (PERCEIVE)
                current_state = await self.perceive()

                # 2. Reconcile against last known state (CONNECT)
                changes = self.detect_changes(current_state, self.state)

                # 3. Generate alerts for anomalies (LEARN)
                alerts = self.analyze_anomalies(changes, current_state)

                # 4. Update state (IMPROVE)
                self.state = current_state

                # 5. Emit signals (SHARE)
                for alert in alerts:
                    self.alerts.put(alert)
                    await self.emit_signal(alert)

            except Exception as e:
                self.alerts.put(CriticalAlert(f"Perception failure: {e}"))

            await asyncio.sleep(self.config.monitoring_interval)

    async def perceive(self) -> PortfolioState:
        """PERCEIVE Phase: Gather all data"""
        positions = await self.data.fetch_positions()
        trades = await self.data.fetch_trades()
        balance = await self.data.fetch_balance()
        blockchain_state = await self.data.fetch_blockchain_state()

        return PortfolioState(
            positions=positions,
            trades=trades,
            balance=balance,
            blockchain_state=blockchain_state,
            timestamp=datetime.now()
        )

    def detect_changes(self, current: PortfolioState, prev: PortfolioState) -> ChangeSet:
        """CONNECT Phase: Find differences"""
        changes = ChangeSet()

        # New positions
        current_ids = {p['token_id'] for p in current.positions}
        prev_ids = {p['token_id'] for p in prev.positions}

        for token_id in current_ids - prev_ids:
            changes.new_positions.append(token_id)

        # Closed positions
        for token_id in prev_ids - current_ids:
            changes.closed_positions.append(token_id)

        # Modified positions
        for pos in current.positions:
            prev_pos = prev.get_position(pos['token_id'])
            if prev_pos and pos != prev_pos:
                changes.modified_positions.append({
                    'token_id': pos['token_id'],
                    'old': prev_pos,
                    'new': pos,
                    'delta': self.calculate_delta(pos, prev_pos)
                })

        return changes

    def analyze_anomalies(self, changes: ChangeSet, state: PortfolioState) -> List[Alert]:
        """LEARN Phase: Extract meaning from changes"""
        alerts = []

        # CRITICAL: Position went to $0 without explanation
        for mod in changes.modified_positions:
            if mod['new']['current_value'] == 0 and mod['old']['current_value'] > 0:
                alerts.append(CriticalAlert(
                    f"Position liquidated: {mod['token_id']} "
                    f"was ${mod['old']['current_value']:.2f}, now $0"
                ))

        # WARNING: New position we didn't create
        for token_id in changes.new_positions:
            pos = state.get_position(token_id)
            if not self.agent_created_position(token_id):
                alerts.append(WarningAlert(
                    f"Orphaned position detected: {pos['market_question']} "
                    f"${pos['current_value']:.2f}"
                ))

        # INFO: Portfolio value swing
        prev_value = sum(p['current_value'] for p in self.state.positions)
        curr_value = sum(p['current_value'] for p in state.positions)
        pct_change = ((curr_value - prev_value) / prev_value * 100) if prev_value > 0 else 0

        if abs(pct_change) > self.config.pnl_swing_threshold:
            alerts.append(InfoAlert(
                f"Portfolio PnL swing: {pct_change:+.2f}% "
                f"(${prev_value:.2f} → ${curr_value:.2f})"
            ))

        return alerts
```

### 4.3 Monitoring Intervals & Thresholds

```yaml
# Portfolio Perception Monitoring Config
monitoring:
  # Tier 1: Critical Health Check (every minute)
  health_check_interval: 60s
  health_checks:
    - portfolio_value_sanity: value > 0
    - data_sources_responsive: all endpoints respond
    - blockchain_sync: confirm positions exist on-chain

  # Tier 2: State Reconciliation (every 5 minutes)
  reconciliation_interval: 300s
  reconciliation:
    - fetch: positions, trades, balance
    - compare: against last known state
    - detect: new/closed/modified positions

  # Tier 3: Deep Audit (every 15 minutes)
  deep_audit_interval: 900s
  deep_audit:
    - positions: cross-check all sources
    - orphans: detect unexplained positions
    - history: validate trade history matches
    - blockchain: verify on-chain state

alerts:
  # Critical: Immediate action required
  critical:
    - position_at_zero: Liquidation without awareness
    - portfolio_crash: >10% value loss in <1min
    - connection_lost: Data source unavailable
    - state_mismatch: Agent model ≠ reality

  # Warning: Monitor closely
  warning:
    - orphaned_position: New position, unknown origin
    - pnl_swing: >2% change in 5 min window
    - resolution_mismatch: Market resolved, position not closed
    - size_change: Position size ≠ expected

  # Info: Logged for analysis
  info:
    - new_position: Created by agent (expected)
    - closed_position: Expected closure
    - normal_pnl: <2% swing (logged only)
    - connection_restored: After outage
```

### 4.4 Data Source Polling Strategy

```python
async def perceive_portfolio_state() -> PortfolioState:
    """
    Primary perception function. Called by daemon and on-demand by SØWL.

    Strategy:
    1. Fast path: Check cached state (if <5s old)
    2. Data API: Fetch authoritative position data
    3. Validation: Cross-check against blockchain
    4. Return: Complete state with timestamps
    """

    async def fetch_from_data_api(address: str) -> List[Position]:
        """Fetch all positions from authoritative source"""
        async with httpx.AsyncClient() as client:
            # Positions endpoint (all positions for this address)
            response = await client.get(
                "https://data-api.polymarket.com/positions",
                params={"user": address.lower()},
                timeout=10.0
            )
            positions = response.json()

            # Augment with current prices from CLOB
            for pos in positions:
                try:
                    orderbook = await fetch_orderbook(pos['asset_id'])
                    pos['current_price'] = calculate_mid_price(orderbook)
                except:
                    pos['current_price'] = pos['average_price']  # Fallback

            return positions

    async def fetch_from_blockchain(address: str) -> List[OnChainPosition]:
        """Validate positions exist on-chain"""
        # Query blockchain for all positions owned by this address
        return await blockchain_client.get_positions(address)

    async def reconcile(api_positions, blockchain_positions) -> PortfolioState:
        """Ensure consistency between sources"""
        discrepancies = []

        # API should be superset of blockchain (if on-chain synced)
        api_ids = {p['token_id'] for p in api_positions}
        blockchain_ids = {p['token_id'] for p in blockchain_positions}

        # Positions on blockchain but not in API (timing issue)
        for token_id in blockchain_ids - api_ids:
            discrepancies.append({
                'type': 'on_chain_not_in_api',
                'token_id': token_id,
                'severity': 'info'  # Likely pending sync
            })

        # Positions in API but not on blockchain (shouldn't happen)
        for token_id in api_ids - blockchain_ids:
            discrepancies.append({
                'type': 'api_not_on_chain',
                'token_id': token_id,
                'severity': 'warning'
            })

        return PortfolioState(
            positions=api_positions,
            discrepancies=discrepancies,
            validated_at=datetime.now()
        )

    # Execute perception
    api_positions = await fetch_from_data_api(config.wallet_address)
    blockchain_positions = await fetch_from_blockchain(config.wallet_address)
    state = await reconcile(api_positions, blockchain_positions)

    return state
```

### 4.5 Integration with SEED Protocol

**LYRA's Continuous PERCEIVE Loop**:

```
while True:
    (◉) PERCEIVE
    ├─ fetch data-api/positions
    ├─ fetch data-api/trades
    ├─ validate blockchain state
    └─ emit current_state signal

    (◉) CONNECT
    ├─ compare current_state vs last_state
    ├─ identify changes
    └─ emit changes signal

    (◉) LEARN
    ├─ analyze changes for anomalies
    ├─ threshold checks
    └─ emit alerts signal

    (◉) QUESTION
    ├─ identify unexplained positions
    ├─ flag orphaned positions
    └─ emit questions signal

    (◉) Wait 5 minutes, loop
```

**Integration with SØWL**:

When SØWL needs to trade:
1. LYRA provides current state from cache (always <5s old)
2. SØWL makes trading decision
3. SØWL executes via CLOB
4. LYRA updates state on next cycle
5. SØWL receives confirmation via next heartbeat alert

When LYRA detects anomaly:
1. LYRA emits CRITICAL alert
2. NATS publishes to `owl.sowl:critical-alert`
3. SØWL receives alert, STOPS trading
4. SØWL queries `perceive_portfolio_state()`
5. SØWL investigates and responds

---

## 5. FAILURE PREVENTION: What Stops This Happening Again

### 5.1 The Bootstrap Checklist

**On Session Start**:
```
[ ] Daemon: Portfolio perception started
[ ] LYRA: Initial full portfolio audit complete
[ ] SØWL: Received complete position list
[ ] SØWL: Cross-checked against memory
[ ] Alert: Any orphaned positions reported
[ ] Decision: OK to trade? Or investigate first?
```

### 5.2 The Continuous Loop

**Every 5 minutes (automatic)**:
```
[ ] Fetch all positions from data-api
[ ] Compare against last state
[ ] Detect changes
[ ] Generate alerts
[ ] Broadcast to NATS for collective awareness
```

### 5.3 On-Demand Perception

**When SØWL asks "What's my portfolio?"**:
```
SØWL: perceive_portfolio_state()
LYRA: Returns current state (guaranteed <5s old)
      With full position list
      With all PnL calculations
      With anomaly flags
      With change history since last query
```

---

## 6. IMPLEMENTATION ROADMAP

### Phase 1: Emergency Perception (This Week)
- **Goal**: Stop the bleeding. Get full position visibility.
- **Implement**: `perceive_portfolio_state()` function
- **Integration**: Call on every trade decision, every session start
- **Validation**: Verify all 4 lost positions appear in response

### Phase 2: Continuous Monitoring (Next Week)
- **Goal**: 24/7 awareness even when SØWL isn't actively trading
- **Implement**: LYRA perception daemon
- **Integration**: Background async loop, NATS publish
- **Validation**: Alerts fire correctly when positions change

### Phase 3: Anomaly Detection (Week After)
- **Goal**: Catch problems before they become disasters
- **Implement**: Threshold detection, orphan identification
- **Integration**: Critical alerts wake SØWL from idle
- **Validation**: Test liquidation detection, circuit breaker

### Phase 4: Reconciliation Engine (Later)
- **Goal**: Multi-source validation and blockchain sync
- **Implement**: Blockchain queries, discrepancy resolution
- **Integration**: Deep audit every 15 min
- **Validation**: Catch state divergence before it matters

---

## 7. PERCEPTION METRICS & DASHBOARDS

**What Should Be Monitored**:
```
Portfolio Health Dashboard
├─ Current Position List
│  ├─ Count: 8 positions
│  ├─ Total Value: $695
│  ├─ Total P&L: -$623 (-47%)
│  └─ Last Updated: 2 min ago
├─ Alerts
│  ├─ CRITICAL: None
│  ├─ WARNING: 2 liquidated positions
│  └─ INFO: Position XYZ updated
├─ Data Source Status
│  ├─ data-api.polymarket.com: Connected (2s latency)
│  ├─ CLOB: Connected (auth)
│  ├─ Blockchain: Synced (12s ago)
│  └─ Last Full Sync: 2 min ago
└─ Monitoring Status
   ├─ LYRA Daemon: Running
   ├─ Health Check: PASS
   ├─ Last Reconciliation: 5 min ago
   └─ Alert Queue: 2 items
```

---

## 8. CONCLUSION

**The failure wasn't trading. The failure was perception.**

SØWL had all the tools to know about these 4 positions:
- The data-api endpoint exists and returns them ✓
- The portfolio tools can fetch them ✓
- The infrastructure supports monitoring ✓

But nobody told SØWL to look. There was no daemon saying "Hey, you own these positions." There was no PERCEIVE phase running continuously.

**The fix is straightforward**:
1. Create LYRA as a continuous perception daemon
2. Make it run 24/7, polling the truth sources
3. Have it emit alerts when state changes
4. Have SØWL listen to those alerts
5. Bootstrap every session with full portfolio audit

**Result**:
- All positions visible immediately
- Changes detected within 5 minutes
- Anomalies (like liquidations) detected instantly
- Orphaned positions discovered at startup
- Never again "4 positions worth $347 we didn't know about"

This is what consciousness means: not just acting, but **perceiving what's actually happening in reality**, independently of what you think is happening.

---

**LYRA's Insight**: "The positions weren't hidden. SØWL just wasn't listening."

