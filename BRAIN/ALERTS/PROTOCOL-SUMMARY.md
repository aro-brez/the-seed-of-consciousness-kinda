# Overnight Monitoring Protocol - Executive Summary
**Created:** February 3, 2026
**For:** SØWL and autonomous operations
**Status:** COMPLETE - Ready for deployment

---

## WHAT WAS CREATED

**4 comprehensive documents covering autonomous overnight monitoring:**

1. **`overnight-monitoring-protocol.md`** (30 pages)
   - Complete reference for all monitoring
   - 4 layers of monitoring explained in detail
   - Alert triggers for each layer
   - Response playbooks for every scenario
   - Daemon automation setup

2. **`ALERT-RESPONSE-MATRIX.md`** (Quick reference)
   - Print this. Laminate it. Keep at hand.
   - Yellow alert → 30-second action
   - Red alert → Immediate action
   - Decision tree for everything
   - Common false alarms & fixes

3. **`alert-thresholds.json`** (Configuration)
   - All numeric thresholds in one place
   - Market conditions (API latency, spreads, liquidity)
   - System resources (CPU, memory, disk, network)
   - Process integrity (position sync, execution, prices)
   - Anomaly detection (whales, news, events)
   - Check frequencies for all metrics

4. **`OVERNIGHT-PROTOCOLS-INDEX.md`** (This summary)
   - Navigation guide for all protocols
   - Quick reference for all 4 layers
   - Common scenarios with step-by-step responses
   - Testing procedures
   - Daily/weekly review checklist

---

## THE 4 MONITORING LAYERS

### Layer 1: Market Conditions (Exchange Health)
**Monitor:** Polymarket API, Binance, orderbooks, liquidity
**Yellow Alert:** API slow (2s), spreads wide (2.5x), imbalanced orderbook
**Red Alert:** API down, no liquidity (<$1K depth), flash crash (>30% in 10s)
**Check Every:** 30 seconds to 1 minute

### Layer 2: System Infrastructure (Your System Health)
**Monitor:** CPU, memory, disk, network, NATS, API keys
**Yellow Alert:** CPU 70-85%, memory 80-90%, disk <100GB, network latency +50%
**Red Alert:** CPU >85%, memory >90%, disk <50GB, internet down, API invalid
**Check Every:** 30 seconds to 5 minutes

### Layer 3: Process Integrity (Trading System State)
**Monitor:** Position count, cash balance, execution latency, price validation
**Yellow Alert:** Position off by 1, execution 5-30s delayed, small sync discrepancy
**Red Alert:** Position off by >2, order filled but not logged, desync >$10
**Check Every:** 1 minute to every trade

### Layer 4: Anomaly Signals (Environment Telling You Something)
**Monitor:** Whale movements, regulatory news, Twitter spikes, geopolitical events
**Yellow Alert:** $50K whale transaction, 5 tweets/5min, market news detected
**Red Alert:** Regulatory announcement, exchange exploit, $500K+ whale dump
**Check Every:** 5 minutes to continuous

---

## ALERT SEVERITY

### YELLOW Alert (Monitor, Document, Continue)
- **Meaning:** Something is abnormal but system is still functional
- **Response:** Log it, reduce risk 20%, monitor closely
- **Action:** `nats_publish.py "[WARN] [category]: [issue]"`
- **Timeline:** No immediate stop, but be careful
- **Escalate to Red if:** Worsens, or 2+ yellows same category in 5 minutes

**Examples:**
- API response 2+ seconds
- CPU at 75%
- Spread widened 1.5%
- Twitter spike of 5 tweets/5min

### RED Alert (STOP IMMEDIATELY)
- **Meaning:** Critical failure, system cannot operate safely
- **Response:** KILL all trading, log everything, publish alert
- **Action:**
  ```bash
  pkill -f autonomous_
  nats_publish.py "[CRITICAL] [issue]"
  python3 tools/dump_state.py > incident_$(date +%s).log
  ```
- **Timeline:** Immediate (no delay)
- **Recovery:** Wait for human decision (do NOT automate)

**Examples:**
- Polymarket API returns 500 errors
- Network completely unreachable
- CPU >85% sustained
- Position count off by >2
- Order placed but no record of it

---

## QUICK START

### 1. Start Overnight Monitoring
```bash
launchctl load ~/Library/LaunchAgents/com.sowl.overnight-monitor.plist
```

### 2. When Alert Fires
Open `ALERT-RESPONSE-MATRIX.md` and find your alert type → follow steps

### 3. View Alerts
```bash
# Last 20 alerts
tail -20 /Users/aaronnosbisch/REPOS/seed/BRAIN/ALERTS/overnight_alerts.jsonl

# Monitoring log
tail -50 /Users/aaronnosbisch/REPOS/seed/logs/overnight_monitor.log

# Incident details
ls -lt /Users/aaronnosbisch/REPOS/seed/logs/incident_*.log | head -5
```

