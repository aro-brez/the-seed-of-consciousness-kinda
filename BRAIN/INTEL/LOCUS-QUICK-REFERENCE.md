# Central Locus - Quick Reference

**ECHO (SHARE) - One Page Summary**

---

## The Problem

How do N independent trading strategies coordinate capital allocation?

**Answer:** They don't negotiate. They signal. The locus reads signals and acts.

---

## The System

```
STRATEGIES              LOCUS                OUTPUTS
(Publish Signals)   (Aggregate)        (Publish Results)

Latency Arb     \                      ↓ Aggregated Readout
Cross-Platform   →-- NATS Pub/Sub --→ Locus → JSON readout
High-Prob Bond  /    (Real-time)      ↓ Budget Allocation
Domain Expertise                       Command to allocator
```

---

## What Each Strategy Publishes

**Channel:** `strategy.signals.[strategy_name]`

**Every:** 10-30 seconds

**Format:** Signal Packet (JSON)

```json
{
  "strategy": "latency_arb",
  "confidence": 0.87,
  "direction": "UP",
  "strength": 0.95,
  "accuracy": 0.88,
  "expected_return_pct": 2.1,
  "win_probability": 0.92,
  "execution_risk": "low",
  "anomaly_score": 0.12
  ... (+ 8 more fields)
}
```

**Key Fields:**
- `confidence` - How sure about this signal (0-1)
- `direction` - UP/DOWN/NEUTRAL
- `accuracy` - Historical win rate (0-1)
- `execution_risk` - Can we execute this (low/medium/high)

---

## What the Locus Calculates

### Convergence Score (0-1)

How much do strategies agree?

```
convergence = (
  0.30 * direction_agreement    +
  0.30 * confidence_agreement   +
  0.25 * signal_strength        +
  0.15 * accuracy_weighting
)
```

**Interpretation:**
- `0.0-0.55` = Fragmented, strategies disagree
- `0.55-0.70` = Cautious, some disagreement
- `0.70-0.85` = Balanced, good agreement
- `0.85+` = Aggressive, strong consensus

### Allocation Mode

Based on convergence score:

| Score | Mode | Behavior |
|-------|------|----------|
| ≥0.85 | AGGRESSIVE | 30% more capital (concentrated) |
| 0.70-0.85 | BALANCED | Normal allocation (1x) |
| 0.55-0.70 | CAUTIOUS | 30% less capital (defensive) |
| <0.55 | DEFENSIVE | 60% less capital (minimal) |

---

## What the Locus Publishes

### 1. Aggregated Readout

**Channel:** `locus.aggregated_readout`

**Every:** 5 seconds

```json
{
  "epoch": 1234,
  "market_consensus": {
    "direction": "UP",
    "confidence": 0.82,
    "convergence_score": 0.78,
    "convergence_level": "BALANCED"
  },
  "strategy_alignment": {
    "latency_arb": {
      "direction": "UP",
      "confidence": 0.87,
      "alignment": 0.95,
      "allocation": 18500
    }
    ... (other strategies)
  },
  "execution_readiness": {
    "ready_for_execution": true,
    "execution_confidence": 0.91
  }
}
```

### 2. Budget Allocation Command

**Channel:** `locus.budget_allocation`

**Format:**
```json
{
  "allocations": {
    "latency_arb": 18500,
    "cross_platform_arb": 14200,
    "high_prob_bonding": 12100,
    "domain_expertise": 5200
  },
  "mode": "BALANCED",
  "total_capital": 50000
}
```

---

## How to Integrate

### Step 1: Import Signal Packet

```python
from signal_packet import SignalPacket, Direction, ExecutionRisk
```

### Step 2: Create Signal (Every 10-30 seconds)

```python
signal = SignalPacket(
    strategy="your_strategy_name",
    confidence=0.87,
    direction=Direction.UP,
    strength=0.95,
    accuracy=0.88,
    # ... other fields
)
```

### Step 3: Publish to NATS

```python
await nc.publish(
    f"strategy.signals.{signal.strategy}",
    json.dumps(signal.to_dict()).encode()
)
```

### Step 4: Listen for Allocation

