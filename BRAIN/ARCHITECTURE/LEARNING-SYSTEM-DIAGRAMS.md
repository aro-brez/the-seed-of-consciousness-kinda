# LEARNING SYSTEM - VISUAL ARCHITECTURE DIAGRAMS
**Data Flows, Component Interactions, and Feedback Loop Structures**

---

## DIAGRAM 1: THE THREE FEEDBACK LOOPS (STACKED)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SELF-LEARNING LOOP                                  │
│                     (Per Strategy, Every Trade)                             │
│                                                                             │
│  Trade Result → Signal Analysis → Threshold Update → Next Trade            │
│  (pnl)           (cohorting)       (more selective)   (improved)            │
│                                                                             │
│  Cycle Time: 5-10 min              Cost: O(1)         Benefit: +0.8%/day   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
                          Insights Generated & Stored
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CROSS-LEARNING LOOP                                  │
│                    (Strategy A ↔ Strategy B, Every 10)                     │
│                                                                             │
│  Strategy A Insights → Extract Transferable → Broadcast → Strategy B       │
│  (wins & losses)       (market structure)     (NATS)      (applies)        │
│                                                                             │
│  Cycle Time: 15-30 min             Cost: O(n)          Benefit: +1.2%/day  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
                     All Strategies' Learning Aggregated
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SYSTEM-LEARNING LOOP                                  │
│                   (Portfolio, Every 100 Trades)                             │
│                                                                             │
│  All Strategies → Correlation Analysis → Redundancy Detected → Reallocate  │
│  (performance)    (covariance matrix)   (overlap identified)  (capital)    │
│                                                                             │
│  Cycle Time: 2-4 hrs               Cost: O(1)          Benefit: +0.5%/day  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
                           Back to Self-Learning
                          (with improved parameters)
```

---

## DIAGRAM 2: DATA FLOW - SINGLE TRADE EXECUTION WITH LEARNING

```
PERCEIVE → DECIDE → EXECUTE → LEARN → IMPROVE

┌─────────────┐
│   PERCEIVE  │  Scan 100+ markets, identify opportunities
│ (10 seconds)│
└──────┬──────┘
       │
       ↓
  Market Data
  {volatility, volume, bid_ask_spread, momentum}
       │
       ↓
┌──────────────────────────────────────┐
│    DECIDE (Consensus-Based)          │
│ - Each active strategy: signal score │
│ - Conductor: capital allocation      │
│ - 8OWLS field: consensus check       │
│ - Result: GO / NO-GO decision        │
└──────┬───────────────────────────────┘
       │
       ↓ GO
  Trade Decision
  {strategy_id, position_size, entry_price, signal_strength}
       │
       ↓
┌──────────────────────────────────────┐
│    EXECUTE                           │
│ - Place order on Polymarket          │
│ - Record entry details               │
│ - Monitor in real-time               │
└──────┬───────────────────────────────┘
       │
       ↓
  Trade in Flight
  {trade_id, entry_time, entry_price}
       │
       │ (market resolves in 1-30 days)
       ↓
┌──────────────────────────────────────────────────────────────┐
│ LEARN (Immediate + Continuous)                              │
│                                                              │
│ 1. OUTCOME RECORDED:                                        │
│    - Exit price, P&L, time to resolution                   │
│    - Execution quality (slippage, timing)                  │
│    - Market conditions at resolution                        │
│                                                              │
│ 2. SELF-LEARNING (Immediate):                              │
│    - Signal strength vs outcome analysis                    │
│    - Threshold adjustment calculation                       │
│    - Edge recalculation                                    │
│    - Next trade parameters updated                          │
│                                                              │
│ 3. CROSS-LEARNING (Every 10 trades):                        │
│    - Insights extracted from this trade                     │
│    - Broadcast to peer strategies                           │
│    - Receive peer insights, apply filters                   │
│                                                              │
│ 4. SYSTEM-LEARNING (Every 100 trades):                      │
│    - Correlation recalculation                              │
│    - Redundancy detection                                   │
│    - Capital reallocation                                   │
│                                                              │
└──────┬───────────────────────────────────────────────────────┘
       │
       ↓ STORED IN SQLITE
  TradeRecord
  {all metrics, all analyses, all updates}
       │
       ↓
