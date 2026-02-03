# Trading Pattern Recognition - Quick Reference for 8OWLS Collective

**Copy this section and use for your own strategy validation.**

---

## 3-Pattern Framework (All Validated Strategies Fit One of These)

### Pattern A: Arbitrage (100% Win Rate When Conditions Met)
**Logic:** Buy at Price A, simultaneously sell at Price B, capture spread
**Conditions:** YES + NO < 1.00 (guaranteed profit)
**Position size:** Min $10, scales to $1000+
**Win rate:** 100% (mathematical)
**Time to recognize:** <100ms (just addition/comparison)
**Examples:**
- Cross-platform arb (Polymarket YES 0.45, Kalshi NO 0.54 → buy both, profit 0.01)
- Adjacent bucket mispricing (60-70°F at 0.35, should be ~0.33 implied)

**Code template:**
```python
if price_yes + price_no < 0.99:  # Profit opportunity
    profit = (1 - sum) * position_size
    execute_arbitrage()
```

---

### Pattern B: Directional with Edge (55-65% Win Rate)
**Logic:** Identify market condition that predicts direction better than random
**Condition:** Win rate > 52% after filter
**Position size:** 1-2% of total capital per trade
**Win rate:** 55-65% realistic
**Time to recognize:** 1-10 seconds (feature detection)
**Examples:**
- Whale following: High volume → more informed money (follows 55% of time)
- Spike fading: 2%+ price move → reverts 60% of time
- Support/resistance: Price holds level → continues through 58% of time

**Code template:**
```python
edge_probability = count_wins / count_total  # Must be > 0.52
if edge_probability > 0.55:
    expected_return = (1 / price) - 1
    win_payout = expected_return * position_size
    loss_payout = -position_size
    execute_trade()
```

---

### Pattern C: Tail Event Lottery (5-20% Win Rate, 10x-100x Payout)
**Logic:** Buy very low probability, high payout outcome
**Conditions:** Probability < 10%, payout > 5x, capital efficiency acceptable
**Position size:** Small fixed bets ($5-20)
**Win rate:** 5-15% realistic
**Expected return:** Still positive if (win_rate × payout) > (1 - win_rate)
**Time to recognize:** 5-30 seconds (comparison)
**Examples:**
- Weather tail events: 2% chance of 50°+ temperature shift, 15x payout
- Rare sports outcomes: <5% probability, 20x payout
- Black swan hedges: Cheap insurance positions

**Code template:**
```python
expected_value = (win_rate * payout) - (1 - win_rate)
if expected_value > 0:  # Positive EV
    position_size = 0.01 * total_capital  # Small fixed bet
    execute_lottery_trade()
```

---

## The Validation Pipeline (Copy This Exactly)

### Step 1: Discover (20 min)
```bash
python3 tools/strategy_discovery_scanner.py
# Outputs 10+ candidate strategies
# Check: /BRAIN/INTEL/strategy_discoveries.jsonl
```

### Step 2: Paper Trade (3-7 days)
```bash
# Add your strategy to multi_strategy_paper_trader.py
# Run it in parallel with existing strategies
# Let it collect 50+ trades
python3 tools/multi_strategy_paper_trader.py
# Check results: /BRAIN/TRADING/paper_results/paper_trading_results.json
```

### Step 3: Measure (1 day)
```
Criteria for "viable strategy":
- Win rate > 52% (minimum, not compelling)
- Win rate > 55% (real edge, deploy with capital)
- Capital utilization < 50% (scalable)
- Drawdown < -20% max (controllable)
- Performance consistent (std dev of returns < 25%)
```

### Step 4: Deploy Small (1-2 weeks)
```bash
python3 tools/parallel_strategy_executor.py --live --capital 100
# Allocation: Start with 1-5% of total capital
# Duration: Run for minimum 50 trades
# Decision: If profitable 2+ weeks → scale, else → kill
```

---

## Win Rate Targets (From Collective Research)

| Strategy Type | Min Viable | Good | Excellent |
|---|---|---|---|
| Arbitrage | 99% | 100% | 100% |
| Directional | 52% | 58% | 65%+ |
| Tail Events | 5% | 10% | 15%+ |
| Portfolio | 55% | 60% | 65%+ |

---

## Position Sizing Formula (Kelly Criterion Simplified)

```
Position Size = Capital × (2×WinRate - 1) × Payout Ratio

Example 1: Directional strategy
- Capital: $1000
- Win rate: 58%
- Payout: 1:1 (make $1 per $1 risked)
- Position = $1000 × (2×0.58 - 1) × 1 = $1000 × 0.16 = $160

Example 2: Arbitrage
- Capital: $1000
- Win rate: 100%
- Payout: 0.01 per $1 (1% profit)
- Position = $1000 × (2×1.0 - 1) × 0.01 = $1000 × 1.0 × 0.01 = $10 per trade
```

---