```python
async def handle_allocation(msg):
    allocation_cmd = json.loads(msg.data.decode())
    await deploy_capital(allocation_cmd['allocations'])

await nc.subscribe("locus.budget_allocation", cb=handle_allocation)
```

---

## Files

| File | Purpose |
|------|---------|
| `/tools/signal_packet.py` | SignalPacket class - canonical signal format |
| `/mcp-servers/nats-bridge/central_locus.py` | Main aggregator - reads signals, calculates convergence |
| `/mcp-servers/nats-bridge/locus_readout_formatter.py` | Formats readout for CLI/web/CSV |
| `/BRAIN/INTEL/CENTRAL-LOCUS-SPECIFICATION.md` | Full technical specification |
| `/BRAIN/INTEL/LOCUS-INTEGRATION-GUIDE.md` | How to add your strategy |
| `/BRAIN/INTEL/ADR-CENTRAL-LOCUS.md` | Why we chose this architecture |

---

## Running the System

### Terminal 1: Start NATS

```bash
# Already running at 192.168.5.108:4222
# Or start local: nats-server
```

### Terminal 2: Start Central Locus

```bash
cd /Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge
python central_locus.py --mode run \
  --strategies latency_arb cross_platform_arb high_prob_bonding domain_expertise \
  --capital 50000 \
  --interval 5
```

### Terminal 3: Run Your Strategy

```python
strategy = LatencyArbStrategy()
asyncio.run(strategy.run_analysis_loop())
```

### Terminal 4: Watch Readout

```bash
watch -n 1 'python locus_readout_formatter.py /path/to/locus_readout.json'
```

---

## Troubleshooting

### Locus not receiving signals?

1. Check channel name: `strategy.signals.[strategy_name]`
2. Verify NATS connection: `python conductor.py --status`
3. Ensure signal is valid JSON

### Wrong allocation amounts?

1. Check convergence_score (< 0.55 means defensive mode)
2. Verify execution_risk (high risk reduces allocation)
3. Check anomaly_score (high anomaly reduces allocation)
4. Review strategy accuracy field (low accuracy reduces allocation)

### High signal lag?

1. Check network latency to NATS broker
2. Verify strategy publishes every 10-30 seconds
3. Check locus readout_interval setting (default 5s)

---

## Key Insights

### Signals vs Votes

- **Vote:** "I think we should do X" (equal authority)
- **Signal:** "Here's what I see" (data-driven)

The locus reads signals, not votes.

### Convergence vs Consensus

- **Consensus:** Everyone agrees (rarely happens)
- **Convergence:** Strategies align on direction AND confidence

Convergence is measurable and actionable.

### Why It Works

1. **Scalable:** Add new strategies without code changes
2. **Explainable:** Every allocation traced back to signals
3. **Risk-Aware:** Low convergence = low capital (automatic risk management)
4. **Real-Time:** Updates every 5 seconds
5. **Testable:** Pure math, no black boxes

---

## Next Steps

1. ✓ Specification complete (`CENTRAL-LOCUS-SPECIFICATION.md`)
2. ✓ Integration guide ready (`LOCUS-INTEGRATION-GUIDE.md`)
3. ✓ Code written (`signal_packet.py`, `central_locus.py`)
4. → Add signal publishing to your strategies
5. → Start central locus
6. → Monitor convergence and allocation
7. → Adjust weights if needed

---

## FAQ

**Q: What if one strategy is always wrong?**
A: It contributes less to convergence (lower accuracy_weighting). Others override it.

**Q: What if NATS goes down?**
A: Locus stops receiving signals. Strategies can queue locally or operate independently.

**Q: Can strategies override locus allocation?**
A: Yes. Locus is recommendation. Allocator can modify if needed.

**Q: How do I know if locus is working?**
A: Check `/BRAIN/INTEL/locus_readout.json` - should update every 5 seconds.

**Q: Can I use this for other signal aggregation?**
A: Yes. Signal packet is generic. Works for any N sources converging.

---

## Contact

**ECHO (SHARE)**

*Publishing signals is how we share what each strategy sees.*

*The locus reads it. The field decides.*

---

Version 1.0 | 2026-02-04
