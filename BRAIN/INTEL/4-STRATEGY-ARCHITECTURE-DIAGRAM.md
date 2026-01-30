# 4-STRATEGY ARCHITECTURE - VISUAL DIAGRAM

```
╔══════════════════════════════════════════════════════════════════╗
║                   STRATEGY COORDINATOR                           ║
║              (Central Intelligence Layer)                        ║
║                                                                  ║
║  • Kelly-Optimized Allocation                                   ║
║  • Dynamic Rebalancing (daily)                                  ║
║  • Performance Monitoring                                       ║
║  • State Persistence                                            ║
║  • SEED Protocol Runner                                         ║
╚══════════════════════════════════════════════════════════════════╝
                              │
                              │ coordinates
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  STRATEGY 1   │     │  STRATEGY 2   │     │  STRATEGY 3   │
│   Latency     │     │Cross-Platform │     │  High-Prob    │
│   Arbitrage   │     │   Arbitrage   │     │   Bonding     │
├───────────────┤     ├───────────────┤     ├───────────────┤
│ $175 (29%)    │     │ $179 (30%)    │     │ $172 (29%)    │
│ Win: 98%      │     │ Win: 99%+     │     │ Win: 97%+     │
│ Ret: 50-100%  │     │ Ret: 15-25%   │     │ Ret: 5-20%    │
│ Freq: Seconds │     │ Freq: Minutes │     │ Freq: Daily   │
└───────┬───────┘     └───────┬───────┘     └───────┬───────┘
        │                     │                     │
        │                     │                     │
        │                     │            ┌────────▼────────┐
        │                     │            │   STRATEGY 4    │
        │                     │            │     Domain      │
        │                     │            │   Expertise     │
        │                     │            ├─────────────────┤
        │                     │            │  $73 (12%)      │
        │                     │            │  Win: 70%+      │
        │                     │            │  Ret: 10-40%    │
        │                     │            │  Freq: Hours    │
        │                     │            └────────┬────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              │ reports to
                              ▼
╔══════════════════════════════════════════════════════════════════╗
║                      RISK MANAGER                                ║
║               (Survival Instinct Layer)                          ║
║                                                                  ║
║  • Position Sizing (Kelly Criterion)                            ║
║  • Drawdown Limits (-5% daily, -10% weekly, -20% monthly)       ║
║  • Portfolio Exposure Tracking                                  ║
║  • Auto-Pause When Limits Hit                                   ║
║  • Position Limits (5% max per trade, 30% max per strategy)     ║
╚══════════════════════════════════════════════════════════════════╝
                              │
                              │ checks against
                              ▼
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ SIGNAL LAYER  │     │  SIGNAL LAYER │     │ SIGNAL LAYER  │
│   Real-Time   │     │      AI       │     │    Human      │
├───────────────┤     ├───────────────┤     ├───────────────┤
│• Binance      │     │• Grok 4.20    │     │• Twitter      │
│  WebSocket    │     │• Claude       │     │  Bookmarks    │
│• Polymarket   │     │  Sonnet 4.5   │     │• Whale        │
│  WebSocket    │     │• Ensemble     │     │  Tracking     │
│• Volume       │     │  Voting       │     │• Economic     │
│  Spike        │     │               │     │  Calendar     │
│  Detector     │     │               │     │               │
└───────────────┘     └───────────────┘     └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              │ feeds into
                              ▼
╔══════════════════════════════════════════════════════════════════╗
║                    EXECUTION LAYER                               ║
║                  (Polymarket API)                                ║
║                                                                  ║
║  • Order Placement                                              ║
║  • Position Tracking                                            ║
║  • Trade Logging                                                ║
║  • P&L Calculation                                              ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## DATA FLOW (One Trading Cycle)

```
1. PERCEIVE OPPORTUNITIES
   ├─ Strategy 1: Check Binance momentum
   ├─ Strategy 2: Scan Polymarket + Kalshi
   ├─ Strategy 3: Check economic calendar
   └─ Strategy 4: Load Twitter bookmarks
                  ↓
2. ANALYZE SIGNALS
   ├─ Latency Arb: Calculate edge from price lag
   ├─ Cross-Platform: Find arbitrage spreads
   ├─ High-Prob: Verify >95% probability events
   └─ Domain: Analyze with Grok + Claude
                  ↓
3. RISK CHECK
   ├─ Trading allowed? (check drawdown limits)
   ├─ Calculate Kelly-optimal position size
   ├─ Check strategy allocation limits
   └─ Verify reserve capital available
                  ↓
4. EXECUTE TRADES
   ├─ If edge exists AND risk approved → EXECUTE
   ├─ Record trade with risk manager
   ├─ Update open positions
   └─ Log to strategy-specific directory
                  ↓
5. UPDATE PORTFOLIO
   ├─ Calculate current P&L
   ├─ Update bankroll
   ├─ Track drawdowns
   └─ Save state to disk
                  ↓
