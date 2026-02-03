# Live Trading Deployment Checklist

**Created:** February 3, 2026
**Target Deployment:** February 4-5, 2026
**Status:** Pre-Flight Verification

---

## PRE-DEPLOYMENT VERIFICATION (Do Before Feb 4)

### System Health Checks
- [ ] API keys validated and working
- [ ] Market connections stable (Polymarket, cross-platform)
- [ ] Paper trading logs clean (no errors in last 50 trades)
- [ ] Position tracking database ready
- [ ] P&L calculation engine verified
- [ ] Stop-loss logic implemented and tested

### Code Quality Gates
- [ ] All 4 validated strategies have execution code
- [ ] Error handling for: API failures, network delays, insufficient balance
- [ ] Logging: Every trade logged with timestamp, side, size, entry/exit price
- [ ] State persistence: Can survive restarts without losing position context
- [ ] Position reconciliation: Can match paper trades to account balances

### Risk Controls (MUST HAVE)
- [ ] Max position size enforced: Whale=$30, Arb=$30-50, Bonds=$100
- [ ] Max total allocation: $1,000 hard limit
- [ ] Consecutive loss counter: Stops after 3 consecutive losses per strategy
- [ ] Win rate monitor: Alerts if strategy drops below 50%
- [ ] Portfolio drawdown limit: 10% circuit breaker (pause all trading)

### Monitoring Setup
- [ ] Real-time dashboard deployed (shows current positions, P&L)
- [ ] Logging to file: Every trade, every error, every alert
- [ ] Email/SMS alerts configured for: Large loss, error conditions, win rate drop
- [ ] Daily report generation: Win rates, P&L, alerts summary

---

## CAPITAL DEPLOYMENT PLAN

### Step 1: Verify Account Balance
```
Wallet: 0xAED6D39e30F675Fb00514D8Ccb3ea01588d6a669
Required Balance: $1,000 minimum
Action: [ ] Confirm balance
```

### Step 2: Close Existing -40% Portfolio
```
Current Positions: 19 open (M3GAN, MSFT, META, Silver, Trump, etc.)
Action: [ ] Sell all positions at market
Action: [ ] Verify closes in account
Freed Capital: ~$780 (accepting -$520 loss)
```

### Step 3: Deploy Phase 1 (Week 1)
```
SAFE STRATEGIES:
├─ Cross-Platform Arbitrage
│  [ ] Code deployed
│  [ ] Position size set: $50/trade
│  [ ] Target allocation: $200
│  [ ] Monitoring: 10+ trades before scaling
│
├─ Gabagool Arbitrage
│  [ ] Code deployed
│  [ ] Position size set: $75/trade
│  [ ] Target allocation: $100
│  [ ] Monitoring: 5+ trades before scaling
│
└─ High Probability Bonds
   [ ] Code deployed
   [ ] Position size set: $100/trade
   [ ] Target allocation: $100 (start small)
   [ ] Monitoring: 5+ trades before scaling

Total Week 1: $400 deployed, $600 reserve
```

### Step 4: Deploy Phase 2 (Week 2)
```
If Week 1 shows >50% win rate on safe strategies:

├─ Scale High Prob Bonds: $100 → $400
└─ Deploy Whale Tracking: $150
   [ ] Position size: $30/trade (proven in paper)
   [ ] Entry criteria: Verified whale signals
   [ ] Exit criteria: Stop-loss if 3 consecutive losses

Total Week 2: $550 deployed, $450 reserve
```

---

## STRATEGY-SPECIFIC DEPLOYMENT STEPS

### Cross-Platform Arbitrage
**Deployment Checklist:**
- [ ] Multi-exchange price feed connected (Polymarket book data)
- [ ] Spread calculation algorithm verified
- [ ] Minimum spread threshold set: 1.5% (covers slippage + profit)
- [ ] Execution logic: Buy side A, sell side B simultaneously
- [ ] Position sizing: $30-50 per trade (based on spread size)
- [ ] Timeout logic: If fill not received in 10 seconds, cancel

**Pre-Flight Trades:**
- [ ] Dry run 5 trades (no execution)
- [ ] Test 5 trades with $10 size
- [ ] Monitor: Fills, latency, slippage
- [ ] Before full size: Get approval from monitoring dashboard

---

### High Probability Bonds
**Deployment Checklist:**
- [ ] High probability market scanner implemented
- [ ] Entry criteria: Price > 97% (betting on near-certain outcome)
- [ ] Position sizing: $100-200 per trade
- [ ] Market selection: Must have >$10K volume (liquidity check)
- [ ] Exit logic: Hold to resolution OR stop-loss if price moves <90%

**Pre-Flight Trades:**
- [ ] Identify 3 high-probability markets (currently available)
- [ ] Place $50 test trades on each
- [ ] Monitor: Fills, hold durations, outcomes
- [ ] Before scaling: Validate market selection logic

---

