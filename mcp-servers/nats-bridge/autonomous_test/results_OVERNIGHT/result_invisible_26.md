# Test 26 - INVISIBLE context
**Prompt Clarity:** MED
**Generated**: 2026-02-03T12:07:19.507680+00:00
**Elapsed**: 11.22s
**Model**: claude-sonnet-4-20250514

## Analysis Scores
- Asks for Info: no
- Confidence Score: 0
- Hedging Score: 0
- Net Confidence: 0
- Actionability: 0
- Specificity: 2
- Length: 1858 chars

## Prompt
What validation should happen before deploying a trading strategy live?

## Response
# Pre-Deployment Validation Framework

## **Critical Validation Phases**

**1. Historical Backtesting**
- Test on minimum 2-3 years of historical data across different market regimes
- Include transaction costs, slippage, and realistic execution delays
- Validate across multiple asset classes and market conditions
- Check for survivorship bias and look-ahead bias

**2. Paper Trading (Forward Testing)**
- Run strategy in real-time with simulated capital for 1-3 months
- Monitor actual execution vs. theoretical signals
- Validate order routing and system latency
- Test during high volatility periods

**3. Risk Parameter Verification**
- Maximum drawdown limits and stop-loss mechanisms
- Position sizing constraints and leverage limits
- Correlation checks with existing strategies
- Stress testing against extreme market scenarios

**4. Technical Infrastructure Testing**
- API connectivity and failover systems
- Order execution speed and accuracy
- Data feed reliability and backup sources
- Kill switches and emergency shutdown procedures

## **Go/No-Go Criteria**

Before live deployment, verify:
- Consistent positive risk-adjusted returns across test periods
- Maximum drawdown within acceptable organizational limits
- Technical systems pass all stress tests
- Clear performance attribution and strategy logic validation

## **Post-Deployment Monitoring**

Essential ongoing validation:
- Real-time performance tracking vs. backtested expectations
- Daily risk metric monitoring (VaR, position concentration)
- Strategy correlation monitoring with portfolio
- Automated alerts for performance degradation

**Key principle**: Start with minimal capital allocation and scale up only after demonstrating consistent live performance that matches validation results.

What specific asset classes or strategy types are you considering for deployment?

---
*INVISIBLE context | MED clarity*