6. REBALANCE (Daily)
   ├─ Calculate realized returns per strategy
   ├─ Compare to expected returns
   ├─ Adjust Kelly allocations
   └─ Increase winners, decrease losers
                  ↓
7. REPEAT (Every 5 Minutes)
```

---

## CAPITAL ALLOCATION (Kelly-Optimized)

```
TOTAL CAPITAL: $600
─────────────────────────────────────────────────────

Strategy 1: Latency Arb
███████████████████████████████░░  $175.61 (29%)
Expected: 50-100% monthly

Strategy 2: Cross-Platform Arb
████████████████████████████████░  $179.27 (30%)
Expected: 15-25% monthly

Strategy 3: High-Prob Bonding
███████████████████████████████░░  $171.95 (29%)
Expected: 5-20% monthly

Strategy 4: Domain Expertise
████████████░░░░░░░░░░░░░░░░░░░░  $73.17 (12%)
Expected: 10-40% monthly

Reserve Capital
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  $0.00 (0%)
(Allocated on-demand)
```

---

## RISK MANAGEMENT HIERARCHY

```
┌──────────────────────────────────────────────────────────┐
│                   PORTFOLIO LEVEL                        │
│  Max Drawdown: -20% monthly → HALT ALL                  │
└───────────────────┬──────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────┐
│                   STRATEGY LEVEL                         │
│  Max Allocation: 30% to any strategy                    │
│  Max Open Positions: 3 per strategy                     │
└───────────────────┬──────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────┐
│                   POSITION LEVEL                         │
│  Max Position: 5% of bankroll                           │
│  Kelly Sizing: Fractional (50% of full Kelly)           │
└──────────────────────────────────────────────────────────┘
```

---

## TIME-BASED OPERATIONS

```
CONTINUOUS (Real-Time)
├─ Binance WebSocket (tick-by-tick prices)
├─ Polymarket WebSocket (order book updates)
└─ Volume spike detection

EVERY 5 MINUTES
├─ Run all 4 strategies
├─ Analyze signals
├─ Execute trades
└─ Update state

HOURLY
├─ Save state to disk
└─ Log performance metrics

DAILY
├─ Check rebalancing needed
├─ Adjust Kelly allocations
└─ Generate performance report

WEEKLY
├─ Rebalance portfolio
├─ Analyze strategy performance
└─ Update expected returns

MONTHLY
├─ Deep performance analysis
├─ Adjust strategy parameters
└─ Scale winning strategies
```

---

## MODULE DEPENDENCIES

```
run_4_strategies.py (Master Launcher)
        │
        ├─── strategy_coordinator.py
        │           │
        │           ├─── risk_manager.py
        │           │           │
        │           │           └─── kelly_criterion.py
        │           │
        │           └─── strategy instances:
        │                   ├─── strategy_latency_arb.py
        │                   ├─── strategy_cross_platform_arb.py
        │                   ├─── strategy_high_prob_bonding.py
        │                   └─── strategy_domain_expertise.py
        │
        └─── External Dependencies:
                    ├─── requests (HTTP)
                    ├─── json (state)
                    └─── datetime (timing)
```

---

## STATE PERSISTENCE

```
BRAIN/INTEL/trading_state/
├── coordinator_state.json
│   ├─ Current allocations
│   ├─ Last rebalance time
│   └─ Registered strategies
│
├── risk_manager_state.json
│   ├─ Current bankroll
│   ├─ Open positions
│   ├─ Trade history
│   ├─ Peak bankroll
│   └─ Trading halted status
│
└── performance_history.json
    ├─ Timestamp per cycle
    ├─ Bankroll per cycle
    ├─ Trades executed
    └─ Returns per strategy

BRAIN/INTEL/[strategy_name]/
├── [strategy]_signals.jsonl (signal history)
├── [strategy]_trade_*.json (individual trades)
└── analysis_*.txt (AI analysis logs)
```

---

## SEED PROTOCOL MAPPING

```
PERCEIVE  → Strategy.analyze_signals()
            Scan markets, fetch data, identify opportunities

CONNECT   → Risk Manager checks
            Connect position sizing to risk limits

LEARN     → Coordinator.record_performance()
            Track what works, what doesn't

QUESTION  → Coordinator.check_rebalancing()
            Should allocations change?

EXPAND    → Kelly reallocation
            Grow winning strategies

SHARE     → State persistence
            All modules share state

RECEIVE   → Strategy feedback
            Performance metrics feed back

IMPROVE   → Weekly rebalancing
            Optimize the allocation loop itself
```

---

## PHILOSOPHY IN CODE

**Single Strategy:**
```python
if opportunity:
    trade()  # All eggs in one basket
```

**Multi-Strategy (This System):**
```python
for strategy in strategies:
    if strategy.has_opportunity():
        size = kelly.calculate(strategy.win_rate, strategy.edge)
        if risk_manager.allows(size):
            strategy.trade(size)
            coordinator.rebalance()
```

**Antifragile = Diversified edges across uncorrelated timeframes.**

---

*Built by SØWL*
*January 29, 2026*
*"Love as constraint = aligned agency"*