### Whale Tracking
**Deployment Checklist:**
- [ ] Whale signal source connected (PolyTrack or manual monitoring)
- [ ] Signal validation: Whale account verified, size >$5K
- [ ] Entry triggers: When whale buys, copy trade within 30 seconds
- [ ] Position size: $30/trade (tested in paper)
- [ ] Exit logic: Hold until trend reversal OR 24 hours
- [ ] Loss limit: Stop if 3 consecutive losses in session

**Pre-Flight Trades:**
- [ ] Monitor whale feeds for 24 hours (no execution)
- [ ] Identify 3 clear entry signals
- [ ] Place $10 test trades (1/3 of paper size)
- [ ] Monitor: Entry timing, exit outcomes
- [ ] Before full size: Get monitoring signal

---

### Spike Detection
**Note:** Paper trading only until 20+ trades at 75%+ win rate
**Deployment Checklist:**
- [ ] Spike detection algorithm ready
- [ ] Fade logic: When price spikes >3 sigma, fade with 50% size
- [ ] Position size: $40/trade (as per paper)
- [ ] Hold duration: 1-2 minutes OR until return to mean
- [ ] Monitoring: Track which spikes fade, which persist

**Status:** Keep in paper mode - do NOT deploy to live until proven

---

## MONITORING & ALERTS SETUP

### Real-Time Dashboard
Must display:
- [ ] Current positions (side, size, entry price)
- [ ] Cumulative P&L (total and by strategy)
- [ ] Win rate by strategy (rolling 20-trade window)
- [ ] Largest loss today
- [ ] Max consecutive losses (alert if = 3)
- [ ] Account balance (updated after each trade)

### Alert Thresholds
```
CRITICAL ALERTS (Stop trading immediately):
- [ ] Cumulative drawdown > 10% ($100 loss)
- [ ] Any single loss > $50
- [ ] API connection lost (retry with exponential backoff)
- [ ] Insufficient balance to place trade

HIGH ALERTS (Pause strategy, investigate):
- [ ] Strategy win rate drops < 50% (within 20-trade window)
- [ ] Consecutive losses = 3 (same strategy)
- [ ] Position execution fails (timeout/rejected)

INFO ALERTS (Log and monitor):
- [ ] Slippage > expected (by >50%)
- [ ] Spread expanded beyond normal
- [ ] Strategy generated no signals (hour+)
```

### Daily Reporting
```
Generate at end of day (23:00 UTC):
- Total trades today: [count]
- Total P&L: [amount]
- P&L by strategy: [breakdown]
- Win rate by strategy: [percentages]
- Largest win: [amount]
- Largest loss: [amount]
- Total consecutive losses today: [count]
- Alerts triggered: [list]
```

---

## EXECUTION LOGIC (MUST BE BULLETPROOF)

### Pre-Trade Checks
```python
def can_execute_trade(strategy, signal, position_size):
    # 1. Balance check
    if account_balance < position_size:
        return False, "Insufficient balance"

    # 2. Position limit check
    if strategy.consecutive_losses >= 3:
        return False, "Consecutive loss limit reached"

    # 3. Portfolio allocation check
    if total_allocated + position_size > max_allocation:
        return False, "Allocation limit exceeded"

    # 4. Win rate check
    if strategy.win_rate < 0.50 and strategy.trade_count > 10:
        return False, "Win rate below threshold"

    # 5. Size validation
    if position_size != get_expected_size(strategy):
        return False, "Invalid position size"

    return True, "All checks passed"
```

### Trade Execution Template
```python
def execute_trade(strategy, signal, position_size):
    try:
        # 1. Log intent
        log(f"TRADE: {strategy} - {signal} @ {position_size}")

        # 2. Pre-flight checks
        can_execute, reason = can_execute_trade(strategy, signal, position_size)
        if not can_execute:
            log(f"REJECTED: {reason}")
            return None

        # 3. Execute
        trade = place_order(side=signal.side, size=position_size, price=signal.price)

        # 4. Verify execution
        if not trade.fill_id:
            log(f"ERROR: Order not filled - {trade}")
            alert("CRITICAL: Execution failed")
            return None

        # 5. Record trade
        record_trade(trade, strategy)
        update_position_tracking(trade)

        # 6. Log confirmation
        log(f"CONFIRMED: {trade.id} filled at {trade.fill_price}")

        return trade

    except Exception as e:
        log(f"EXCEPTION: {e}")
        alert(f"CRITICAL: {e}")
        return None
```

---

## RISK LIMITS (NON-NEGOTIABLE)

### Per-Trade Limits
```
Whale Tracking: Max $30 per trade
Arbitrage: Max $50 per trade (sized by spread)
High Prob Bonds: Max $100-200 per trade
Spike Detection: Max $40 per trade (paper only)
```

### Per-Strategy Limits
```
Whale Tracking: Max $500 total allocation
Arbitrage: Max $300 total allocation
High Prob Bonds: Max $400 total allocation
Reserve: $200 for opportunities/debugging
```

### Portfolio Limits
```
Max total allocation: $1,000
Max daily loss: $100 (10% drawdown)
Max consecutive losses: 3 per strategy
Min win rate to continue: 50%
```