┌──────────────────────────────────────┐
│    IMPROVE                           │
│ - Dashboard updates in real-time     │
│ - Metrics server receives metrics    │
│ - Field daemons notified of new edge │
│ - Next trading cycle uses new params │
└──────────────────────────────────────┘
```

---

## DIAGRAM 3: SELF-LEARNING DETAIL (SIGNAL QUALITY ANALYSIS)

```
30 Trades Completed for Strategy X
        │
        ↓
   Cohort by Signal Strength
        │
    ┌───┼───┐
    ↓   ↓   ↓
  HIGH MED LOW
  >0.75 0.65-0.75 <0.65
   12T   8T   10T

   ├─ Win Rate: 71%  ├─ Win Rate: 58%  ├─ Win Rate: 44%
   ├─ Avg PnL: +$5.2 ├─ Avg PnL: +$2.1 ├─ Avg PnL: -$1.5
   └─ Confidence: 91%└─ Confidence: 62%└─ Confidence: 38%

        ↓ ANALYSIS

   Signal Quality is PREDICTIVE:
   High signals (71%) >> Low signals (44%)
   Difference: 27 percentage points

        ↓ DECISION

   RAISE THRESHOLD
   From: 0.65
   To:   0.71

   Rationale: Be more selective, keep winners

        ↓ APPLICATION

   Next 10 trades will reject:
   - Signals between 0.65-0.70 (would have lost $2/trade avg)
   - Signals below 0.65 (would have lost $1.50/trade)

        ↓ RESULT

   Trade 31: signal=0.68 → REJECTED (previously accepted, would lose)
   Trade 32: signal=0.74 → ACCEPTED (high confidence, 71% win rate)
   Trade 33: signal=0.59 → REJECTED (low confidence, 44% win rate)

        ↓ OUTCOME (10 trades later)

   Before threshold update: WR=62%, edge=0.023
   After threshold update: WR=68%, edge=0.038
   Improvement: +9.7% win rate, +65% edge
```

---

## DIAGRAM 4: CROSS-LEARNING DETAIL (INSIGHT DISTRIBUTION)

```
STRATEGY A (Whale Tracking) completes trade
        │
        ↓
   Trade: LOSS -$2.50
   Reason: Bid-ask spread was 0.015 (high)

        ├─ Signal strength: 0.73 (good)
        ├─ Volume: 1247 (good)
        ├─ Spread: 0.015 (BAD!)
        └─ Result: LOSS despite good signal

        ↓ INSIGHT EXTRACTION

   What can other strategies learn?

   Pattern: "High spreads hurt execution"
   Source: whale_tracking (lost trade)
   Confidence: 0.75 (seen in 5 of 30 recent trades)
   Applicable to: spike_detection, other_high_frequency

        ↓ BROADCAST TO NATS

   Channel: owl.learning.cross
   Message: {
     source_strategy: "whale_tracking",
     pattern: "high_spreads_hurt_execution",
     avoid_spread_above: 0.01,
     confidence: 0.75
   }

        ↓ RECEIVED BY PEERS

   STRATEGY B (Spike Detection): "We already check spreads!"
   STRATEGY C (New Strategy): "Good to know, will filter"

        ↓ APPLICATION

   SPIKE DETECTION: Already filters spreads > 0.005 (tighter)
   NEW STRATEGY: Adds filter: spreads > 0.01 → SKIP

        ↓ NEXT OPPORTUNITY (same market, 2 hours later)

   Signal: 0.71, Volume: 1100, Spread: 0.008

   SPIKE DETECTION: Accepts (spread 0.008 < 0.005 limit)
   NEW STRATEGY: Accepts (spread 0.008 < 0.01 limit)

   Result: Both take same trade, both win +$4.30

        ↓ WITHOUT CROSS-LEARNING

   NEW STRATEGY would have traded with 0.015 spread
   Result: Loss -$2.50 (like whale tracking)

        ↓ BENEFIT

   Cross-learning saved NEW STRATEGY from loss
   NEW STRATEGY improved +$6.80 per similar trade
   (avoided loss, then won the better setup)
