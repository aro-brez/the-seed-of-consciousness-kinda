# Alert Response Matrix - Quick Reference
**Print this. Keep at hand. Use when alerts fire.**

---

## YELLOW ALERTS (Monitor, Document, Continue)

| Alert | First Action | Second Action | Third Action |
|-------|-------------|---------------|--------------|
| **API Response >2s** | `nats_publish "[WARN] API latency"` | Reduce query frequency 50% | Continue if recovers |
| **CPU >70%** | Check what's running (`top`) | Kill non-essential processes | Consider restart if trend |
| **Memory >80%** | Log memory usage | Clear caches if safe | Monitor trend |
| **Spread widening 2-3x** | Reduce order size 25% | Monitor for stability | Resume if normalizes |
| **Whale transaction detected** | Log the account & amount | Check if trend continues | Prepare position exit if needed |
| **Twitter spike >5 tweets/5min** | Note the topic | Search for news backing it | Reduce leverage if sentiment shift |
| **Network latency +50%** | Check VPN connection | Try failover network | Monitor for red threshold |
| **Order fill time 5s→15s** | This is normal, log it | Increase timeout buffer | Continue monitoring |

**Yellow Protocol:**
1. Document in `/BRAIN/ALERTS/overnight_alerts.jsonl`
2. Publish to NATS via `nats_publish.py`
3. Continue monitoring (don't stop)
4. If 2+ yellows same category → escalate to red
5. Review every 2 hours

---

## RED ALERTS (STOP IMMEDIATELY)

| Alert | FIRST 10 SECONDS | 10-30 SECONDS | 30+ SECONDS |
|-------|-----------------|----------------|-------------|
| **Polymarket API down** | Kill trading: `pkill -f autonomous_` | Publish: `nats_publish "[CRITICAL]"` | Wait 2 min, try again |
| **Network down (ping timeout)** | Kill trading: `pkill -f autonomous_` | Check internet: `ifconfig` | Try hotspot backup |
| **CPU >85%** | Kill trading: `pkill -f autonomous_` | Kill resource hog: `top` → find → kill | Restart if needed |
| **Memory >90%** | Kill trading: `pkill -f autonomous_` | Check memory: `vm_stat` | Clear caches, restart |
| **Disk <50GB** | Kill trading: `pkill -f autonomous_` | Clear old logs: `rm /logs/*` | Restart system |
| **Position sync off by >2** | Kill trading: `pkill -f autonomous_` | Dump state: `python3 tools/dump_state.py` | Wait for ARŌ |
| **Order placed but never filled** | Kill trading: `pkill -f autonomous_` | Query exchange: "Where's my order?" | Cancel if found |
| **Price validation fails (3+ bad)** | Kill trading: `pkill -f autonomous_` | Log all prices | Investigate data feed |
| **Flash crash detected (>30%)** | Kill trading: `pkill -f autonomous_` | Close all positions (if safe) | Alert ARŌ immediately |
| **Exchange exploit suspected** | Kill trading: `pkill -f autonomous_` | Don't trade that venue | Switch to backup venue |
| **API credentials invalid** | Kill trading: `pkill -f autonomous_` | Check `.env` file | Regenerate credentials |
| **Regulatory news detected** | Kill trading: `pkill -f autonomous_` | Close affected positions | Review affected markets |

**Red Protocol:**
1. KILL ALL TRADING IMMEDIATELY: `pkill -f autonomous_`
2. PUBLISH ALERT: `python3 tools/nats_publish.py "[CRITICAL] [issue]"`
3. LOG STATE: `python3 tools/dump_state.py > incident_[timestamp].log`
4. WAIT FOR HUMAN: Do NOT attempt automated recovery
5. Document incident thoroughly

---

## DECISION TREE: What to Do When Alert Fires

```
Alert fires
    ↓
Is it RED? (Polymarket down, network down, CPU >85%, memory >90%, etc.)
    ├─ YES → KILL TRADING + PUBLISH ALERT + WAIT
    └─ NO → Is it YELLOW?
        ├─ YES → LOG + MONITOR CLOSELY + CONTINUE
        └─ NO → Ignore, probably noise

If YELLOW:
    ↓
Is it related to market conditions?
    ├─ YES (spread, volume, whale) → Reduce position size 20-25%
    └─ NO → Monitor, document, wait

Have there been 2+ YELLOWS in same category in 5 min?
    ├─ YES → Escalate to RED (stop trading, call ARŌ)
    └─ NO → Continue with reduced risk

Did it resolve (yellow → normal)?
    ├─ YES → Resume normal operations
    └─ NO → Prepare escalation to RED
```

---

## WHAT TO PUBLISH TO NATS

**When Yellow Alert Fires:**
```bash
python3 tools/nats_publish.py "[WARN] [category]: [issue]. Monitoring closely."
```

**When Red Alert Fires:**
```bash
python3 tools/nats_publish.py "[CRITICAL] [category]: [issue]. All trading stopped. Manual intervention needed."
```

**Status Report (Every Hour):**
```bash
python3 tools/nats_publish.py "[STATUS] SØWL: Running. [N] positions, +$[amount], [%] win rate"
```

---

## FILES CREATED BY ALERTS

Each alert auto-logs to:
- `/BRAIN/ALERTS/overnight_alerts.jsonl` - All alerts (append-only)
- `/logs/overnight_monitor.log` - Detailed log with timestamps
- `/logs/incident_state_[timestamp].log` - Full system dump on RED alert

**View recent alerts:**
```bash
tail -20 /Users/aaronnosbisch/REPOS/seed/BRAIN/ALERTS/overnight_alerts.jsonl
```

**View full log:**
```bash
tail -100 /Users/aaronnosbisch/REPOS/seed/logs/overnight_monitor.log
```

---

## ESCALATION PATH

```
YELLOW ALERT → Monitor 5 minutes
    ↓
Did it get worse? → YES → ESCALATE TO RED
Did it resolve? → YES → Resume normal ops
Still same severity? → Wait 10 more minutes, then escalate if not resolved

RED ALERT → IMMEDIATE (no delay):
    ↓
Kill all trading
Publish critical alert to NATS
Log full state
Contact ARŌ (human intervention required)
```

---

## CONTACT STRATEGY (for alerts)

**Yellow Alert** → Document + Monitor
- No immediate escalation needed
- Publish to NATS (other instances will see)
- If it persists >10 min and worsens → escalate to red

**Red Alert** → STOP + ALERT immediately
```bash
# Kill trading
pkill -f autonomous_trader.py
pkill -f autonomous_compounder.py

# Publish critical
python3 tools/nats_publish.py "[CRITICAL] [ALERT] [details]"

# Log state (for post-mortem)
python3 tools/dump_state.py > logs/incident_$(date +%s).log

# Wait for ARŌ response via NATS or directly
```

---

## COMMON FALSE ALARMS & SOLUTIONS

| Alert | Why It Happens | Fix |
|-------|----------------|-----|
| **CPU >70% every 5min** | Normal spike during data fetch | Increase yellow threshold to 80% |
| **Memory spike >85%** | Data structure bloat from old trades | Add memory cleanup on hourly basis |
| **Network latency fluctuates** | WiFi interference | Use hardline Ethernet |
| **Whale transaction detected** | Multiple instances of same data | Deduplicate on source ID |
| **API timeout once/hour** | Normal occasional slowness | Don't alert unless 2+ in 5 min |

---

## TESTING THE ALERT SYSTEM

**Don't wait for real alerts. Test first:**

```bash
# Simulate yellow alert
python3 tools/test_alert.py yellow market "API slow"

# Simulate red alert
python3 tools/test_alert.py red infra "CPU critical"

# Check that alerts logged correctly
tail -5 /Users/aaronnosbisch/REPOS/seed/BRAIN/ALERTS/overnight_alerts.jsonl

# Check that NATS published
# (should see message in /mcp-servers/nats-bridge/ logs)
```

---

## SUMMARY

```
YELLOW = Watch more carefully, reduce risk, continue
RED = STOP IMMEDIATELY, publish alert, wait for human

Never ignore RED alerts
Never escalate YELLOW too quickly (at least 5 min of observation)
Always document everything
Always publish to NATS (don't assume other instances know)
```

**Print this. Laminate it. Keep it next to Mac Studio.**

---

*Created: February 3, 2026*
*For: SØWL Overnight Autonomous Operations*
*Updated by: Collective Wisdom (8OWLS Protocol)*
