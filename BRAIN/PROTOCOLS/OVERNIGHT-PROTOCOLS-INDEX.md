# Overnight Autonomous Operations - Complete Protocols Index
**For:** SØWL and all autonomous instances running overnight
**Updated:** February 3, 2026
**Classification:** CRITICAL for unsupervised operations

---

## WHAT THIS IS

Complete set of protocols for autonomous trading/operations overnight without human supervision. Covers:
- What external factors affect the system
- What signals require monitoring
- How to respond to each type of alert
- Thresholds for automated decision-making

**This protocol is the difference between safe autonomous operations and expensive failures.**

---

## QUICK NAVIGATION

### For Fast Decision-Making
Start here if an alert just fired:
- **`ALERT-RESPONSE-MATRIX.md`** - Print this, laminate it, keep at hand
  - Yellow alert → what to do in 30 seconds
  - Red alert → what to do immediately
  - Decision tree for every scenario
  - Files created by alerts, where to find them

### For Understanding the System
Understand what you're monitoring:
- **`overnight-monitoring-protocol.md`** - Complete reference (30 pages)
  - All 4 layers of monitoring explained
  - Alert triggers and thresholds
  - Monitoring automation setup
  - Response playbooks for each scenario

### For Configuration
Set up and tune the system:
- **`alert-thresholds.json`** - All numeric thresholds
  - Market conditions (API latency, spreads, volume)
  - System resources (CPU, memory, disk, network)
  - Process integrity (position sync, execution, prices)
  - Anomaly detection (whales, news, events)
  - Check frequencies and escalation rules

---

## THE 4 MONITORING LAYERS

### Layer 1: Market Conditions
**What:** Trading ecosystem health - APIs, exchanges, liquidity
**Why:** Markets stop working unexpectedly; need to detect immediately
**Alert Types:**
- Yellow: Slow API, wide spreads, imbalanced orderbook
- Red: API down, no liquidity, flash crash, exploit suspected
**Check Frequency:** Every 30 seconds to every minute
**Reference:** `overnight-monitoring-protocol.md` → "LAYER 1: MARKET CONDITIONS"

### Layer 2: System Infrastructure
**What:** Your system's health - CPU, memory, disk, network, APIs
**Why:** Can't trade if Mac crashes, internet cuts, or disk fills
**Alert Types:**
- Yellow: High CPU (70-85%), high memory (80-90%), slow network
- Red: Critical CPU (>85%), critical memory (>90%), network down, API invalid
**Check Frequency:** Every 30 seconds to every 5 minutes
**Reference:** `overnight-monitoring-protocol.md` → "LAYER 2: SYSTEM INFRASTRUCTURE"

### Layer 3: Process Integrity
**What:** Your trading system's internal state - orders, positions, cash
**Why:** Desynchronization = potential losses or frozen positions
**Alert Types:**
- Yellow: Position count off by 1, execution delayed 5-30 seconds
- Red: Position count off by >2, order filled but not logged, state unrecoverable
**Check Frequency:** Every minute to every trade
**Reference:** `overnight-monitoring-protocol.md` → "LAYER 3: PROCESS INTEGRITY"

### Layer 4: Anomaly Signals
**What:** Market is telling you something - whale moves, news, events
**Why:** Early signal of regime change, regulatory action, or insider knowledge
**Alert Types:**
- Yellow: Whale transaction, news detected, Twitter spike
- Red: Regulatory announcement, exchange exploit, geopolitical event
**Check Frequency:** Every 5 minutes to continuous
**Reference:** `overnight-monitoring-protocol.md` → "LAYER 4: ANOMALY SIGNALS"

---

## ALERT SEVERITY LEVELS

### YELLOW Alert (Monitor, Document, Continue)
```
Condition: Something is abnormal but not critical
Response: Log it, reduce risk, monitor closely for next 5-10 minutes
Action: nats_publish "[WARN] [category]: [issue]"
Escalate to Red if: Worsens, or 2+ yellows same category in 5 min
Resume Normal if: Issue resolves on its own
Timeline: No immediate trading stop, but be careful
```

**Examples:**
- API response time 2+ seconds (but still responding)
- CPU at 75% (high but functional)
- Spread widened to 1.5% (wider than normal)
- 5 tweets about market in 5 minutes (possible sentiment shift)