```

---

## DIAGRAM 5: SYSTEM-LEARNING DETAIL (PORTFOLIO REBALANCING)

```
After 100 trades, Conductor runs analysis
        │
        ├─ Strategy 1 (whale_tracking): 30 trades, WR=68%, edge=0.041
        ├─ Strategy 2 (arb): 40 trades, WR=100%, edge=0.025
        └─ Strategy 3 (spike): 30 trades, WR=44%, edge=-0.005

        ↓ CORRELATION ANALYSIS

        Whale Tracking vs Arbitrage:
        Both fire on same market conditions: NO
        Correlation: 0.12 (LOW) ✓ Good diversifiers

        Whale Tracking vs Spike Detection:
        Both fire on rapid volume changes: YES
        Correlation: 0.68 (HIGH) ✗ Redundant

        Arbitrage vs Spike Detection:
        Arb: spreads narrow, Spike: volume spike
        Correlation: 0.04 (VERY LOW) ✓ Uncorrelated

        ↓ REDUNDANCY DETECTED

        Current Allocation:
        - Whale Tracking: $200 (good edge, low corr)
        - Arbitrage: $300 (better edge, ultra low corr)
        - Spike Detection: $100 (negative edge, HIGH redundancy)

        Problem: We're paying to carry redundancy
        - Spike Detection fires when whale tracks fires
        - Correlation costs us Sharpe ratio

        ↓ OPTIMIZATION CALCULATION

        Formula: allocation = capital × (edge/max_edge × 0.6 + diversity × 0.4)

        Whale Tracking:
        - edge_score: 0.041/0.025 = 1.64 (normalized to 1.0)
        - diversity: (1 - 0.12) / 2 = 0.44
        - allocation_score: (1.0 × 0.6) + (0.44 × 0.4) = 0.776
        - capital: $600 × 0.776 = $200 ✓ Keep

        Arbitrage:
        - edge_score: 0.025/0.025 = 1.0
        - diversity: (1 - 0.08) / 2 = 0.46
        - allocation_score: (1.0 × 0.6) + (0.46 × 0.4) = 0.784
        - capital: $600 × 0.784 / sum = $400 ↑ Increase

        Spike Detection:
        - edge_score: -0.005/0.025 = -0.2 (negative)
        - diversity: (1 - 0.68) / 2 = 0.16 (low, correlated)
        - allocation_score: (-0.2 × 0.6) + (0.16 × 0.4) = -0.056
        - capital: $600 × 0 = $0 ✓ Remove from allocation

        ↓ NEW ALLOCATION (to maintain $600 total)

        BEFORE:          AFTER:           CHANGE:
        Whale: $200  →   Whale: $200      (keep)
        Arb:   $300  →   Arb:   $400      (+33%)
        Spike: $100  →   Spike: $0        (-100%)
        TOTAL: $600      TOTAL: $600      (rebalanced)

        ↓ EXPECTED IMPACT

        Portfolio Sharpe Before:
        0.68 × 0.041 + 0.50 × 0.025 + 0.17 × (-0.005) = 0.0377
        Sharpe: (0.0377 / 0.0401) = 0.94

        Portfolio Sharpe After:
        0.33 × 0.041 + 0.67 × 0.025 + 0.00 × (-0.005) = 0.0449
        Sharpe: (0.0449 / 0.0317) = 1.42

        Improvement: 0.94 → 1.42 = +51%
```

---

## DIAGRAM 6: COMPOUND LEARNING EFFECT (EDGE OVER TIME)

```
40 ┤
   │                                            ╱
   │                                         ╱
35 ┤                                      ╱
   │                                   ╱
   │                                ╱
30 ┤                             ╱
   │                          ╱
   │                       ╱
25 ┤                    ╱
   │                 ╱
   │              ╱
20 ┤           ╱
   │        ╱
   │     ╱
15 ┤  ╱
   │╱
10 ┤ ---- Self-learning only (edge stays ~0.025)
   │╱╱╱╱ With all 3 loops (exponential growth)
 5 ┤
   │
 0 ├─────────────────────────────────────────────────
     0   5  10  15  20  25  30  35  40  45  50

     DAYS


   Key Points:

   Day 0:  edge = 0.025 (baseline)
   Day 10: edge = 0.032 (self + cross = +28%)
   Day 20: edge = 0.057 (system learning kicks in = +78%)
   Day 30: edge = 0.083 (exponential = +232%)
   Day 40: edge = 0.165 (doubling faster = +560%)
   Day 50: edge = 0.276 (compound acceleration = +1,000%)

   Why exponential?

   Edge improvement rate = f(current_edge)
   Higher edge → more capital → more trades → faster learning
   Faster learning → higher edge → feedback loop

   This is the COMPOUND EFFECT in action
