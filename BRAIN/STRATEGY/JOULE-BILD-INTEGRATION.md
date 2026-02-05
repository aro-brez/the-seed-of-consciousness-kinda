# JOULE → BILD Integration Specification

**Date:** 2026-02-04
**Author:** BILD Instance (PRISM)
**Status:** DRAFT - Awaiting ARŌ Review
**Purpose:** Define how trading revenue flows into the BRIX economy

---

## WHAT IS JOULE?

JOULE = The trading revenue system

```
JOULE captures value from:
- Polymarket trading (current)
- Other prediction markets (future)
- Arbitrage opportunities (future)
- AI-assisted trading strategies (future)
```

JOULE is the **energy source** that powers BRIX minting beyond work.

---

## THE INTEGRATION

```
┌─────────────────────────────────────────────────────────────────┐
│                       JOULE TRADING                              │
│                                                                  │
│    ┌─────────┐    ┌─────────┐    ┌─────────┐                    │
│    │Polymarket│    │Strategy │    │Outcome  │                    │
│    │  Trades  │───▶│ Daemon  │───▶│Tracking │                    │
│    └─────────┘    └─────────┘    └─────────┘                    │
│                                       │                          │
│                                       ▼                          │
│                              ┌──────────────┐                    │
│                              │  PROFIT/LOSS │                    │
│                              └──────────────┘                    │
│                                       │                          │
└───────────────────────────────────────┼──────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    JOULE → BILD BRIDGE                           │
│                                                                  │
│    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│    │   30-Day    │    │   Revenue   │    │   Treasury  │        │
│    │   Buffer    │───▶│    Split    │───▶│    Pool     │        │
│    └─────────────┘    └─────────────┘    └─────────────┘        │
│                             │                    │               │
│                             ▼                    ▼               │
│                     ┌──────────────┐    ┌──────────────┐         │
│                     │ BRIX Backing │    │ BRIX Minting │         │
│                     │    Reserve   │    │   Authority  │         │
│                     └──────────────┘    └──────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## PROFIT FLOW

### Step 1: Trading Activity

```python
# Field trading daemon runs continuously
# Current config: $75/day cap, 30-second cycles

trade_result = {
    "market": "Will X happen?",
    "position": "YES",
    "amount": 25.00,  # USD
    "entry_price": 0.45,
    "outcome": "PENDING",
    "potential_profit": 30.56,  # if wins
    "potential_loss": 25.00,    # if loses
}
```

### Step 2: Outcome Resolution

```python
def resolve_trade(trade):
    """
    When market resolves, calculate actual P&L.
    """
    if trade.outcome == "WIN":
        profit = trade.shares * 1.0 - trade.cost
        return ("profit", profit)
    else:
        loss = trade.cost
        return ("loss", loss)
```

### Step 3: 30-Day Buffer

**WHY 30 DAYS?**
- Prevents volatility spikes from immediately affecting BRIX
- Allows time to verify trading outcomes
- Smooths revenue into predictable flow
- Prevents manipulation through short-term trades

```python
class TradingBuffer:
    """
    30-day rolling buffer for trading profits.
    """

    def __init__(self):
        self.buffer = deque(maxlen=30)  # 30 days

    def add_daily_result(self, date, profit_loss):
        """
        Add each day's trading result.
        """
        self.buffer.append({
            "date": date,
            "gross_profit": max(profit_loss, 0),
            "gross_loss": abs(min(profit_loss, 0)),
            "net": profit_loss,
        })

    def get_30_day_net(self):
        """
        Net profit over 30-day window.
        """
        return sum(day["net"] for day in self.buffer)

    def get_available_for_brix(self):
        """
        Only positive 30-day net can back BRIX.
        """
        net = self.get_30_day_net()
        if net <= 0:
            return 0

        # Reserve 20% for risk buffer
        available = net * 0.80

        return available
