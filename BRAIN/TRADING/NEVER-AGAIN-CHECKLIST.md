# NEVER AGAIN CHECKLIST

**After -47% drawdown ($622.68 lost)**

This is the NON-NEGOTIABLE system. DO NOT TRADE until every item is checked.

---

## PART A: SYSTEM IMPLEMENTATION (Install the Guards)

### Gate 1: Thesis Quality Gate
- [ ] ThesisGate class instantiated
- [ ] Confidence threshold set to 0.70 (70% minimum)
- [ ] Vague word detector implemented (maybe, probably, think, believe, seems)
- [ ] Thesis length limit enforced (max 200 chars)
- [ ] Concrete market signal requirement enforced
- [ ] Rejection tracking enabled
- [ ] Test: Reject 3 vague theses, accept 3 specific ones
- [ ] Location: `tools/mvrs_minimum_viable_risk_system.py`

### Gate 2: Position Sizing (Kelly Criterion)
- [ ] PositionSizer class instantiated
- [ ] Kelly Criterion formula implemented
- [ ] 1/4 Kelly fractional applied (kelly_fraction=0.25)
- [ ] Position cap at 5% of bankroll enforced
- [ ] Negative Kelly rejection implemented (don't trade if negative EV)
- [ ] Win rate impact clear: 50% win = smaller positions than 60% win
- [ ] Test: Calculate size for 55% win rate, 15% win, 10% loss
- [ ] Location: `tools/mvrs_minimum_viable_risk_system.py`

### Gate 3: Loss Stop
- [ ] StopManager class instantiated
- [ ] Max loss at 10% per position (hardcoded, no negotiation)
- [ ] Auto-calculate loss stop price: entry_price * 0.90
- [ ] Automated check at every price update
- [ ] ZERO EMOTION: loss stops must auto-execute
- [ ] Test: Enter position, verify stop level calculated correctly
- [ ] Location: `tools/mvrs_minimum_viable_risk_system.py`

### Gate 4: Time Stop
- [ ] Max hold time at 14 days (hardcoded, no extension)
- [ ] Auto-calculate exit day: entry_time + 14 days
- [ ] Automated check at market open
- [ ] Exit executed automatically if time limit hit
- [ ] Test: Verify time stop triggers on day 14, not day 13 or 15
- [ ] Location: `tools/mvrs_minimum_viable_risk_system.py`

### Gate 5: Daily Circuit Breaker
- [ ] DailyCircuitBreaker class instantiated
- [ ] Max daily loss at 5% (halts all NEW trades)
- [ ] Max weekly loss at 10% (halts all trades, even existing)
- [ ] Automated reset at midnight (daily) and Monday (weekly)
- [ ] Check called at market open and before every entry
- [ ] Trading halted returns specific halt reason
- [ ] Test: Simulate -5% loss, verify trading halted
- [ ] Location: `tools/mvrs_minimum_viable_risk_system.py`

### Gate 6: Trade Journal
- [ ] TradeJournal class instantiated
- [ ] Every entry logged: thesis, confidence, entry price, position size
- [ ] Every exit logged: exit price, exit reason, thesis correctness
- [ ] Journal persisted to disk (JSON)
- [ ] Weekly analysis capability implemented
- [ ] Kills identified: which exit reasons lose money?
- [ ] Test: Log 5 trades, run weekly analysis, identify patterns
- [ ] Location: `tools/mvrs_minimum_viable_risk_system.py`

### Gate 7: Daily Monitoring
- [ ] PositionMonitor class instantiated
- [ ] All open positions tracked continuously
- [ ] Health score calculated (0-100 scale)
- [ ] Alerts triggered for health < 60
- [ ] Daily morning routine implemented
- [ ] Current prices fetched for all positions
- [ ] Test: Add 3 positions, run daily check, verify alerts for underwater ones
- [ ] Location: `tools/mvrs_minimum_viable_risk_system.py`

### Gate 8: Weekly Retrospective
- [ ] Weekly analysis capability implemented
- [ ] Calculates: win rate, P&L, avg win, avg loss, by exit reason
- [ ] Identifies "top killer" (exit reason that costs most money)
- [ ] Thesis accuracy tracked
- [ ] Recommendations generated: size up/down for next week?
- [ ] Friday market close automation in place
- [ ] Test: Run on sample trades, verify killer identification
- [ ] Location: `tools/mvrs_minimum_viable_risk_system.py`

---

## PART B: TRADING RULES HARDCODED (These Cannot Be Negotiated)

### Position Entry Rules
- [ ] No trade enters without passing Thesis Gate
- [ ] No trade enters with confidence < 70%
- [ ] No trade enters if Circuit Breaker active
- [ ] No trade enters without calculated position size from Kelly
- [ ] No trade enters if position size > 5% of bankroll
- [ ] No trade enters with vague thesis language
- [ ] Entry thesis recorded before execution

### Position Monitoring Rules
- [ ] All positions checked at market open
- [ ] All positions checked every hour (or tick-based)
- [ ] Alerts sent for health < 60%
- [ ] Alerts sent for losses > 50% of account
- [ ] Alerts sent for positions near stop levels

### Position Exit Rules
- [ ] All positions have loss stop at -10% (no negotiation)
- [ ] All positions have time stop at 14 days (no extension)
- [ ] All positions have thesis stop (exit if thesis invalidated)
- [ ] No positions held beyond their stop levels
- [ ] Exit reason recorded for every exit

### Daily Rules
- [ ] Trading halted at -5% daily loss
- [ ] Position sizes reduced to 50% if weekly loss > 10%
- [ ] Daily morning routine run at market open
- [ ] Current capital checked before each entry
- [ ] Thesis confidence minimum: 70%

### Weekly Rules
- [ ] Retrospective run Friday at market close
- [ ] Win rate calculated
- [ ] "Top killer" identified (what's losing money?)
- [ ] Next week plan generated
- [ ] Thesis effectiveness updated (proven/disproven)

---

## PART C: METRICS TO TRACK

### Daily Metrics
- [ ] Capital: opening, closing, change
- [ ] Trades: count, wins, losses, P&L
- [ ] Circuit breaker status (OK / reduced size / halted)
- [ ] Position health distribution (healthy/warning/critical)

### Weekly Metrics
- [ ] Win rate (target: >= 50%)
- [ ] Average win ($)
- [ ] Average loss ($)
- [ ] Win:Loss ratio (target: >= 1:1)
- [ ] Total P&L
- [ ] "Top killer" exit reason (what costs most?)

### Monthly Metrics
- [ ] Total return %
- [ ] Max drawdown (peak to trough)
- [ ] Recovery time from largest DD
- [ ] Thesis accuracy (% of theses correct)
- [ ] Position sizing effectiveness

---

## PART D: DOCUMENTATION & RECORDS

### Files That Must Exist
- [ ] `/BRAIN/TRADING/DRAWDOWN-ANALYSIS-47pct.md` (lessons from -47% loss)
- [ ] `/tools/mvrs_minimum_viable_risk_system.py` (the actual code)
- [ ] `/BRAIN/TRADING/mvrs_trade_journal.json` (trade log)
- [ ] `/BRAIN/TRADING/NEVER-AGAIN-CHECKLIST.md` (this file)

### Documentation That Must Be Written
- [ ] [ ] Why thesis validation is critical (and what went wrong)
- [ ] [ ] Why position sizing is scientific (not guessing)
- [ ] [ ] Why stops must be automated (no emotion)
- [ ] [ ] Why circuit breakers prevent catastrophe (math of -47%)
- [ ] [ ] Why trade journal drives learning (can't fix what you don't measure)

---

## PART E: LAUNCH VERIFICATION (Before Trading 1 Dollar)

### Code Works (Test All Gates)
- [ ] Test 1: Thesis Gate accepts good thesis, rejects bad ones
  - Run: `python3 tools/mvrs_minimum_viable_risk_system.py`
  - Verify: 3 accepted, 3 rejected

- [ ] Test 2: Position Sizing calculates correctly
  - Input: 55% win rate, 15% win, 10% loss
  - Expected output: position_size = ~2.25% of bankroll

- [ ] Test 3: Stop Manager flags losses at -10%
  - Input: entry $100, current $90
  - Expected: should_exit = True, reason = LOSS_STOP

- [ ] Test 4: Circuit Breaker halts at -5%
  - Input: capital -5%, current price check
  - Expected: trading_allowed = False

- [ ] Test 5: Trade Journal records + exits
  - Log 3 trades
  - Exit 2 trades
  - Verify JSON file has correct records

- [ ] Test 6: Weekly Analysis identifies killer
  - Load sample trades (some profitable, some not)
  - Run weekly_analysis()
  - Verify killer reason identified

### Mental Model Clear
- [ ] Can explain why position sizing matters (2:1 risk:reward needs 50% win rate)
- [ ] Can explain why stops prevent catastrophe (math of uncontrolled loss)
- [ ] Can explain why thesis validation is critical (wrong thesis = wrong entry)
- [ ] Can explain why circuit breaker saves accounts (daily loss halt prevents spiral)
- [ ] Can explain why trade journal drives learning (you learn patterns from data, not memory)

### Ready to Trade
- [ ] All code deployed and tested
- [ ] All metrics being tracked
- [ ] All alerts configured
- [ ] Morning routine automated
- [ ] Friday retrospective process in place
- [ ] Capital restored to trading level
- [ ] **SIGNED OFF**: Aaron confirms readiness

---

## PART F: RED FLAGS (Stop Immediately If Any Occur)

### System Failures
- [ ] Thesis Gate bypassed (trading without passing gate)
- [ ] Stop loss not honored (loss > -10%)
- [ ] Time stop not honored (held > 14 days)
- [ ] Circuit breaker ignored (trading despite halt)
- [ ] Position size calculated outside Kelly bounds
- [ ] Trade not logged in journal

### Pattern Failures
- [ ] Win rate below 40% for 3+ consecutive days
- [ ] Average loss > average win (losing bigger than winning)
- [ ] Same exit reason killing 50%+ of losses (thesis validation broken?)
- [ ] Thesis accuracy below 25% (thesis generation completely broken)

### Capital Failures
- [ ] Daily loss > 5% (circuit breaker should halt, if it doesn't = system bug)
- [ ] Weekly loss > 10% (should be halted, if not = system bug)
- [ ] Drawdown from peak > 20% (something is wrong, investigate)

### Process Failures
- [ ] Morning routine skipped
- [ ] Friday retrospective skipped
- [ ] Trade journal not updated
- [ ] Positions not monitored
- [ ] Alerts ignored

**IF ANY RED FLAG TRIGGERS: Stop trading immediately, debug the system, fix the issue, then resume.**

---

## PART G: RECOVERY PROTOCOL (From $695.95)

### Phase 1: STABILIZE (Weeks 1-2)
- [ ] Max 1 trade per day
- [ ] Position sizes at 50% normal
- [ ] Thesis confidence >= 80% (very high bar)
- [ ] Target: Stop drawdown, reach $695.95 + 5% buffer
- [ ] Success metric: Win rate >= 60% (proof system works)

### Phase 2: BUILD BACK (Weeks 3-8)
- [ ] Increase to 3 trades per day if win rate >= 55%
- [ ] Normal position sizes if capital >= $850
- [ ] Thesis confidence >= 75%
- [ ] Target: Reach $1,000 (44% recovery from current)
- [ ] Success metric: Consistent 55%+ win rate

### Phase 3: RESTORE (Weeks 9-26)
- [ ] Full trading resume at $1,000+
- [ ] Scale positions based on Kelly
- [ ] Thesis confidence >= 70%
- [ ] Target: Reach $1,318 (100% recovery)
- [ ] Success metric: Maintain positive returns monthly

---

## THE FINAL COMMITMENT

**I understand that:**

1. **This is not optional.** Every rule must be enforced, every gate must be passed.

2. **This is not temporary.** These rules apply forever (or until I prove I can trade safely).

3. **This is not negotiable.** No exceptions, no "just this once."

4. **This is the price of trading.** Better discipline now than bankruptcy later.

5. **This is how I learn.** Trade journal + retrospective = exponential improvement.

---

## SIGNATURE & DATE

**System ready for deployment:**
- [ ] All 8 gates implemented
- [ ] All tests passing
- [ ] All documentation complete
- [ ] All alerts configured
- [ ] All processes automated
- [ ] Ready to trade with MVRS active

**By date:** ___________

**Status: LIVE DEPLOYMENT**

---

## NEXT SESSION: FIRST DAY CHECKLIST

When you start trading again:

1. [ ] Run morning routine (circuit breaker check, position health check)
2. [ ] Verify all systems running (journal, monitor, alerts)
3. [ ] Thesis confidence high (>= 75%)
4. [ ] Position size calculated by Kelly (automatic)
5. [ ] Stops set before entry (automatic)
6. [ ] Trade logged (automatic)
7. [ ] EOD review (did anything violate rules?)

**Remember:** The system isn't meant to make you money. It's meant to prevent you from losing money. Once losses are prevented, profits follow naturally.

(◉) Breathe. Check. Trade.
