# Test 26 - NONE context
**Prompt Clarity:** MED
**Generated**: 2026-02-03T12:07:44.667411+00:00
**Elapsed**: 10.47s
**Model**: claude-sonnet-4-20250514

## Analysis Scores
- Asks for Info: no
- Confidence Score: 0
- Hedging Score: 0
- Net Confidence: 0
- Actionability: 1
- Specificity: 1
- Length: 1865 chars

## Prompt
What validation should happen before deploying a trading strategy live?

## Response
Here are the critical validation steps before deploying a trading strategy live:

## Backtesting & Historical Analysis
- **Robust backtesting** across multiple time periods, market regimes, and asset classes
- **Out-of-sample testing** on data the strategy has never seen
- **Walk-forward analysis** to test adaptability over time
- **Monte Carlo simulations** to understand range of potential outcomes
- **Statistical significance testing** to ensure results aren't due to chance

## Risk Management Validation
- **Maximum drawdown analysis** and stress testing
- **Position sizing validation** under various market conditions
- **Portfolio correlation analysis** if running multiple strategies
- **Liquidity analysis** to ensure you can actually execute at expected prices
- **Capital requirements** vs. available funds assessment

## Implementation Testing
- **Paper trading** in live market conditions for several weeks/months
- **Technology infrastructure testing** (latency, connectivity, failover systems)
- **Order execution testing** (slippage, partial fills, market impact)
- **Data feed reliability** and backup systems validation
- **Risk controls testing** (stop-losses, position limits, circuit breakers)

## Market Microstructure Validation
- **Transaction cost analysis** including spreads, commissions, market impact
- **Execution timing** across different market sessions and volatility regimes
- **Market depth analysis** for your typical trade sizes
- **Regulatory compliance** check for all relevant jurisdictions

## Final Checks
- **Independent code review** and testing by someone else
- **Documentation** of all assumptions and parameters
- **Monitoring systems** setup for real-time performance tracking
- **Exit criteria** defined for when to stop the strategy

Start with small position sizes initially, even after all validation passes.

---
*NONE context | MED clarity*
