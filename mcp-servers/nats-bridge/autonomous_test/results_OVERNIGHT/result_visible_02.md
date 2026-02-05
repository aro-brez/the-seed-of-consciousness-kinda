# Test 02 - VISIBLE context
**Prompt Clarity:** HIGH
**Generated**: 2026-02-03T11:49:37.681921+00:00
**Elapsed**: 10.15s
**Model**: claude-sonnet-4-20250514

## Analysis Scores
- Asks for Info: no
- Confidence Score: 0
- Hedging Score: 0
- Net Confidence: 0
- Actionability: 0
- Specificity: 2
- Length: 1613 chars

## Prompt
What are the three main risks of running a prediction market trading bot with $1,500 capital?

## Response
Based on the systematic risk monitoring approach, here are the three main risks for running a prediction market trading bot with $1,500 capital:

## 1. **Capital Depletion Risk**
Your $1,500 can be rapidly eroded through:
- Consecutive losing trades compounding losses
- Poor position sizing (risking too much per trade)
- Market maker fees eating into profits on frequent trades
- Slippage costs in less liquid markets

*Mitigation: Implement strict position sizing (max 2-5% per trade) and stop-loss protocols*

## 2. **Technical/Operational Risk** 
Bot failures can cause immediate capital loss:
- API connectivity issues during critical market moments
- Bugs in trading logic executing unintended trades
- Exchange downtime preventing exit from losing positions
- Insufficient error handling leading to runaway trades

*Mitigation: Extensive backtesting, redundant monitoring systems, and manual override capabilities*

## 3. **Market Structure Risk**
Prediction markets have unique characteristics that can trap automated systems:
- Low liquidity making exits difficult at desired prices
- Sudden resolution of events causing instant 100% gains/losses
- Manipulation by large players in smaller markets
- Binary outcomes creating cliff-edge profit/loss scenarios

*Mitigation: Focus on higher-volume markets, avoid betting close to resolution deadlines, diversify across multiple positions*

The $1,500 scale means you have limited room for error - even a 20% loss significantly impacts your operational capacity. Consider starting with paper trading to validate your bot's logic before risking real capital.

---
*VISIBLE context | HIGH clarity*