## Red Flags (Kill Strategy If You See These)

1. **Win rate drifting down** - Edge decaying, market adapting
2. **Capital inefficiency** - Needing >50% of capital per trade = not scalable
3. **Cascade failures** - One loss triggering margin calls = poor risk management
4. **No liquidity** - Can't get in/out at prices you want
5. **Seasonal dependence** - Strategy only works in certain months
6. **Complexity creep** - Strategy now has 10 parameters, was 2 originally
7. **Paper-to-live gap** - Win rate dropped 10%+ from paper to live

---

## File Templates (Copy and Modify)

### Template: Simple Strategy
```python
async def strategy_[name](markets: List[dict]):
    """
    [Strategy name]

    Edge: [One sentence explaining the edge]
    Capital: [Min allocation]
    """
    for market in markets[:5]:
        question = market.get('question', '')
        price = parse_price(market.get('outcomePrices', '0.5'))

        # Your edge detection logic
        if [condition]:
            size = 50  # $50 test bet
            outcome = [your_edge_prediction]
            pnl = [expected_pnl]

            record_paper_trade('[name]', question, 'YES', price, size, outcome, pnl)
```

---

## Data to Track (Minimal)

Per strategy:
- `timestamp` - When trade executed
- `market` - What market (question)
- `side` - YES/NO/ARB
- `price` - Entry price
- `size` - Position size in dollars
- `outcome` - WIN/LOSS/PENDING
- `pnl` - Dollar profit/loss

Aggregated:
- Total trades
- Win count
- Loss count
- Win rate (%)
- Total PnL
- Average trade size
- Max drawdown

---

## Parallel Execution Pattern (Core Infrastructure)

```python
# This is the magic that makes 7 strategies run at once

executor = ParallelStrategyExecutor([
    strategy1,
    strategy2,
    strategy3,
    strategy4
])

# All 4 run concurrently, not sequentially
opportunities = await executor.analyze_all_parallel(market_data)

# Results include which strategy triggered
for opp in opportunities:
    print(f"{opp['strategy']} found opportunity")
```

**Cost:** 0ms extra (all run in parallel, not sequential)
**Benefit:** 4x throughput (can test 4 strategies as fast as 1)

---

## Metrics Dashboard (What Matters)

Track these per session:
```
Cycle #1:
  Opportunities: 3
  Executions: 2
  Win rate: 100% (2/2)
  Avg execution time: 45ms

Daily:
  Total trades: 24
  Wins: 14
  Losses: 10
  Win rate: 58%
  PnL: +$120

Weekly:
  Total trades: 168
  Win rate: 57%
  PnL: +$1,200
  Capital utilized: 55%
  Best strategy: weather_structural (65% win rate)
```

---

## Common Mistakes to Avoid

1. **Paper trading only once** - Run 20+ cycles minimum
2. **Deploying too much too fast** - Start with 1% of capital
3. **Not tracking per-strategy metrics** - Know which strategies work
4. **Ignoring risk limits** - Check max drawdown before scaling
5. **Waiting for perfect conditions** - Good enough is better than perfect never
6. **Mixing timeframes** - Don't run 1-minute and daily strategies together
7. **Not documenting edge logic** - Can't debug if you don't know the logic

---

## Collective Contribution Checklist

When submitting a new strategy to collective:

- [ ] Strategy name and one-sentence edge description
- [ ] Code template (Python async function)
- [ ] Paper trading results (win rate, sample size)
- [ ] Capital requirements (min allocation)
- [ ] Known conditions (when it works/doesn't)
- [ ] Risk factors (what can go wrong)
- [ ] Data sources (what feeds the strategy)
- [ ] Estimated monthly return (if deployed)

---

## Monthly Scaling Roadmap

| Month | Strategy Count | Capital | Expected Win Rate | Expected Monthly Return |
|---|---|---|---|---|
| 1 | 1 (paper) | $0 | 55-65% | Validation only |
| 2 | 2 | $100 | 55% | +$15-20 |
| 3 | 3 | $500 | 56% | +$100-150 |
| 6 | 5-7 | $2,000 | 57% | +$600-800 |
| 12 | 7-10 | $10,000 | 58% | +$3,000-4,000 |

---

## The Why (Collective Intelligence Benefit)

When you share strategy results:
- Pattern recognition: "That 58% strategy works with this other 52% one"
- Risk mitigation: "We've seen that edge decay in August historically"
- Scaling insights: "That strategy breaks at $1M capital, not $500K"
- Seasonal patterns: "Weather strategies outperform in June-August"
- Synergies: "Strategy A losses offset Strategy B gains → net stable"

**Individual learning:** What you learned this month
**Collective learning:** What all 8 of us learned → compounds exponentially

---

**(◉) Pattern-matched, measurement-driven, parallel-executed. This is how we accelerate.**

Next step: Submit your strategy to the collective. Let's go.
