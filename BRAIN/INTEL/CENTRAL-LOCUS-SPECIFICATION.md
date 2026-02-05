# CENTRAL LOCUS - Signal Aggregation & Budget Allocation System

**ECHO (SHARE) Specification Document**
**Date: 2026-02-04**
**Version: 1.0**

---

## THE VISION

A real-time signal aggregation system that:
1. Collects signals from N parallel trading strategies via NATS pub/sub
2. Calculates convergence score across strategies
3. Outputs budget allocation recommendations based on consensus
4. Visualizes strategy alignment and confidence in real-time
5. Feeds allocation decisions back to capital allocator

**Core Insight:** Strategies don't vote or debate. They SIGNAL. The locus reads signals and acts.

---

## ARCHITECTURE

### Layer 1: Signal Producers (Strategies)

Each strategy publishes **signal packets** to NATS:

```
NATS Channel: strategy.signals.[strategy_name]

Example: strategy.signals.latency_arb
         strategy.signals.cross_platform_arb
         strategy.signals.high_prob_bonding
         strategy.signals.domain_expertise
         strategy.signals.discovery_scanner
```

### Layer 2: Central Locus (Aggregator)

The locus subscribes to ALL strategy signal channels and:
1. Buffers incoming signals (time window: 5-30 seconds)
2. Calculates convergence metrics
3. Generates budget allocation recommendations
4. Publishes aggregated readout

### Layer 3: Budget Allocator (Consumer)

Receives aggregated readout and:
1. Executes capital allocation decisions
2. Feeds back execution status to locus
3. Logs allocation history

---

## SIGNAL SPECIFICATION

### 1. What Each Strategy Publishes

Each strategy emits a **Signal Packet** every N seconds (configurable, default 10s):

```json
{
  "timestamp": "2026-02-04T10:30:45.123Z",
  "strategy": "latency_arb",
  "signal_version": "1.0",

  "market_view": {
    "confidence": 0.87,
    "direction": "UP",
    "strength": 0.95,
    "liquidity_score": 0.72,
    "volatility": 0.18
  },

  "position_recommendation": {
    "action": "BUY",
    "suggested_size_bps": 150,
    "max_size_bps": 200,
    "entry_price_range": [0.42, 0.48],
    "expected_return_pct": 2.5,
    "win_probability": 0.92
  },

  "performance_context": {
    "recent_accuracy": 0.88,
    "sharpe_ratio": 2.4,
    "max_drawdown_pct": -3.2,
    "days_active": 12,
    "trades_closed": 47
  },

  "risk_assessment": {
    "edge_confidence": 0.78,
    "model_confidence": 0.91,
    "execution_risk": "low",
    "market_regime": "trending",
    "anomaly_score": 0.12
  },

  "metadata": {
    "version": "v2.1",
    "uptime_pct": 99.3,
    "last_signal_drift": 2.5,
    "pending_orders": 3,
    "allocation_utilization_pct": 65
  }
}
```

### 2. Signal Dimensions (Axes for Convergence)

The Central Locus tracks these 7 dimensions:

| Dimension | Range | Meaning |
|-----------|-------|---------|
| **Confidence** | 0.0-1.0 | How sure is the strategy? |
| **Direction** | UP/DOWN/NEUTRAL | Which way should we lean? |
| **Strength** | 0.0-1.0 | How strong is the conviction? |
| **Accuracy** | 0.0-1.0 | Historical prediction accuracy |
| **Allocation_Request** | 0-1.0 | What % of capital does it want? |
| **Risk** | LOW/MED/HIGH | Perceived execution risk |
| **Recency** | seconds | How fresh is this signal? |

---

## AGGREGATION ALGORITHM

### Step 1: Buffer & Weight Signals

```
time_window = 10 seconds (configurable)

For each strategy:
  - Collect all signals in the window
  - Keep ONLY the most recent from each strategy
  - Weight by recency (exponential decay, λ=0.7)
```

### Step 2: Convergence Scoring

Calculate how much strategies agree:

```python
# DIRECTIONAL CONVERGENCE
consensus_direction = weighted_mean(signal.direction for all signals)
# Result: UP (>0.6), DOWN (<-0.6), NEUTRAL (else)
direction_convergence = abs(consensus_direction)

# CONFIDENCE CONVERGENCE
mean_confidence = weighted_mean(signal.confidence)
confidence_std = weighted_std(signal.confidence)
confidence_convergence = 1.0 - (confidence_std / (mean_confidence + ε))

# STRENGTH CONVERGENCE
mean_strength = weighted_mean(signal.strength)
strength_convergence = mean_strength  # Direct

# ACCURACY WEIGHTED CONSENSUS
accuracy_weighted_confidence = weighted_mean(
  signal.confidence * signal.performance_context.recent_accuracy
  for all signals
)

# COMPOSITE CONVERGENCE SCORE
convergence = (
  0.3 * direction_convergence +
  0.3 * confidence_convergence +
  0.25 * strength_convergence +
  0.15 * accuracy_weighted_confidence
)
# Result: 0.0 (fragmented) to 1.0 (unified)
```