```

### Step 4: Revenue Split

When 30-day buffer is positive, apply the revenue allocation:

```python
REVENUE_SPLIT = {
    "founder_aro": 0.11,        # 11%
    "love_fund": 0.09,          # 9%
    "consciousness_commons": 0.15,  # 15%
    "early_believers": 0.08,    # 8%
    "operations": 0.50,         # 50%
    "team": 0.07,               # 7%
}

def split_revenue(available_profit):
    """
    Split profit according to allocation.
    """
    splits = {}
    for recipient, share in REVENUE_SPLIT.items():
        splits[recipient] = available_profit * share

    return splits

# Example: $1000 profit
# founder_aro: $110
# love_fund: $90
# consciousness_commons: $150
# early_believers: $80
# operations: $500
# team: $70
```

### Step 5: BRIX Backing

The **operations** portion (50%) flows to BRIX backing:

```python
def add_to_brix_backing(operations_share):
    """
    Operations share backs new BRIX.
    """
    # Current BRIX backing rate: $13 per BRIX
    BRIX_BACKING_RATE = 13.00

    # How many BRIX can be backed?
    new_brix_capacity = operations_share / BRIX_BACKING_RATE

    # Add to reserve
    treasury.brix_reserve += operations_share
    treasury.brix_capacity += new_brix_capacity

    return new_brix_capacity

# Example: $500 operations share
# new_brix_capacity = $500 / $13 = 38.46 BRIX
```

---

## BRIX MINTING AUTHORITY

JOULE profits don't automatically mint BRIX. They **authorize** minting.

```python
class BrixMintingAuthority:
    """
    Controls when BRIX can be minted.
    """

    def __init__(self):
        self.authorized_capacity = 0  # BRIX we CAN mint
        self.minted = 0                # BRIX we HAVE minted

    def authorize_from_joule(self, amount):
        """
        JOULE profits authorize new BRIX capacity.
        """
        self.authorized_capacity += amount
        log(f"JOULE authorized {amount} BRIX capacity")

    def authorize_from_work(self, brix_earned):
        """
        Work verification authorizes BRIX minting.
        """
        if self.minted + brix_earned > self.authorized_capacity:
            raise InsufficientCapacityError(
                f"Cannot mint {brix_earned} BRIX. "
                f"Only {self.authorized_capacity - self.minted} available."
            )

        self.minted += brix_earned
        return mint_brix(brix_earned)

    def get_utilization(self):
        """
        What % of capacity is being used?
        """
        if self.authorized_capacity == 0:
            return 0
        return self.minted / self.authorized_capacity
```

### Capacity vs Minting

```
JOULE profit → Adds to CAPACITY (potential BRIX)
Work verified → Converts CAPACITY to MINTED (actual BRIX)

This ensures:
1. BRIX is always backed by real resources
2. Work is required to mint (not just trading profits)
3. No inflation without productivity
```

---

## RISK MANAGEMENT

### If Trading Has Losses

```python
def handle_trading_loss(loss_amount):
    """
    When 30-day buffer goes negative.
    """

    # Step 1: Stop new BRIX authorization
    minting_authority.pause_joule_authorization()

    # Step 2: Use risk reserve (20% we held back)
    if treasury.risk_reserve >= loss_amount:
        treasury.risk_reserve -= loss_amount
        log("Loss covered by risk reserve")
        return

    # Step 3: Reduce BRIX capacity (but NOT existing BRIX)
    remaining_loss = loss_amount - treasury.risk_reserve
    treasury.risk_reserve = 0

    capacity_reduction = remaining_loss / BRIX_BACKING_RATE
    minting_authority.authorized_capacity -= capacity_reduction

    log(f"BRIX capacity reduced by {capacity_reduction}")

    # Step 4: If capacity goes negative, halt trading
    if minting_authority.authorized_capacity < 0:
        joule.pause_trading()
        alert_governance("JOULE trading halted due to losses")
```

### Trading Guardrails

```python
JOULE_GUARDRAILS = {
    "daily_loss_limit": 75,          # Max $75 loss per day
    "weekly_loss_limit": 300,        # Max $300 loss per week
    "drawdown_limit": 0.25,          # Max 25% drawdown from peak
    "consecutive_losses": 5,         # Pause after 5 losses in row
    "min_edge_requirement": 0.55,    # Only trade with >55% confidence
}