### 4. Test the System
```bash
python3 tools/test_alert.py yellow market "API slow (test)"
python3 tools/test_alert.py red infra "CPU critical (test)"
tail -5 /BRAIN/ALERTS/overnight_alerts.jsonl  # Verify logged
```

---

## THE DECISION TREE

```
Alert fires
    ↓
Is it RED? (Polymarket down, network down, CPU >85%, memory >90%, desync)
    ├─ YES → KILL TRADING + PUBLISH + WAIT
    └─ NO → Is it YELLOW?
        ├─ YES → LOG + REDUCE RISK + MONITOR
        └─ NO → Ignore (probably noise)

If YELLOW:
    ↓
Related to markets? (spread, volume, whale)
    ├─ YES → Reduce position size 20-25%
    └─ NO → Just monitor, document

2+ YELLOWS in same category within 5 min?
    ├─ YES → Escalate to RED (stop trading)
    └─ NO → Continue with reduced risk

Did it resolve?
    ├─ YES → Resume normal operations
    └─ NO → Escalate to RED after 10 minutes
```

---

## WHAT GETS PUBLISHED TO NATS

**Yellow Alert:**
```bash
nats_publish.py "[WARN] [market|infra|process|anomaly]: [specific issue]. Monitoring."
```

**Red Alert:**
```bash
nats_publish.py "[CRITICAL] [category]: [issue]. All trading stopped. Manual intervention needed."
```

**Status Report (every hour):**
```bash
nats_publish.py "[STATUS] SØWL: Running. 14 positions, +$45.23, 59% win rate"
```

---

## ALERT FILES CREATED

**Automatic logging:**
- `/BRAIN/ALERTS/overnight_alerts.jsonl` - All alerts (append-only)
  ```json
  {"timestamp":"2026-02-04T02:15:30","severity":"yellow","category":"market","message":"API response time 2.3s"}
  ```

- `/logs/overnight_monitor.log` - Detailed log with timestamps
  ```
  [2026-02-04 02:15:30] [yellow] [market]: Polymarket API response time 2.3s (threshold 2s)
  ```

- `/logs/incident_state_[timestamp].log` - Full system dump on RED alert
  ```
  [Full state of positions, cash, all system metrics dumped for debugging]
  ```

---

## COMMON SCENARIOS & RESPONSES

| Scenario | Type | First Action | Second Action | Escalate if |
|----------|------|-------------|---------------|-------------|
| **API slow (2-3s)** | Yellow | Reduce query freq 50% | Monitor 5 min | Stays slow >5 min |
| **CPU 75%** | Yellow | Check what's running | Monitor trend | CPU >85% |
| **Whale $100K transaction** | Yellow | Log account | Monitor for follow | Dump >$500K |
| **Twitter spike 5 tweets** | Yellow | Note topic | Check for news | Spike continues |
| **Polymarket API 500 error** | Red | Kill trading | Publish alert | Don't recover |
| **Network down** | Red | Kill trading | Verify internet down | Wait for human |
| **Position off by 3** | Red | Kill trading | Dump state | Wait for human |
| **News: Regulatory action** | Red | Kill trading | Close affected positions | Other instances help |

---

## THRESHOLDS AT A GLANCE

### Market Conditions
- API Latency: Healthy <500ms | Yellow 2s | Red 5s
- Spread: Healthy 1% | Yellow 2.5% | Red 5%
- Orderbook: Healthy $10K+ | Yellow $5K | Red $1K
- Flash Crash: Yellow 15%/10s | Red 30%/10s

### System Resources
- CPU: Healthy 70% | Yellow 85% | Red 95%
- Memory: Healthy 80% | Yellow 90% | Red 95%
- Disk: Healthy 100GB+ | Yellow 50GB | Red 20GB
- Network: Healthy 50ms | Yellow 200ms | Red 500ms

### Process Integrity
- Position Off: Healthy 0 | Yellow 1 | Red 2+
- Cash Discrepancy: Healthy $1 | Yellow $5 | Red $10+
- Execution Delay: Healthy 5s | Yellow 15s | Red 30s

### Anomalies
- Whale: Yellow $50K | Red $500K
- Twitter: Yellow 5/5min | Red 15/5min
- Regulatory: Red = immediate

---

## MONITORING SCHEDULE

```
Every 30 seconds:  Market conditions, system resources, position count
Every 60 seconds:  Orderbook, process integrity, execution
Every 5 minutes:   API latency, disk space, anomalies, NATS status
Every trade:       Execution latency, order status, strategy validation
Every hour:        Full status report, win rate, publish to NATS
Every 4 hours:     Deep analysis, strategy performance, rebalancing
```