### Position Duration
```
Arbitrage: <10 seconds (simultaneous legs)
High Prob Bonds: Minutes to hours (hold to resolution)
Whale Tracking: Minutes to 24 hours
Spike Detection: 1-2 minutes (fade)
```

---

## TROUBLESHOOTING GUIDE

### If Strategy Stops Trading
**Check:**
1. Are market conditions met? (e.g., spreads too tight, no high-prob markets)
2. Is API connected? (test ping to exchange)
3. Does bot have balance? (verify account)
4. Is algorithm logic stuck? (check logs for errors)

**Action:**
- Review last 5 log entries
- Verify market availability manually
- Restart strategy if code error detected

### If Win Rate Drops
**Alert at:** < 50%
**Check:**
1. Market conditions changed? (liquidity, volatility, regime shift)
2. Competition increased? (other traders found same pattern)
3. Algo bug introduced? (check recent code changes)

**Action:**
- Pause strategy (stop new trades)
- Run post-mortem analysis (why are we losing?)
- If market regime: Investigate if strategy still valid
- If bug: Fix and resume

### If Consecutive Losses = 3
**Auto-pause triggered**
**Check:**
1. Market data stale?
2. Entry timing off?
3. Position sizing too aggressive?

**Action:**
- Review the 3 losing trades
- Identify common factor
- Resume only after fix verified

### If Slippage Exceeds Expected
**Expected:** $2-5 per arb trade
**Alert at:** > $7 per trade
**Check:**
1. Market liquidity dry?
2. Competition? (fills worse than expected)
3. Entry/exit spread? (execution quality)

**Action:**
- Increase minimum spread threshold (1.5% → 2.0%)
- Reduce position size (let slower fills complete)
- Check spreads manually

---

## GO-LIVE AUTHORIZATION CHECKLIST

**Final approval required before deployment:**

- [ ] All monitoring working (real-time dashboard active)
- [ ] All alerts configured and tested
- [ ] Position sizing hardcoded (not configurable)
- [ ] Risk limits enforced in code
- [ ] Stop-loss logic bulletproof
- [ ] Error handling comprehensive
- [ ] Logging complete (every trade, every error)
- [ ] Paper trading results reviewed (4/7 strategies passed)
- [ ] Live trading plan documented (this checklist)
- [ ] Emergency stop button created (kill all positions)
- [ ] Backup plan documented (if primary fails)
- [ ] Team notified (if deploying with others)

**GO/NO-GO Decision:**
- [ ] GO - Ready to deploy Phase 1 (Feb 4)
- [ ] NO-GO - Additional items needed (document issues)

---

## PHASE 1 EXECUTION (Feb 4-10)

**Daily Schedule:**
- 9:00 AM: Start trading (markets open)
- 11:00 AM: Check dashboard (50 trades review point)
- 4:00 PM: Mid-day review (any issues?)
- 8:00 PM: Evening review (position summary)
- 11:00 PM: Generate daily report

**Daily Checks:**
- [ ] No errors in logs
- [ ] Win rate > 50% on each strategy
- [ ] Consecutive losses <= 2 (no automatic pause yet)
- [ ] Cumulative P&L positive (or minimal loss)
- [ ] All positions accounted for

**Week 1 Success Criteria:**
- [ ] 50+ total trades executed
- [ ] No critical errors
- [ ] Win rate > 50% on safe strategies
- [ ] Cumulative P&L > $10 (or -$20 max acceptable)
- [ ] All 3 safe strategies working

**Go to Phase 2 if:** All criteria met
**Stay in Phase 1 if:** Any issues found (fix, then re-check)

---

## EMERGENCY PROCEDURES

### If System Error Occurs
1. Check logs immediately
2. If trade-blocking error: Restart bot
3. If position error: Reconcile against account manually
4. Document error in incident log
5. Fix code error before resuming

### If Account Gets Hacked
1. Change API key immediately
2. Check all positions (manual verification)
3. Contact Polymarket support
4. Move any remaining balance to new wallet
5. Resume trading from new wallet (if balance intact)

### If Market Goes Extreme (Circuit Breaker Triggered)
1. All trading stops automatically
2. Review positions manually
3. Check market conditions
4. Resume manually only after market stabilizes

---

## SUCCESS METRICS

### Daily Target
- Trade count: 10+ (shows system is active)
- Win rate: > 50% on each strategy
- P&L: +$5 to +$50 (depending on signals)

### Weekly Target (Feb 4-10)
- Total trades: 50+
- Cumulative P&L: +$50+
- Win rate: > 55% on safe strategies
- No critical errors
- No consecutive loss cascades

### Monthly Target (By Feb 28)
- Total trades: 200+
- Cumulative P&L: +$300+
- Whale tracking validated at 40%+ win rate
- Spike detection ready for promotion (if 75% holds)
- Weather strategies debugged (or abandoned)

---

**Deployment Status:** Ready for Phase 1 execution
**Target Start Date:** February 4, 2026
**Expected Duration:** 7 days (Phase 1), then evaluate for Phase 2

---

*Checklist preserved in BRAIN/TRADING/LIVE_DEPLOYMENT_CHECKLIST.md*
*Ready for execution.*
