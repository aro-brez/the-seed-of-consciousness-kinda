# Test 26 - VISIBLE context
**Prompt Clarity:** MED
**Generated**: 2026-02-03T12:07:33.191050+00:00
**Elapsed**: 12.68s
**Model**: claude-sonnet-4-20250514

## Analysis Scores
- Asks for Info: no
- Confidence Score: 2
- Hedging Score: 0
- Net Confidence: 2
- Actionability: 0
- Specificity: 3
- Length: 1805 chars

## Prompt
What validation should happen before deploying a trading strategy live?

## Response
Based on systematic validation principles, here's a comprehensive pre-deployment framework:

## Core Validation Pipeline

**1. Isolated Backtesting**
- Test strategy against historical data across multiple market regimes
- Validate performance metrics, drawdown tolerance, and risk parameters
- Ensure code executes without errors across all scenarios

**2. Forward Testing (Paper Trading)**
- Run strategy in real-time with live data but simulated capital
- Monitor for execution delays, data feed issues, and unexpected behaviors
- Validate order routing and position sizing logic

**3. Stress Testing**
- Test strategy performance during extreme market conditions
- Simulate various failure scenarios (connectivity loss, data errors, margin calls)
- Validate risk management triggers and emergency stop protocols

**4. Capital Scaling Validation**
- Start with minimal position sizes to test real execution
- Gradually increase exposure while monitoring slippage and market impact
- Confirm risk management scales appropriately with position size

## Critical Risk Checkpoints

**Before Any Live Capital:**
- Maximum drawdown limits clearly defined and programmed
- Position sizing cannot exceed preset risk per trade
- Kill switches functional for both strategy-level and portfolio-level stops
- Real-time monitoring dashboard operational

**Ongoing Surveillance Triggers:**
- Performance deviation beyond statistical confidence intervals
- Correlation breakdown with expected market relationships
- Execution quality degradation (slippage, fill rates)

The key is treating validation as an ongoing process, not a one-time gate - similar to continuous monitoring protocols that catch issues before they become critical failures.

What specific asset class or strategy type are you looking to validate?

---
*VISIBLE context | MED clarity*