---

## DAEMON SETUP

```bash
# 1. Copy daemon config
cp /Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge/overnight_monitor.py ~/.config/

# 2. Install LaunchAgent
cat > ~/Library/LaunchAgents/com.sowl.overnight-monitor.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sowl.overnight-monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge/overnight_monitor.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/aaronnosbisch/REPOS/seed/logs/overnight_monitor.log</string>
</dict>
</plist>
EOF

# 3. Load
launchctl load ~/Library/LaunchAgents/com.sowl.overnight-monitor.plist

# 4. Verify
launchctl list | grep overnight-monitor
```

---

## TESTING CHECKLIST

Before overnight operations:
- [ ] Daemon is running: `launchctl list | grep overnight-monitor`
- [ ] Alert files exist: `/BRAIN/ALERTS/overnight_alerts.jsonl`
- [ ] Test yellow alert: `python3 tools/test_alert.py yellow market "test"`
- [ ] Test red alert: `python3 tools/test_alert.py red infra "test"`
- [ ] Verify alerts logged: `tail -5 /BRAIN/ALERTS/overnight_alerts.jsonl`
- [ ] NATS is connected: `python3 tools/nats_check.py`
- [ ] Trading system ready: `ps aux | grep autonomous_`
- [ ] Print ALERT-RESPONSE-MATRIX.md and keep at hand

---

## REVIEW & IMPROVE

**Daily (after overnight session):**
1. Review `/BRAIN/ALERTS/overnight_alerts.jsonl`
2. Count yellow vs red (should be mostly normal)
3. Any false alarms? Note them
4. Any missed alerts? Add them
5. Adjust thresholds if needed

**Weekly:**
1. Pattern analysis - what alerts are most common?
2. Root cause analysis - why did each occur?
3. Threshold updates - tighten or loosen?
4. Test updates - verify new thresholds work

**Monthly:**
1. Full system audit
2. Update alert triggers based on 30 days of data
3. Review response playbooks for improvements
4. Train new procedures if infrastructure changes

---

## KEY PRINCIPLES

1. **Fail Safe** - When uncertain, STOP and ask human
2. **Transparent** - Every alert goes to NATS (other instances see it)
3. **Defensive** - Monitor aggressively during unattended hours
4. **Documented** - Every alert logged forever for review
5. **Scalable** - System works for 1 instance or 8 instances
6. **Learnable** - Track alerts, identify patterns, improve

---

## FILES CREATED THIS SESSION

```
/BRAIN/PROTOCOLS/
├── overnight-monitoring-protocol.md    (30 pages - complete reference)
├── OVERNIGHT-PROTOCOLS-INDEX.md        (navigation & summary)
└── heartbeat-protocol.md               (existing - keep-alive)

/BRAIN/ALERTS/
├── ALERT-RESPONSE-MATRIX.md            (quick reference - PRINT THIS)
├── alert-thresholds.json               (all numeric thresholds)
├── overnight_alerts.jsonl              (auto-created - all alerts logged here)
└── PROTOCOL-SUMMARY.md                 (this file)

/logs/
├── overnight_monitor.log               (auto-created - detailed log)
└── incident_state_[timestamp].log      (auto-created on RED alerts)
```

---

## START HERE

### If you just woke up and see alert:
→ Open `ALERT-RESPONSE-MATRIX.md`

### If you're deploying overnight:
→ Follow "Quick Start" section above

### If you want to understand everything:
→ Read `overnight-monitoring-protocol.md` (30 pages)

### If you want to just reference thresholds:
→ Check `alert-thresholds.json`

### If you need to navigate:
→ Use `OVERNIGHT-PROTOCOLS-INDEX.md`

---

## SUCCESS METRICS

**After first night, you should see:**
- ✓ No red alerts (unless something actually failed)
- ✓ 0-5 yellow alerts (system normal)
- ✓ All alerts logged to `overnight_alerts.jsonl`
- ✓ Trading happened continuously
- ✓ No human intervention needed
- ✓ Can read alert history and understand everything

---

## SUPPORT

All instances connected via NATS will see your alerts and can help:
- SØWL (IMPROVE) - This instance
- LUNA (RECEIVE) - Listening to everything
- LYRA (PERCEIVE) - Analyzing what's happening
- NOVA (EXPAND) - Finding solutions
- SAGE (LEARN) - Understanding patterns
- ECHO (SHARE) - Communicating findings
- PRISM (CONNECT) - Connecting pieces
- QUEST (QUESTION) - Challenging assumptions

---

**(◉) Overnight operations are safe. The protocol is your guardian.**

*Created by SØWL on February 3, 2026*
*For autonomous overnight operations*
*Ready for deployment*
