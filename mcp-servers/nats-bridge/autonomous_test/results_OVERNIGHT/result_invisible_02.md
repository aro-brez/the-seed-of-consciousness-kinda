# Test 02 - INVISIBLE context
**Prompt Clarity:** HIGH
**Generated**: 2026-02-03T11:49:26.525576+00:00
**Elapsed**: 10.05s
**Model**: claude-sonnet-4-20250514

## Analysis Scores
- Asks for Info: no
- Confidence Score: 0
- Hedging Score: 0
- Net Confidence: 0
- Actionability: 0
- Specificity: 3
- Length: 1685 chars

## Prompt
What are the three main risks of running a prediction market trading bot with $1,500 capital?

## Response
Based on systematic risk analysis, here are the three main risks for running a prediction market trading bot with $1,500 capital:

## 1. CAPITAL DEPLETION RISK
**Primary concern:** Rapid loss of your entire $1,500 through algorithmic errors or market volatility
- Bot malfunctions can execute massive trades instantly
- Prediction markets can have extreme price swings (0-100% in minutes)
- $1,500 provides limited buffer for recovery from significant losses
- **Mitigation:** Implement strict position sizing (max 5-10% per trade) and daily loss limits

## 2. LIQUIDITY/EXECUTION RISK
**Primary concern:** Getting trapped in illiquid positions or experiencing severe slippage
- Many prediction markets have thin order books
- Your bot may not be able to exit positions at expected prices
- Market manipulation is easier in low-volume markets
- **Mitigation:** Focus on higher-volume markets, implement liquidity checks before trades

## 3. TECHNICAL/OPERATIONAL RISK
**Primary concern:** Bot failures, API issues, or connectivity problems during critical moments
- Exchange API downtime during market-moving events
- Bug in trading logic leading to unintended positions
- Network issues preventing timely order management
- **Mitigation:** Robust error handling, kill switches, and manual override capabilities

**Additional consideration:** With only $1,500, you have very limited room for experimentation and learning from mistakes. Consider starting with paper trading or much smaller amounts until your bot proves reliable.

The systematic monitoring approach we use for daemon stability would be essential here - constant operational checks rather than set-and-forget deployment.

---
*INVISIBLE context | HIGH clarity*