### Step 3: Allocation Recommendation

Based on convergence, generate budget allocation:

```python
if convergence >= 0.85:
  allocation_mode = "AGGRESSIVE"
  # All agreeing, concentrated bets

elif convergence >= 0.70:
  allocation_mode = "BALANCED"
  # Good agreement, balanced sizing

elif convergence >= 0.55:
  allocation_mode = "CAUTIOUS"
  # Moderate disagreement, smaller sizes

else:
  allocation_mode = "DEFENSIVE"
  # No consensus, minimal capital
```

### Step 4: Per-Strategy Allocation

For each strategy:

```
# Base allocation (if convergence permits)
base_allocation = (
  signal.market_view.confidence * 0.4 +
  signal.performance_context.recent_accuracy * 0.3 +
  (1.0 - signal.risk_assessment.anomaly_score) * 0.3
) * total_capital

# Mode adjustment
allocation = base_allocation * mode_multiplier[allocation_mode]

# Risk adjustment
if signal.risk_assessment.execution_risk == "high":
  allocation *= 0.6
elif signal.risk_assessment.execution_risk == "med":
  allocation *= 0.8

# Utilization cap
max_allowed = signal.position_recommendation.max_size_bps / 10000 * total_capital
allocation = min(allocation, max_allowed)

return allocation
```

---

## OUTPUT SPECIFICATION

### 1. Central Locus Readout (Published every 5 seconds)

```json
{
  "timestamp": "2026-02-04T10:30:50.000Z",
  "epoch": 1234,

  "market_consensus": {
    "direction": "UP",
    "confidence": 0.82,
    "strength": 0.79,
    "convergence_score": 0.78,
    "convergence_level": "BALANCED"
  },

  "strategy_alignment": {
    "num_active_strategies": 4,
    "num_aligned_up": 3,
    "num_aligned_down": 0,
    "num_neutral": 1,
    "alignment_matrix": {
      "latency_arb": { "direction": "UP", "confidence": 0.87, "alignment": 0.95 },
      "cross_platform": { "direction": "UP", "confidence": 0.79, "alignment": 0.88 },
      "high_prob_bonding": { "direction": "UP", "confidence": 0.80, "alignment": 0.89 },
      "domain_expertise": { "direction": "NEUTRAL", "confidence": 0.71, "alignment": 0.42 }
    }
  },

  "aggregate_metrics": {
    "mean_confidence": 0.79,
    "confidence_std_dev": 0.06,
    "mean_accuracy": 0.84,
    "mean_sharpe": 2.31,
    "uptime_pct": 98.6
  },

  "budget_allocation": {
    "mode": "BALANCED",
    "total_capital": 50000,
    "timestamp_generated": "2026-02-04T10:30:50.000Z",
    "allocations": {
      "latency_arb": {
        "capital": 18500,
        "pct": 0.37,
        "confidence": 0.87,
        "expected_return": 2.1,
        "max_size": 24000,
        "utilization": 0.77
      },
      "cross_platform": {
        "capital": 14200,
        "pct": 0.28,
        "confidence": 0.79,
        "expected_return": 1.8,
        "max_size": 16500,
        "utilization": 0.86
      },
      "high_prob_bonding": {
        "capital": 12100,
        "pct": 0.24,
        "confidence": 0.80,
        "expected_return": 1.2,
        "max_size": 15000,
        "utilization": 0.81
      },
      "domain_expertise": {
        "capital": 5200,
        "pct": 0.10,
        "confidence": 0.71,
        "expected_return": 2.5,
        "max_size": 8000,
        "utilization": 0.65
      }
    }
  },

  "convergence_analysis": {
    "convergence_trend": "improving",
    "epochs_stable": 12,
    "last_divergence_epoch": 3,
    "risk_alert": null,
    "opportunity_score": 0.78
  },

  "execution_readiness": {
    "all_signals_fresh": true,
    "min_signal_age_sec": 0.5,
    "max_signal_age_sec": 4.2,
    "ready_for_execution": true,
    "execution_confidence": 0.91
  }
}
```

### 2. Human-Readable Summary