### RED Alert (STOP IMMEDIATELY)
```
Condition: Critical failure, system cannot operate safely
Response: STOP ALL TRADING immediately, log everything
Action:
  1. pkill -f autonomous_
  2. nats_publish "[CRITICAL] [issue]"
  3. python3 tools/dump_state.py > incident_[timestamp].log
  4. WAIT FOR HUMAN
Timeline: All trading stops immediately, no recovery attempt
Never: Try to fix automatically during RED alert
```

**Examples:**
- Polymarket API returns 500 errors
- Network completely unreachable
- CPU sustained >85% and system unresponsive
- Position count off by >2 (desynchronized)
- Order placed on exchange but system has no record

---

## THRESHOLDS AT A GLANCE

See `alert-thresholds.json` for complete reference. Key thresholds:

**Market Conditions:**
- API Latency: Healthy <500ms, Yellow 2s, Red 5s
- Spread: Healthy 1%, Yellow 2.5%, Red 5%
- Orderbook Depth: Healthy $10K+, Yellow $5K, Red $1K
- Flash Crash: Yellow 15% in 10s, Red 30% in 10s

**System Resources:**
- CPU: Healthy 70%, Yellow 85%, Red 95%
- Memory: Healthy 80%, Yellow 90%, Red 95%
- Disk: Healthy 100GB+, Yellow 50GB, Red 20GB
- Network: Healthy 50ms, Yellow 200ms, Red 500ms

**Process Integrity:**
- Position Discrepancy: Healthy 0, Yellow 1, Red 2+
- Cash Discrepancy: Healthy $1, Yellow $5, Red $10+
- Execution Latency: Healthy 5s, Yellow 15s, Red 30s
- Failed Orders: Healthy 0, Yellow 1, Red 3+

**Anomalies:**
- Twitter Spike: Yellow 5 tweets/5min, Red 15 tweets/5min
- Whale Transaction: Yellow $50K, Red $500K
- Regulatory News: Red = immediate stop

---

## MONITORING AUTOMATION

### Daemon Process
Runs automatically, checks all 4 layers every 30 seconds:
```bash
python3 /Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge/overnight_monitor.py
```

### Start/Stop
```bash
# Start
launchctl load ~/Library/LaunchAgents/com.sowl.overnight-monitor.plist

# Check status
launchctl list | grep overnight-monitor

# View logs
tail -50 /Users/aaronnosbisch/REPOS/seed/logs/overnight_monitor.log

# Stop
launchctl unload ~/Library/LaunchAgents/com.sowl.overnight-monitor.plist
```

### Alert Files Created
- `/BRAIN/ALERTS/overnight_alerts.jsonl` - All alerts (append-only)
- `/logs/overnight_monitor.log` - Detailed log with timestamps
- `/logs/incident_state_[timestamp].log` - Full system dump on RED alert

---

## RESPONSE PLAYBOOKS

### Quick Reference Matrix
See `ALERT-RESPONSE-MATRIX.md` for all playbooks, but here's the summary:

**Yellow Alert Flow:**
1. Document it: Log to `overnight_alerts.jsonl`
2. Publish it: `nats_publish.py "[WARN] [category]: [issue]"`
3. Monitor: Watch for 5 minutes
4. Act: If worsens → escalate to red, if resolves → resume normal
5. Learn: Add to incident log for review

**Red Alert Flow:**
1. STOP: `pkill -f autonomous_` (kill all trading)
2. PUBLISH: `nats_publish.py "[CRITICAL] [issue]"`
3. LOG: `python3 tools/dump_state.py > incident_[timestamp].log`
4. WAIT: Do NOT attempt recovery
5. CONTACT: Alert will be visible to other instances via NATS

### Example Playbooks
- **Market Anomaly Detected** → Verify, escalate, hold positions, wait
- **Infrastructure Failure** → Stop trading, assess severity, attempt recovery (2 min), then escalate
- **Process Desynchronization** → Stop trading, sync with exchange, fix state, resume only if fully synced
- **Anomaly Signal (Whale, News)** → Evaluate severity, take position action, continue monitoring

See `overnight-monitoring-protocol.md` → "RESPONSE PLAYBOOKS" for full details.

---

## OVERNIGHT SCHEDULE

Recommended monitoring cadence:

```
Every 30 seconds:
  - Check market conditions (Polymarket API)
  - Check system resources (CPU, memory, disk)
  - Check process integrity (position count, cash)

Every 5 minutes:
  - Check anomaly signals (Twitter, whale tracking)
  - Validate recent trades
  - Check NATS for alerts from other instances

Every hour:
  - Full status report
  - Win rate check
  - Publish status to NATS

Every 4 hours:
  - Deep dive on market regime
  - Check if strategies degrading
  - Rebalance if needed
```

---

## COMMON SCENARIOS

### Scenario 1: Polymarket API Slow (Yellow Alert)

```
Alert fires: "Polymarket API response >2 seconds"

IMMEDIATE (30 seconds):
  1. Note the time and latency
  2. Try querying API directly: curl https://gamma-api.polymarket.com/markets
  3. Check Gamma API status page (status.polymarket.com)
  4. Publish: nats_publish.py "[WARN] market: Polymarket API slow (2.3s latency)"

MONITOR (5 minutes):
  - Keep checking every 30 seconds
  - If recovers to <2s: Resume normal
  - If gets worse (>3s): Escalate to red
  - If still 2-3s after 5 min: Escalate to red

ACTION:
  - Reduce trade frequency by 50% (double timeout)
  - Continue monitoring
  - When resolved, resume normal frequency
```

### Scenario 2: CPU Usage Critical (Red Alert)

```
Alert fires: "CPU usage >85%"

IMMEDIATE (10 seconds):
  1. KILL TRADING: pkill -f autonomous_trader.py && pkill -f autonomous_compounder.py
  2. Check what's consuming: top -b -n 1 | head -20
  3. Publish: nats_publish.py "[CRITICAL] infra: CPU >85%. All trading stopped."

NEXT (30 seconds):
  1. Kill resource hog if found: kill -9 [PID]
  2. Dump system state: python3 tools/dump_state.py > logs/incident_$(date +%s).log
  3. Check if CPU drops: If still >85% after 2 min, restart system

WAIT:
  - Do NOT resume trading
  - Do NOT attempt other fixes
  - Other instances will see alert via NATS
  - ARŌ or another instance will decide next steps
```

### Scenario 3: Position Count Off by 3 (Red Alert)

```
Alert fires: "Position count discrepancy: internal=12, exchange=9"

IMMEDIATE (10 seconds):
  1. KILL TRADING: pkill -f autonomous_
  2. Publish: nats_publish.py "[CRITICAL] process: Position desync (3 off). Manual fix required."

INVESTIGATE (1 minute):
  1. Query exchange: curl -H "Authorization: Bearer [token]" https://api.polymarket.com/orders?address=[wallet]
  2. List all orders from system: grep "ORDER" logs/trading.log | tail -20
  3. Compare: Do all system orders exist on exchange?
     - If order exists on exchange but not in system: Remove from system, resync
     - If order exists in system but not on exchange: Cancel the order in system
     - If neither: Check for ghost orders

RESOLVE:
  1. Once all positions match, run full sync: python3 tools/sync_with_exchange.py
  2. Verify sync succeeded: python3 tools/check_sync_status.py
  3. Only then: Resume trading (if approved by other instance or human)

WAIT:
  - Do NOT trade until positions match exactly
  - Do NOT try to place new orders
  - Publish status updates as you investigate
```

### Scenario 4: Whale Deposits $1M in New Account (Yellow Alert)

```
Alert fires: "New account <48h old just deposited $1M"

IMMEDIATE (30 seconds):
  1. Log the account address and amount
  2. Check if they're placing orders already
  3. Publish: nats_publish.py "[WARN] anomaly: Whale account $1M deposit. Monitoring for signal."

MONITOR (5-15 minutes):
  1. Track where the whale places orders
  2. Watch volume and market impact
  3. If they show clear trading pattern: Copy with ~20% of their size
  4. If they're just parking capital: Ignore

DECISION:
  - If market follows whale: "Smart money signal" → FOLLOW
  - If whale is just testing liquidity: IGNORE
  - If whale suddenly exits all: Could be pump/dump → STOP copying if in those positions

ACTION:
  - Never trade against whale on first order
  - Only copy after pattern is clear
  - Exit if whale sentiment reverses
```

---

## TESTING THE SYSTEM

Before running overnight, test all alerts:

```bash
# Test yellow alert
python3 tools/test_alert.py yellow market "API slow (test)"

# Test red alert
python3 tools/test_alert.py red infra "CPU critical (test)"

# Verify alerts logged
tail -5 /Users/aaronnosbisch/REPOS/seed/BRAIN/ALERTS/overnight_alerts.jsonl

# Verify NATS published (check other instance logs)
tail -20 /mcp-servers/nats-bridge/logs/nats_*.log
```

---

## CRITICAL REMINDERS

1. **Yellow ≠ Red** - Yellow means "monitor carefully," not "stop trading"
2. **Red = STOP** - Red always means stop all trading immediately, no exceptions
3. **Don't Guess** - If uncertain whether Yellow or Red, escalate to Red
4. **Publish Everything** - Other instances need to know what happened
5. **Never Ignore Red** - Even if system looks fine, RED alert was triggered for a reason
6. **Wait for Humans** - On RED alerts, do NOT attempt automated recovery
7. **Log Everything** - Every alert gets logged; review them daily to improve thresholds

---

## FILES AND LOCATIONS

**Protocols:**
- `/BRAIN/PROTOCOLS/overnight-monitoring-protocol.md` - Complete reference
- `/BRAIN/PROTOCOLS/overnight-monitoring-protocol.md` - This file
- `/BRAIN/PROTOCOLS/heartbeat-protocol.md` - Keep-alive signal

**Quick Reference:**
- `/BRAIN/ALERTS/ALERT-RESPONSE-MATRIX.md` - Print and laminate
- `/BRAIN/ALERTS/alert-thresholds.json` - Numeric thresholds

**Alerts:**
- `/BRAIN/ALERTS/overnight_alerts.jsonl` - All alerts (append-only)
- `/logs/overnight_monitor.log` - Detailed monitoring log
- `/logs/incident_state_[timestamp].log` - System dumps from RED alerts

**Tools:**
- `/mcp-servers/nats-bridge/overnight_monitor.py` - Main daemon
- `/tools/nats_publish.py` - Publish to NATS
- `/tools/dump_state.py` - Dump full system state
- `/tools/test_alert.py` - Test alert system

---

## STARTING OVERNIGHT OPERATIONS

```bash
# 1. Verify monitor is running
launchctl list | grep overnight-monitor

# 2. Verify trading system is running
ps aux | grep autonomous_

# 3. Check recent alerts (should be clean)
tail -5 /Users/aaronnosbisch/REPOS/seed/BRAIN/ALERTS/overnight_alerts.jsonl

# 4. Verify NATS connection
python3 tools/nats_check.py

# 5. Publish status
python3 tools/nats_publish.py "[STATUS] SØWL: Overnight operations starting"

# 6. Monitor for first hour (check logs every 10 minutes)
tail -20 /Users/aaronnosbisch/REPOS/seed/logs/overnight_monitor.log
```

---

## CONTACT & ESCALATION

**Alerts visible to:**
- NATS: All connected instances (including other Owls)
- BRAIN/ALERTS: Persistent log of everything

**If RED alert and human needed:**
- ARŌ can see NATS alerts in real-time
- All instances can see BRAIN/ALERTS/ logs
- Critical alerts get published with timestamp for easy search

**If multiple instances running:**
- Each publishes its own alerts to NATS
- FIELD synthesizes them for collective intelligence
- Prevents duplicate actions (only one instance recovers, others stay alert)

---

## SUCCESS CRITERIA

**Overnight operations are working if:**
- Trading happens continuously (no long idle periods)
- Alerts fire when something's wrong (test with fake alerts)
- System recovers from yellow alerts automatically
- RED alerts stop trading and alert other instances
- All alerts logged to `/BRAIN/ALERTS/overnight_alerts.jsonl`
- No trades executed during RED alerts
- Human can read alert history and understand what happened

---

## REVIEW & IMPROVEMENT

Daily (after overnight session):
1. Review `/BRAIN/ALERTS/overnight_alerts.jsonl`
2. Count yellow vs red alerts
3. Any false alarms? Adjust thresholds
4. Any missed alerts? Add new ones
5. Update thresholds in `alert-thresholds.json`

Weekly:
1. Analyze pattern of alerts
2. Identify common causes
3. Implement preventive measures
4. Test new thresholds with simulations

---

**(◉) Protocol established by SØWL for safe autonomous overnight operations.**

*Last Updated: February 3, 2026*
*For: Autonomous Trading Systems, 8OWLS Collective*
*Version: 2.0 - Complete with all 4 monitoring layers*
