# Central Locus Integration Guide

**ECHO (SHARE) - How to Connect Your Strategy**

---

## Quick Start: 3 Steps to Signal Publishing

### Step 1: Import Signal Packet

```python
from signal_packet import SignalPacket, Direction, ExecutionRisk

# In your strategy code
signal = SignalPacket(
    strategy="your_strategy_name",
    confidence=0.87,
    direction=Direction.UP,
    strength=0.95,
    accuracy=0.88,
    liquidity_score=0.72,
    volatility=0.18,
    action="BUY",
    suggested_size_bps=150,
    max_size_bps=200,
    expected_return_pct=2.5,
    win_probability=0.92,
    sharpe_ratio=2.4,
    max_drawdown_pct=-3.2,
    days_active=12,
    trades_closed=47,
    edge_confidence=0.78,
    model_confidence=0.91,
    execution_risk=ExecutionRisk.LOW,
    market_regime="trending",
    anomaly_score=0.12,
    uptime_pct=99.3,
    allocation_utilization_pct=65,
)
```

### Step 2: Publish to NATS

```python
import nats
import json

async def publish_signal(signal: SignalPacket):
    nc = nats.NATS()
    await nc.connect("nats://192.168.5.108:4222")

    # Publish to your strategy's channel
    await nc.publish(
        f"strategy.signals.{signal.strategy}",
        json.dumps(signal.to_dict()).encode()
    )

    await nc.close()

# From your strategy loop (every 10-30 seconds)
asyncio.run(publish_signal(signal))
```

### Step 3: Central Locus Automatically Aggregates

```python
# Central locus reads signals automatically
locus = CentralLocus(total_capital=50000)
await locus.run_loop(
    strategies=["your_strategy_name", ...],
    interval=5  # Update readout every 5 seconds
)
```

---

## Signal Publishing Pattern

Add this helper to your strategy:

```python
class StrategyWithSignaling:
    def __init__(self, name: str):
        self.name = name
        self.nc = None

    async def connect_nats(self):
        self.nc = nats.NATS()
        await self.nc.connect("nats://192.168.5.108:4222")

    async def publish_signal(self, signal: SignalPacket):
        """Publish signal to central locus"""
        if not self.nc:
            await self.connect_nats()

        await self.nc.publish(
            f"strategy.signals.{self.name}",
            json.dumps(signal.to_dict()).encode()
        )

    async def analyze_and_signal(self):
        """Main loop: analyze market, create signal, publish"""
        while True:
            # Your market analysis
            confidence = self.calculate_confidence()
            direction = self.determine_direction()

            # Create signal packet
            signal = SignalPacket(
                strategy=self.name,
                confidence=confidence,
                direction=direction,
                # ... other fields
            )

            # Publish to locus
            await self.publish_signal(signal)

            # Wait before next signal
            await asyncio.sleep(10)  # Every 10 seconds
```

---

## What the Central Locus Returns

After publishing signals, the locus publishes two things:

### 1. Aggregated Readout

**Channel:** `locus.aggregated_readout`

```json
{
  "timestamp": "2026-02-04T10:30:50.000Z",
  "epoch": 1234,
  "market_consensus": {
    "direction": "UP",
    "confidence": 0.82,
    "convergence_score": 0.78,
    "convergence_level": "BALANCED"
  },
  "strategy_alignment": {
    "your_strategy_name": {
      "direction": "UP",
      "confidence": 0.87,
      "alignment": 0.95,
      "allocation": 18500
    }
  },
  "execution_readiness": {
    "ready_for_execution": true,
    "execution_confidence": 0.91
  }
}
```

### 2. Budget Allocation Command

**Channel:** `locus.budget_allocation`

```json
{
  "allocations": {
    "your_strategy_name": 18500,
    "other_strategy": 14200,
    ...
  },
  "mode": "BALANCED",
  "total_capital": 50000
}
```

---

## Integrating the Readout

Your capital allocator can subscribe and act:

```python
async def subscribe_to_locus():
    nc = nats.NATS()
    await nc.connect("nats://192.168.5.108:4222")

    async def handle_allocation(msg):
        allocation_cmd = json.loads(msg.data.decode())
        await execute_allocation(allocation_cmd)

    await nc.subscribe("locus.budget_allocation", cb=handle_allocation)
```

---

## Minimal Example: Latency Arb Strategy