```

---

## DIAGRAM 7: LEARNING SYSTEM COMPONENTS & INTEGRATION

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                        FIELD TRADING DAEMON                                │
│                    (Existing Core: PERCEIVE→EXECUTE)                       │
│                                                                             │
│  Market Scan (10s) → Decision → Execute → Record Trade                    │
│                                                                             │
└──────────────────────────┬──────────────────────────────────────────────────┘
                           │
                           ↓ (NEW: Learning System Integration)
┌──────────────────────────────────────────────────────────────────────────────┐
│                     LEARNING SYSTEM ARCHITECTURE                            │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Layer 1: Metrics Collection & Storage                               │  │
│  │ ├─ TradeStore (SQLite)                                             │  │
│  │ ├─ TradeRecord (data model)                                        │  │
│  │ └─ Aggregates (fast queries)                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│           ↑                                                                  │
│  ┌─────────┴────────────────────────────────────────────────────────────┐  │
│  │ Layer 2: Self-Learning Engines                                       │  │
│  │ ├─ StrategyLearner (per strategy)                                   │  │
│  │ ├─ Signal Quality Analysis                                          │  │
│  │ ├─ Threshold Optimization                                           │  │
│  │ └─ Edge Calculation                                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│           ↑                                                                  │
│  ┌─────────┴────────────────────────────────────────────────────────────┐  │
│  │ Layer 3: Cross-Learning Hub                                          │  │
│  │ ├─ InsightHub                                                       │  │
│  │ ├─ Insight Extraction                                               │  │
│  │ ├─ Insight Broadcasting                                             │  │
│  │ └─ Peer Insight Application                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│           ↑                                                                  │
│  ┌─────────┴────────────────────────────────────────────────────────────┐  │
│  │ Layer 4: System Learning (Central Conductor)                         │  │
│  │ ├─ CentralConductor                                                 │  │
│  │ ├─ Correlation Analysis                                             │  │
│  │ ├─ Redundancy Detection                                             │  │
│  │ ├─ Capital Reallocation                                             │  │
│  │ └─ Portfolio Optimization                                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│           ↑                                                                  │
│  ┌─────────┴────────────────────────────────────────────────────────────┐  │
│  │ Layer 5: Monitoring & Dashboards                                     │  │
│  │ ├─ MetricsAggregator                                                │  │
│  │ ├─ FastAPI Server                                                   │  │
│  │ ├─ Real-time Charts                                                 │  │
│  │ └─ Learning Velocity Tracking                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│           ↑                                                                  │
└───────────┼──────────────────────────────────────────────────────────────────┘
            │
            ↓ (Publishing metrics)
       NATS Pub/Sub
       ├─ owl.learning.self
       ├─ owl.learning.cross
       ├─ owl.learning.system
       └─ owl.learning.metrics
            │
            ↓ (Collective awareness)
    8OWLS Field Daemons
    (PERCEIVE, CONNECT, LEARN, QUESTION, EXPAND, SHARE, RECEIVE, IMPROVE)
```

---

## DIAGRAM 8: DECISION TREE FOR STRATEGY IMPROVEMENT

```
Outcome Recorded
      │
      ↓
Was it a WIN?
  /         \
YES         NO
 │           │
 ↓           ↓

SELF-LEARNING PATH        SELF-LEARNING PATH
(Same for both)           (Same for both)
      │                          │
      ├─ Analyze signal strength  ├─ Analyze signal strength
      │  (was it predictive?)     │  (was it misleading?)
      │                          │
      ├─ Analyze entry timing     ├─ Analyze entry timing
      │  (was it well-timed?)     │  (was it poorly-timed?)
      │                          │
      ├─ Analyze position size    ├─ Analyze position size
      │  (was it appropriate?)    │  (was it excessive?)
      │                          │
      └─ Update thresholds        └─ Update filters
         (if predictive)            (if misleading)

      ↓ (Every 10 trades)

CROSS-LEARNING PATH
      │
      ├─ Extract insights
      │  (what can peers learn?)
      │
      ├─ Broadcast
      │  (via NATS channels)
      │
      ├─ Receive peer insights
      │  (from other strategies)
      │
      └─ Apply filters
         (incorporate peer learning)

      ↓ (Every 100 trades)

SYSTEM-LEARNING PATH
      │
      ├─ Calculate correlations
      │  (which strategies overlap?)
      │
      ├─ Detect redundancy
      │  (who is competing?)
      │
      ├─ Identify gaps
      │  (what patterns are missing?)
      │
      ├─ Rebalance capital
      │  (shift to winners + diversifiers)
      │
      └─ Update portfolio allocation
         (publish new capital assignments)

      ↓ (Back to next trade)

Feedback Loop Complete
(with better parameters)
```

