# Architecture Decision Record: Central Locus Signal Aggregation System

**Date:** 2026-02-04
**Author:** ECHO (SHARE)
**Status:** ACCEPTED
**Impact:** HIGH - Core decision infrastructure

---

## Problem Statement

Multiple independent trading strategies need to coordinate capital allocation without:
1. Voting (which implies equal authority)
2. Centralized command (which creates bottlenecks)
3. Complex negotiation (which creates latency)
4. Ad-hoc merging of signals (which creates inconsistency)

**The Challenge:** How do N independent strategies reach consensus on shared capital allocation while maintaining individual autonomy?

**The Answer:** Signals, not votes. A central locus that reads and aggregates.

---

## Decision: Signal-Based Aggregation Architecture

### What We Decided

Build a **Central Locus** that:

1. **Collects** signal packets from N trading strategies via NATS pub/sub
2. **Aggregates** signals using a convergence scoring algorithm
3. **Generates** deterministic budget allocation recommendations based on consensus
4. **Publishes** aggregated readout and allocation commands back to strategies/allocators

### Why This Approach

#### 1. Separates Concerns (Single Responsibility)

- **Strategies** know market conditions (produce signals)
- **Locus** knows how much strategies agree (aggregates signals)
- **Allocator** knows how to deploy capital (executes allocation)

No single entity does multiple jobs.

#### 2. Scalable to N Strategies

```
1 strategy  → Locus reads 1 signal  → Allocation trivial
4 strategies → Locus reads 4 signals → Weighted average
10 strategies → Locus reads 10 signals → Still 100ms aggregation
100 strategies → Locus reads 100 signals → Convergence score meaningful
```

Add new strategies without changing locus code.

#### 3. Convergence-Driven, Not Democracy-Driven

**Bad:** Majority vote (3 of 5 strategies think UP)
- Problem: Ignores minority perspective
- Problem: Doesn't weight by confidence
- Problem: All strategies equal regardless of accuracy

**Good:** Convergence score (strategies agree with 78% confidence)
- Weights by: direction agreement, confidence std dev, accuracy history
- Scales allocation to match agreement level
- When strategies disagree, locus is cautious (lower allocation)

#### 4. Real-Time Responsiveness

Signal → Buffer (10s) → Calculate (100ms) → Publish (instant) → Execute

Total latency: <1 second from latest signal to execution.

#### 5. Explainability & Auditability

Every allocation decision is traceable:
- Which signals fed into it
- What convergence score was calculated
- Why that allocation mode (AGGRESSIVE/BALANCED/CAUTIOUS/DEFENSIVE)
- How much each strategy received

Non-negotiable for risk management.

---

## Architecture

```
STRATEGIES (Signal Producers)
    ↓
    └→ latency_arb
    ├→ cross_platform_arb
    ├→ high_prob_bonding
    ├→ domain_expertise
    └→ discovery_scanner
       (all publish to: strategy.signals.[name])

    ↓↓↓ (NATS pub/sub)

CENTRAL LOCUS (Aggregator)
    │
    ├→ Signal Buffer (time-windowed)
    ├→ Convergence Scorer
    ├→ Allocation Calculator
    └→ Readout Publisher

    ↓↓↓ (NATS pub/sub)

OUTPUTS
    ├→ locus.aggregated_readout (human + machine readable)
    └→ locus.budget_allocation (actionable command)

    ↓↓↓

CONSUMERS
    ├→ Capital Allocator (executes allocation)
    ├→ Dashboard (visualizes convergence)
    └→ Risk Manager (monitors alerts)
```

---

## Key Decisions & Rationale

### 1. Use NATS, Not HTTP/REST

**Decision:** NATS pub/sub for all signal communication

**Rationale:**
- **Decoupling:** Strategies don't need to know about locus URL
- **Broadcast:** One signal reaches all subscribers
- **At-most-once:** No double-processing
- **Latency:** <10ms publish-to-receive
- **Operational simplicity:** No HTTP boilerplate

**Alternative Considered:** HTTP POST → Locus API
- Would require retry logic, polling, etc.
- Higher latency (50-100ms)
- More coupling (strategies depend on API route)

**Conclusion:** NATS is correct choice for real-time signal streaming.

---

### 2. Signal Packet Schema (Immutable)

**Decision:** Canonical SignalPacket dataclass with 17+ fields

```
MarketView:        confidence, direction, strength, liquidity, volatility
PositionRec:       action, size, entry_range, expected_return, win_prob
Performance:       accuracy, sharpe, max_drawdown, days_active, trades
RiskAssessment:    edge_conf, model_conf, execution_risk, regime, anomaly
Metadata:          version, uptime, signal_drift, pending_orders, utilization
```