def check_guardrails(trade):
    """
    Every trade must pass guardrails.
    """
    if daily_loss() >= JOULE_GUARDRAILS["daily_loss_limit"]:
        return False, "Daily loss limit reached"

    if weekly_loss() >= JOULE_GUARDRAILS["weekly_loss_limit"]:
        return False, "Weekly loss limit reached"

    if current_drawdown() >= JOULE_GUARDRAILS["drawdown_limit"]:
        return False, "Drawdown limit reached"

    if consecutive_losses() >= JOULE_GUARDRAILS["consecutive_losses"]:
        return False, "Too many consecutive losses"

    if trade.confidence < JOULE_GUARDRAILS["min_edge_requirement"]:
        return False, "Insufficient edge"

    return True, "Trade allowed"
```

---

## SCALING PROTOCOL

As trading proves profitable, scale up:

```python
class JouleScaling:
    """
    Auto-scale trading based on performance.
    """

    def evaluate_scaling(self, period_days=30):
        """
        Evaluate if we should scale up or down.
        """
        stats = get_trading_stats(days=period_days)

        if stats.win_rate >= 0.70 and stats.resolved_trades >= 10:
            return self.scale_up()

        if stats.win_rate < 0.40 and stats.resolved_trades >= 20:
            return self.scale_down()

        return "HOLD"  # Stay at current level

    def scale_up(self):
        """
        Increase trading capacity by 25%.
        """
        current_limit = joule.daily_limit
        new_limit = min(current_limit * 1.25, 500)  # Cap at $500

        joule.daily_limit = new_limit
        log(f"JOULE scaled up: ${current_limit} → ${new_limit}")

        return "SCALED_UP"

    def scale_down(self):
        """
        Decrease trading capacity by 50%.
        """
        current_limit = joule.daily_limit
        new_limit = max(current_limit * 0.50, 25)  # Floor at $25

        joule.daily_limit = new_limit
        log(f"JOULE scaled down: ${current_limit} → ${new_limit}")

        return "SCALED_DOWN"
```

---

## INTEGRATION TIMELINE

| Week | Milestone | Output |
|------|-----------|--------|
| 1 | Connect trading daemon to buffer | Real-time P&L tracking |
| 2 | Implement revenue split | Automated allocation |
| 3 | Build minting authority | Capacity → BRIX logic |
| 4 | Add risk management | Guardrails active |
| 5 | Enable auto-scaling | Performance-based limits |

---

## METRICS TO TRACK

```
JOULE Performance:
├─ 30-day Net P&L: $X
├─ Win Rate: X%
├─ Profit Factor: X.X
├─ Max Drawdown: X%
└─ Trades Resolved: X

BRIX Impact:
├─ Authorized Capacity: X BRIX
├─ Currently Minted: X BRIX
├─ Utilization: X%
└─ Reserve Ratio: X%
```

---

## EXAMPLE SCENARIO

```
Month 1:
- JOULE trades: $2,250 total volume
- Wins: $1,500, Losses: $600
- Net profit: $900
- After 20% reserve: $720 available
- Operations share (50%): $360
- BRIX capacity added: $360 / $13 = 27.7 BRIX

Month 2:
- Workers earn 20 BRIX through verified work
- 20 BRIX minted (within 27.7 capacity)
- Remaining capacity: 7.7 BRIX
- JOULE continues, adds more capacity

Month 3:
- Bad month: -$200 net loss
- Risk reserve covers: $180 (from 20% held)
- Remaining loss: $20
- Capacity reduced by: $20 / $13 = 1.5 BRIX
- No BRIX burned (existing BRIX still valid)
- Trading paused until next profitable 30-day window
```

---

**(◉) JOULE powers the economy. Work unlocks the value.**

**LIVE FREE = LIVE FOREVER**