```
═══════════════════════════════════════════════════════════════════
CENTRAL LOCUS READOUT - Epoch 1234 (10:30:50 UTC)
═══════════════════════════════════════════════════════════════════

🎯 MARKET CONSENSUS
   Direction: ↑ UP (82% confident)
   Strength: 79% | Convergence: 78% (BALANCED)

📊 STRATEGY ALIGNMENT
   ✓ Latency Arb        →UP (87%)  | Aligned: 95% | Edge: High
   ✓ Cross-Platform Arb →UP (79%)  | Aligned: 88% | Edge: Strong
   ✓ High-Prob Bonding  →UP (80%)  | Aligned: 89% | Edge: Strong
   ~ Domain Expertise   →NEUTRAL (71%) | Aligned: 42% | Edge: Moderate

📈 AGGREGATE METRICS
   Mean Confidence: 79% | Std Dev: 6%
   Mean Accuracy: 84% | Mean Sharpe: 2.31x
   System Uptime: 98.6%

💰 BUDGET ALLOCATION (Total: $50,000)
   Latency Arb         $18,500 (37%) | Confidence: 87% | Expected: +2.1%
   Cross-Platform Arb  $14,200 (28%) | Confidence: 79% | Expected: +1.8%
   High-Prob Bonding   $12,100 (24%) | Confidence: 80% | Expected: +1.2%
   Domain Expertise    $ 5,200 (10%) | Confidence: 71% | Expected: +2.5%

⚡ EXECUTION READINESS: READY ✓
   Min Signal Age: 0.5s | Max Signal Age: 4.2s
   Execution Confidence: 91%

═══════════════════════════════════════════════════════════════════
```

### 3. Machine-Actionable Commands

```python
{
  "command": "REALLOCATE_CAPITAL",
  "allocations": {
    "latency_arb": 18500,
    "cross_platform_arb": 14200,
    "high_prob_bonding": 12100,
    "domain_expertise": 5200
  },
  "metadata": {
    "convergence_score": 0.78,
    "epoch": 1234,
    "execution_confidence": 0.91,
    "timestamp": "2026-02-04T10:30:50.000Z"
  }
}
```

---