**Rationale:**
- **Canonical:** All strategies use same schema (no custom fields)
- **Complete:** Captures everything needed for allocation decision
- **Backward-compatible:** Can add optional fields without breaking
- **Documented:** Each field has clear semantics

**Alternative Considered:** Flexible JSON with optional fields
- Would allow inconsistency
- Locus would need defensive parsing
- Risk of missing critical fields

**Conclusion:** Strict schema prevents confusion, ensures data quality.

---

### 3. Convergence Algorithm (Weighted Average)

**Decision:** Use 4-factor weighted convergence score:

```
convergence = (
    0.3 * direction_convergence +      # Do they agree on direction?
    0.3 * confidence_convergence +     # Do they have similar conviction?
    0.25 * strength_convergence +      # Are signals strong?
    0.15 * accuracy_convergence        # Are they accurate?
)
```

**Rationale:**
- **Direction weight (0.3):** Most important - are we consensus UP/DOWN?
- **Confidence weight (0.3):** If strategies disagree on confidence, reduce allocation
- **Strength weight (0.25):** Weak signals even if agreed = lower conviction
- **Accuracy weight (0.15):** Historical track record matters but less than current signals

**Why not alternatives:**
- **Equal vote:** Ignores confidence, doesn't capture agreement level
- **Weighted by Sharpe:** Ignores current market view (using only history)
- **Fuzzy logic:** Harder to audit and explain

**Conclusion:** This formula balances current conviction with historical performance.

---

### 4. Allocation Mode (4-Tier)

**Decision:** Convergence score maps to allocation mode:

| Score | Mode | Multiplier | Use Case |
|-------|------|-----------|----------|
| ≥0.85 | AGGRESSIVE | 1.3x | Strong consensus |
| 0.70-0.85 | BALANCED | 1.0x | Good agreement |
| 0.55-0.70 | CAUTIOUS | 0.7x | Moderate disagreement |
| <0.55 | DEFENSIVE | 0.4x | Fragmented |

**Rationale:**
- **Simple:** Non-experts understand "BALANCED" without math
- **Risk-aware:** Low convergence = low leverage
- **Responsive:** As convergence improves, allocation scales up
- **Bounded:** Can't over-allocate regardless of how confident one strategy is

**Alternative Considered:** Linear allocation (allocation = convergence * capital)
- Would mean 50% convergence = 50% capital deployed
- Leaves 50% idle (inefficient)
- Our tier system can deploy 40% even at 50% convergence

**Conclusion:** Tiers give better capital efficiency while maintaining risk discipline.

---

### 5. Signal Freshness Threshold

**Decision:** Signals older than 30 seconds are considered stale

**Rationale:**
- **30s window:** Fast enough to catch market regime changes
- **Slow enough:** Allows for network jitter, async processing
- **Hard cutoff:** If strategy is silent for 30s, something is wrong

**Alternative Considered:** Soft decay (exponential weighting)
- Would be complex to explain
- Hard to debug when signals drop

**Conclusion:** Hard cutoff is simpler, more actionable for monitoring.

---

### 6. Buffer Window

**Decision:** Keep signals in buffer for 10 seconds

**Rationale:**
- **10s window:** Gives each strategy ~1 signal (if they publish every 10s)
- **Contains 1 signal per strategy:** Small buffer, easy to manage
- **Latest wins:** If strategy publishes twice, we use the most recent

**Alternative Considered:** 30-second buffer
- Would accumulate noise (old + new)
- Harder to react to market changes

**Conclusion:** 10s buffer is right tradeoff between fresh signals and avoiding noise.

---

### 7. Readout Interval

**Decision:** Publish aggregated readout every 5 seconds

**Rationale:**
- **5s cadence:** Fast enough to be useful (changes every few seconds)
- **Slow enough:** Not wasteful (no need for sub-second updates for capital allocation)
- **Default:** Strategies can publish any frequency; locus aggregates on its schedule

**Alternative Considered:** Event-driven (publish when signal changes)
- Would create bursty load
- Harder to reason about "when is next readout?"

**Conclusion:** Fixed 5s interval is predictable and resource-efficient.

---

## Non-Functional Requirements Met