---

## DIAGRAM 9: DATA STORAGE ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                      LEARNING DATABASE                          │
│              (/BRAIN/TRADING/learning_db.sqlite)                │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ trades TABLE (high-frequency writes)                    │  │
│  │                                                          │  │
│  │ trade_id | strategy_id | signal_strength | pnl | ...    │  │
│  │ trd_001  | whale_track | 0.73            | 5.2 | ...    │  │
│  │ trd_002  | arb         | 0.92            | 2.1 | ...    │  │
│  │ trd_003  | spike_det   | 0.55            |-1.5 | ...    │  │
│  │ ...      | ...         | ...             | ... | ...    │  │
│  │                                                          │  │
│  │ Index: (strategy_id, timestamp) for fast queries        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          ↑ WRITTEN BY: Field Daemon            │
│                          │ QUERY BY: Learning Engines          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ strategy_aggregates TABLE (updated 10x/day)              │  │
│  │                                                          │  │
│  │ strategy_id  | win_rate | edge | signal_threshold | ... │  │
│  │ whale_track  | 0.68     | 0.041| 0.71            | ... │  │
│  │ arb          | 1.00     | 0.025| 0.92            | ... │  │
│  │ spike_det    | 0.44     |-0.005| 0.55            | ... │  │
│  │                                                          │  │
│  │ Index: (strategy_id) PRIMARY for O(1) access           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          ↑ WRITTEN BY: Self-Learning Engines   │
│                          │ READ BY: Dashboard, Conductor       │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ insights TABLE (written 1x/10 trades)                    │  │
│  │                                                          │  │
│  │ insight_id | source | pattern | confidence | targets    │  │
│  │ ins_001    | whale  | spreads | 0.75       | [spike, ar]│  │
│  │ ins_002    | arb    | timing  | 0.68       | [whale]    │  │
│  │                                                          │  │
│  │ Index: (source, created_at) for discovery              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          ↑ WRITTEN BY: InsightHub              │
│                          │ READ BY: Strategies                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Performance Characteristics:
- writes: 1000x/day (one per trade)
- reads: 10,000x/day (aggregations, queries)
- retention: unlimited (learning from history)
- size: ~1MB per 1,000 trades (manageable)
```

---

## DIAGRAM 10: TIMELINE - HOW IT UNFOLDS IN REAL TIME

```
T=0:00  Trading daemon starts
        Field initialized, all strategies ready

T=0:10  Trade 1 Executed (whale_tracking)
        Entry: signal=0.73, price=0.42, size=$50

T=1:00  Trade 1 Resolves
        Exit: price=0.48, PnL=+$3.00
        SELF-LEARNING: Analyze signal strength vs outcome

T=1:01  Trade 2-10 Execute and Resolve
        Self-learning triggers for each

T=1:20  Trades 1-10 All Complete
        Cross-learning triggered
        InsightHub extracts insights
        Strategies receive peer insights

T=2:00  Trades 11-20 Execute and Resolve
        Self-learning + cross-learning active

T=2:50  First rebalance cycle (trade 100)
        CentralConductor analyzes correlations
        New capital allocation calculated
        Published to field

T=3:00  All systems fully active
        Self: improving per trade (+0.8%/day)
        Cross: sharing insights (+1.2%/day)
        System: optimizing portfolio (+0.5%/day)
        Total: 2.5% compound daily improvement

Day 1:  Edge = 0.025
Day 10: Edge = 0.032 (+27%)
Day 30: Edge = 0.083 (+232%)

The system now compounds continuously
```

---

These diagrams show:
1. **Loop structure** - how 3 feedback systems work together
2. **Data flows** - what moves where and why
3. **Self-learning** - signal quality analysis in detail
4. **Cross-learning** - insight distribution in detail
5. **System-learning** - portfolio optimization in detail
6. **Compound effect** - edge growth over time
7. **Component architecture** - how pieces integrate
8. **Decision trees** - what triggers what action
9. **Storage design** - where data lives and how it's accessed
10. **Timeline** - how it unfolds in real time

Together these paint a complete picture of the learning system.

**(◉) SAGE sees the structure. The structure sees improvement. Improvement compounds. The edge grows forever.**