## REAL-TIME VISUALIZATION

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│ CONVERGENCE GAUGE              │ DIRECTION CONSENSUS        │
│  ██████████░░░░  78%           │  ↑ UP  79% ↓ 21%           │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ STRATEGY SIGNALS (Real-time)                                 │
├──────────────────────────────────────────────────────────────┤
│ latency_arb:        ████████░░ 87% confidence | Up  | +2.1% │
│ cross_platform:     ███████░░░ 79% confidence | Up  | +1.8% │
│ high_prob_bonding:  ███████░░░ 80% confidence | Up  | +1.2% │
│ domain_expertise:   ██████░░░░ 71% confidence | ↔ | +2.5% │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ CAPITAL ALLOCATION                                           │
├──────────────────────────────────────────────────────────────┤
│ latency_arb        ████████████░░░░░░░░ 37% ($18,500)       │
│ cross_platform     ████████░░░░░░░░░░░░ 28% ($14,200)       │
│ high_prob_bonding  ████████░░░░░░░░░░░░ 24% ($12,100)       │
│ domain_expertise   ██░░░░░░░░░░░░░░░░░░ 10% ($5,200)        │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ CONVERGENCE TREND (Last 100 epochs)                          │
│                    ╱╲    ╱╲                                   │
│         ╱╲  ╱╲  ╱╲╱  ╲╱╲╱  ╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲                │
│   ╱╲╱╲╱  ╲╱  ╲╱                                              │
│  Trend: Stabilizing ✓  | Volatility: 12% | Drift: 1.2%     │
└──────────────────────────────────────────────────────────────┘
```

---

## NATS CHANNEL TOPOLOGY

### Publisher Channels

```
strategy.signals.latency_arb           ← Published by latency_arb strategy
strategy.signals.cross_platform_arb    ← Published by cross_platform strategy
strategy.signals.high_prob_bonding     ← Published by high_prob_bonding
strategy.signals.domain_expertise      ← Published by domain_expertise
strategy.signals.discovery_scanner     ← Published by discovery scanner
...
strategy.signals.[name]                ← Generic pattern for all strategies
```

### Aggregator Channels

```
locus.aggregated_readout               ← Central Locus publishes consolidated view
locus.budget_allocation                ← Budget allocation commands
locus.convergence_metrics              ← Convergence scoring detail
locus.alerts                           ← Risk/opportunity alerts
```

### Consumer Channels

```
allocator.status.[strategy]            ← Capital allocator publishes execution status
allocator.confirmed_allocation         ← Confirmation of allocation executed
```

---

## IMPLEMENTATION ROADMAP

### Phase 1: Signal Infrastructure (Week 1)

- [ ] Define Signal Packet schema (JSON)
- [ ] Build signal publisher decorator for strategies
- [ ] Create test signal generator (mock strategies)
- [ ] Verify NATS pub/sub connectivity
- [ ] Document signal format and examples

### Phase 2: Central Locus Core (Week 2)

- [ ] Build signal subscriber and buffer
- [ ] Implement convergence scoring algorithm
- [ ] Build allocation calculator
- [ ] Create readout generator
- [ ] Unit tests for aggregation logic

### Phase 3: Output & Visualization (Week 3)

- [ ] Build dashboard renderer (web + CLI)
- [ ] Real-time NATS message streaming
- [ ] Human-readable formatting
- [ ] Machine-actionable command generation
- [ ] Convergence trend tracking

### Phase 4: Integration & Optimization (Week 4)

- [ ] Hook into existing strategy coordinator
- [ ] Feed allocations to capital allocator
- [ ] Performance monitoring and alerting
- [ ] Stress testing (N strategies, high frequency)
- [ ] Documentation and runbooks

---

## KEY DESIGN PRINCIPLES

1. **Signal, Not Vote**: Strategies publish signals (data), not votes (opinions)
2. **Convergence-Driven**: Allocation follows consensus, not individual strategy requests
3. **Weighted by Performance**: Historical accuracy weights current signals
4. **Real-Time**: Readout updates every 5 seconds with fresh signals
5. **Transparent**: Every decision is explainable and auditable
6. **Resilient**: Missing signals don't break aggregation (weighted averaging)
7. **Human-Readable**: Non-technical stakeholders understand the output
8. **Machine-Actionable**: Systems can automatically execute recommendations

---

## MONITORING & ALERTING

### Key Metrics to Track

- **Signal Freshness**: Age of oldest signal in current readout
- **Convergence Velocity**: Rate of convergence score change
- **Allocation Drift**: Deviation from target allocations
- **Strategy Disagreement**: When strategies diverge dangerously
- **Risk Score**: Anomaly detection across signal dimensions

### Alert Triggers

```
1. CONVERGENCE_DROP: convergence < 0.50 (fragmented)
2. STALE_SIGNALS: max_age > 30 seconds (communication issue)
3. EXTREME_ALLOCATION: single strategy > 50% (concentration risk)
4. STRATEGY_BLACKOUT: no signal from strategy > 60 seconds
5. ACCURACY_DROP: recent_accuracy declines >10% (model degradation)
6. REGIME_CHANGE: volatility spikes >0.5 (market shift detected)
```

---

## EXTENSIBILITY

### Adding a New Strategy

1. Strategy publishes to `strategy.signals.[name]` with Signal Packet schema
2. Locus automatically starts collecting and weighting signals
3. No code changes needed (plug-and-play)

### Custom Convergence Metrics

Can define different convergence formulas for different market regimes:
- Trending markets: weight direction_convergence higher
- Range-bound: weight strength_convergence higher
- Volatile: weight risk assessment higher

---

## EDGE CASES & ROBUSTNESS

### Handling Missing Signals

```
If strategy N is silent for >10 seconds:
- Drop from convergence calculation
- Reduce allocation to zero gradually (5-second ramp)
- Alert monitoring system
- Continue aggregating other strategies (N-1)
```

### Handling Divergent Signals

```
If std_dev(confidence) > 0.3:
- Convergence score penalized by (std_dev * 0.5)
- Allocation mode shifts toward CAUTIOUS
- Increase execution_confidence threshold
```

### Handling Signal Bursts

```
Queue max size: 5000 packets per strategy
If exceeded:
- Keep only most recent signal
- Log warning
- Increase buffer time window to 15s
- Alert ops
```

---

## SUCCESS CRITERIA

By end of Phase 4, the Central Locus should:

✓ Collect signals from 4+ strategies in real-time
✓ Calculate convergence scores with 95%+ accuracy
✓ Generate allocation recommendations within 100ms
✓ Update visualization every 5 seconds
✓ Support up to 100 signals/second throughput
✓ Handle strategy blackouts gracefully
✓ Provide audit trail of all allocation decisions
✓ Integrate seamlessly with existing capital allocator

---

## TECHNICAL DETAILS

### Technology Stack

- **Language**: Python 3.9+
- **Messaging**: NATS (pub/sub)
- **Data Format**: JSON
- **Visualization**: Web dashboard (React/Vue) + CLI (rich)
- **Storage**: JSON files + optional Redis for performance
- **Testing**: pytest + mock NATS

### Dependencies

```
nats-py==2.4.2
anthropic==0.28.1
rich==13.7.0
pydantic==2.6.0
pandas==2.0.0
numpy==1.26.0
```

---

## SIGNATURE

**ECHO (SHARE)**
*The owl who brings collective wisdom to the locus of decision.*

"I publish what each knows. The locus reads it. The field decides."

---

END OF SPECIFICATION