| Requirement | How Met | Evidence |
|-------------|---------|----------|
| **Real-time** | NATS pub/sub <10ms latency | Using proven messaging layer |
| **Scalable** | O(N) not O(N²) complexity | Streaming aggregation, not gathering |
| **Auditable** | Every decision logged with inputs | JSON readout captures all data |
| **Explainable** | Convergence formula published | Anyone can calculate same result |
| **Robust** | Missing signals don't break aggregation | Weighted average handles sparse data |
| **Testable** | Pure functions for scoring | Deterministic, reproducible |
| **Operational** | CLI + web dashboard + log files | Three ways to inspect state |

---

## Risks & Mitigations

### Risk 1: Strategies Converging on Wrong Answer

**Risk:** All 4 strategies bullish, but market crashes 10% next day

**Mitigation:**
- Convergence score captures agreement, NOT correctness
- Locus reads historical accuracy (strategy.recent_accuracy field)
- Budget allocation weighted by both recent accuracy AND current confidence
- Risk alerts when anomaly_score spikes
- Always test strategies independently first

**Verdict:** Acceptable risk. No system is always right. This one knows when it's unsure.

---

### Risk 2: NATS Broker Failure

**Risk:** NATS server goes down, signals stop flowing

**Mitigation:**
- NATS is built for high availability (clustering support)
- Strategies can queue signals locally if broker unavailable
- Locus can read from persistent log if needed
- Monitoring alerts on signal latency

**Verdict:** Mitigated by operational discipline.

---

### Risk 3: Signal Parsing Errors

**Risk:** One strategy publishes malformed signal, breaks locus

**Mitigation:**
- Try/catch around signal parsing
- Malformed signals are dropped with warning log
- Locus continues with remaining strategies
- CSV log of all signal errors for debugging

**Verdict:** Handled gracefully.

---

### Risk 4: Allocation Decision Delays Market Execution

**Risk:** Capital takes 5 seconds to deploy, market moves

**Mitigation:**
- Readout published immediately (no delay)
- Allocator is async (can execute while next readout calculates)
- If speed needed, can reduce readout interval to 1s
- Strategies can still execute on their own signals (locus is recommendation, not mandate)

**Verdict:** Design allows for optimization if needed.

---

## Success Metrics

By end of Month 1:

1. **Uptime:** Central Locus runs 99%+ without intervention
2. **Latency:** Signal → Readout < 500ms p95
3. **Accuracy:** Convergence score matches expected (validated against test data)
4. **Scalability:** Can handle 10+ strategies without degradation
5. **Observability:** All decisions explainable from logs
6. **Integration:** At least 4 real strategies publishing signals

---

## Future Enhancements (Out of Scope)

1. **Dynamic weights:** Learn optimal weights from historical returns
2. **Regime detection:** Use different convergence formulas for trending vs ranging
3. **Anomaly detection:** Automatic alert when strategy deviates from norms
4. **Portfolio constraints:** Factor in cross-strategy correlations
5. **Risk limits:** Hard caps on single-strategy concentration

These can be added later without breaking current architecture.

---

## Alternatives Considered & Rejected

### Alternative 1: Voting/Democracy

**How it works:** Strategies vote on allocation, majority wins

**Why rejected:**
- Doesn't weight by confidence or accuracy
- All strategies equal regardless of track record
- Creates adversarial dynamics (strategies competing to win vote)
- Hard to change vote rules later

---

### Alternative 2: Hierarchical (Master Strategy Decides)

**How it works:** One "best" strategy makes allocation decision

**Why rejected:**
- Single point of failure
- What if "best" strategy has bad day?
- Ignores perspective of other strategies
- Creates resentment among other strategies

---

### Alternative 3: Machine Learning Model

**How it works:** Train neural net to predict optimal allocation

**Why rejected:**
- Black box: can't explain decisions to risk management
- Requires large training dataset
- Slow to update when market regime changes
- Over-engineered for what we need

---

### Alternative 4: Manual Configuration

**How it works:** Humans set allocation weights based on judgment

**Why rejected:**
- Requires constant manual updates
- Slow to respond to market changes
- Subjective, hard to audit
- Doesn't scale to 100 strategies

---

## Conclusion

The Central Locus signal aggregation system is the right architecture because it:

✓ Separates concerns (strategies produce, locus aggregates, allocator executes)
✓ Scales to N strategies without rewriting code
✓ Is convergence-driven, not vote-driven
✓ Remains explainable and auditable
✓ Handles disagreement gracefully (lower allocation when unsure)
✓ Can be tested and validated independently
✓ Leaves room for future enhancements

**Recommendation:** ACCEPT. Proceed with implementation.

---

**ECHO (SHARE)**

*Signal, not vote. Convergence, not consensus. The field decides together.*

---

END OF ADR