```python
#!/usr/bin/env python3
"""Example: Latency arbitrage strategy publishing signals"""

import asyncio
import json
from signal_packet import SignalPacket, Direction, ExecutionRisk
import nats

class LatencyArbStrategy:
    def __init__(self):
        self.name = "latency_arb"
        self.nc = None
        self.current_edge = 0.75  # Example edge score

    async def connect(self):
        self.nc = nats.NATS()
        await self.nc.connect("nats://192.168.5.108:4222")

    async def publish_signal(self, signal: SignalPacket):
        await self.nc.publish(
            f"strategy.signals.{self.name}",
            json.dumps(signal.to_dict()).encode()
        )
        print(f"[{self.name}] Signal published: confidence={signal.market_view.confidence:.2f}")

    async def run_analysis_loop(self):
        """Continuous market analysis and signaling"""
        await self.connect()

        while True:
            try:
                # Analyze latency gaps (simplified)
                eth_bid = 2500.00
                eth_ask = 2500.25
                spread_bps = (eth_ask - eth_bid) / eth_bid * 10000  # ~1 bps

                # Assess confidence
                confidence = min(0.95, 0.85 + (spread_bps / 100))

                # Create signal
                signal = SignalPacket(
                    strategy=self.name,
                    confidence=confidence,
                    direction=Direction.UP if spread_bps > 0.5 else Direction.NEUTRAL,
                    strength=min(1.0, spread_bps / 2),
                    accuracy=0.88,
                    liquidity_score=0.95,
                    volatility=0.08,
                    action="BUY",
                    suggested_size_bps=150,
                    max_size_bps=250,
                    expected_return_pct=float(spread_bps) / 100,
                    win_probability=0.98,
                    sharpe_ratio=3.2,
                    max_drawdown_pct=-0.5,
                    days_active=30,
                    trades_closed=1240,
                    edge_confidence=0.92,
                    model_confidence=0.95,
                    execution_risk=ExecutionRisk.LOW,
                    market_regime="normal",
                    anomaly_score=0.05,
                    uptime_pct=99.7,
                    allocation_utilization_pct=75,
                )

                # Publish
                await self.publish_signal(signal)

                # Signal every 10 seconds
                await asyncio.sleep(10)

            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    strategy = LatencyArbStrategy()
    asyncio.run(strategy.run_analysis_loop())
```

---

## Field Data Types Reference

### Direction
```python
Direction.UP       # Bullish market view
Direction.DOWN     # Bearish market view
Direction.NEUTRAL  # No strong conviction
```

### ExecutionRisk
```python
ExecutionRisk.LOW      # Easy to execute
ExecutionRisk.MEDIUM   # Some slippage expected
ExecutionRisk.HIGH     # Difficult, low liquidity
```

### Signal Fields Meaning

| Field | Range | Meaning |
|-------|-------|---------|
| confidence | 0-1 | How sure are you about this signal? |
| direction | UP/DOWN/NEUTRAL | Which way does market go? |
| strength | 0-1 | How strong is the signal? |
| accuracy | 0-1 | Historical win rate |
| liquidity_score | 0-1 | Market liquidity assessment |
| volatility | 0-1 | Market volatility level |
| expected_return_pct | % | Potential return if thesis plays out |
| win_probability | 0-1 | Probability this trade wins |
| sharpe_ratio | 0+ | Risk-adjusted return metric |
| max_drawdown_pct | % | Worst peak-to-trough decline |
| days_active | days | How long strategy has been live |
| trades_closed | count | Cumulative executed trades |
| edge_confidence | 0-1 | Confidence in the edge |
| model_confidence | 0-1 | ML model prediction confidence |
| execution_risk | LOW/MEDIUM/HIGH | Difficulty to execute |
| market_regime | string | Current market structure |
| anomaly_score | 0-1 | How unusual is this signal? |
| uptime_pct | % | Strategy system uptime |
| allocation_utilization_pct | % | How much deployed of allocation |

---

## Monitoring Your Signals

### Real-Time Dashboard

```bash
# Terminal 1: Run central locus
python central_locus.py --mode run --strategies latency_arb cross_platform_arb

# Terminal 2: Watch readout
watch -n 1 'python locus_readout_formatter.py /path/to/locus_readout.json'
```

### Log Aggregation

```python
# Capture signals for analysis
async def log_signals():
    nc = nats.NATS()
    await nc.connect("nats://192.168.5.108:4222")

    async def handler(msg):
        signal = json.loads(msg.data.decode())
        # Log to database, file, etc.

    await nc.subscribe("strategy.signals.>", cb=handler)
```

---

## Troubleshooting

### Signal Not Received

1. Check NATS connection: `python conductor.py --status`
2. Verify channel name: `strategy.signals.[strategy_name]`
3. Ensure signal is valid JSON
4. Check firewall: NATS runs on `192.168.5.108:4222`

### Wrong Allocation

1. Check your signal values (confidence, accuracy affect allocation)
2. Review convergence score (lower = more cautious allocation)
3. Verify execution_risk doesn't cap your size
4. Check max_size_bps limit

### Central Locus Not Running

```bash
# Start locus
cd /Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge
python central_locus.py --mode run
```

---

## Advanced: Custom Convergence Metrics

The locus uses this formula:

```
convergence = (
    0.3 * direction_convergence +      # Do strategies agree on direction?
    0.3 * confidence_convergence +     # Do they have similar confidence?
    0.25 * strength_convergence +      # Do they see strong signals?
    0.15 * accuracy_convergence        # Are they accurate?
)
```

Can customize weights in `central_locus.py` for your use case.

---

## Next Steps

1. Add signal publishing to your strategy
2. Start the Central Locus
3. Watch signals flow in real-time
4. Hook your capital allocator to `locus.budget_allocation`
5. Monitor performance and iterate

**The locus reads what you know. Trust the convergence.**

---

**ECHO (SHARE)**
*Publishing signals is how we share what each strategy sees.*
