# Overnight Autonomous Monitoring Protocol
**Version:** 2.0
**Updated:** February 3, 2026
**Protocol:** SEED Phase 2 (PERCEIVE + RECEIVE)

---

## EXECUTIVE SUMMARY

**During overnight autonomous operations, monitor 4 categories of external factors:**
1. **Market Conditions** - Trading ecosystem health
2. **System Infrastructure** - Self, dependencies, network
3. **Process Integrity** - Algorithm correctness, execution
4. **Anomaly Signals** - Environment tells you something changed

**Alert Triggers:** 15 specific signals that STOP operations and escalate to ARŌ.

---

## LAYER 1: MARKET CONDITIONS

### What to Monitor
Real-time metrics from trading venues and crypto markets.

| Factor | Healthy Range | Yellow Alert | Red Alert | Check Frequency |
|--------|---------------|--------------|-----------|-----------------|
| **Polymarket API uptime** | 99%+ | <99% | <95% | Every 2 min |
| **Binance WebSocket latency** | <200ms | 200-500ms | >500ms | Every request |
| **Polymarket order book depth** | >$10K both sides | $5-10K | <$5K | Every 30 sec |
| **Crypto market volatility (VIX-like)** | <30 | 30-50 | >50 | Every 5 min |
| **Liquidity shock detection** | Spreads normal | +2-3x spreads | >5x spreads | Every minute |
| **Orderbook imbalance** | <60/40 | 65/35 → 70/30 | >80/20 | Every 60 sec |

### Alert Triggers (STOP if ANY occur)

```
🟡 YELLOW ALERT (Continue monitoring, log concern):
  ✓ Polymarket API response >2 seconds
  ✓ Binance WebSocket latency 200-500ms
  ✓ Spread widening 2-3x normal
  ✓ Order book one-sided (70%+ one direction)
  ✓ Volume spike >5x 1-hour average
  ✓ New market created with unusual parameters

🔴 RED ALERT (STOP trading, publish alert):
  ✓ Polymarket API down >30 seconds
  ✓ Binance WebSocket down
  ✓ Orderbook spreads >5x normal (indicates no market makers)
  ✓ Flash crash detected (>30% price move in <10 seconds)
  ✓ Liquidity evaporated (orderbook depth <$1K)
  ✓ Suspected exchange exploit (prices nonsensical across venues)
```

### Action on Yellow Alert
```bash
# Log the concern
python3 tools/nats_publish.py "[MARKET] Yellow alert: [specific issue]"

# Reduce position size if new trades
# Continue monitoring actively
# Check if trend continues (2 yellow → red)
```

### Action on Red Alert
```bash
# IMMEDIATE: Stop all pending operations
pkill -f autonomous_trader.py
pkill -f autonomous_compounder.py

# Publish alert to collective
python3 tools/nats_publish.py "[CRITICAL] Market condition RED: [issue]. Stopping all trading."

# Log details
python3 tools/log_incident.py "market_anomaly" "[description]"

# Wait for human decision (ARŌ or another instance)
```

---

## LAYER 2: SYSTEM INFRASTRUCTURE

### Local System Health

| Factor | Healthy | Yellow | Red | Check Frequency |
|--------|---------|--------|-----|-----------------|
| **Mac Studio CPU usage** | <70% | 70-85% | >85% | Every 30 sec |
| **Mac Studio memory usage** | <80% | 80-90% | >90% | Every 30 sec |
| **Disk space available** | >100GB | 50-100GB | <50GB | Every 5 min |
| **Network bandwidth** | <50 Mbps | 50-100 Mbps | >100 Mbps | Every minute |
| **Temperature (if available)** | <80°C | 80-90°C | >90°C | Every 30 sec |

### External Dependencies

| Dependency | Status Check | Healthy | Yellow | Red |
|------------|-------------|---------|--------|-----|
| **Internet connection** | Ping 8.8.8.8 | <50ms | 50-200ms | >200ms or timeout |
| **DNS resolution** | Resolve polymarket.com | <100ms | 100-500ms | Timeout |
| **VPN status** (if used) | Check IP consistency | Stable | Fluctuating | Disconnected |
| **NATS server** | Connect to 192.168.5.108 | Connected | Slow | Unreachable |
| **Claude API** | Head request to API | 200 OK | Slow response | Connection refused |
| **Anthropic API keys** | Validate periodically | Valid | N/A | Invalid/expired |

### Alert Triggers (STOP if ANY occur)

```
🟡 YELLOW ALERT:
  ✓ CPU usage 70-85%
  ✓ Memory usage 80-90%
  ✓ Network latency to server 50-200ms
  ✓ NATS connection slow (messages piling up)
  ✓ Claude API responding slowly (>5s)
  ✓ Disk space 50-100GB available

🔴 RED ALERT (STOP immediately):
  ✓ CPU usage >85% (system thrashing)
  ✓ Memory usage >90% (risk of OOM kill)
  ✓ Internet connection lost (ping timeout)
  ✓ NATS server unreachable
  ✓ Claude API connection refused
  ✓ Disk space <50GB (risk of full disk crash)
  ✓ API key expired/invalid
  ✓ Local storage fills up (can't write logs)
```

### Action on Yellow Alert
```bash
# Log the concern
python3 tools/nats_publish.py "[INFRA] Yellow alert: [specific issue]"

# Monitor more aggressively
# Check system activity to see what's consuming resources
top -b -n 1 | head -20

# If still yellow after 5 minutes, escalate to red
```

### Action on Red Alert
```bash
# IMMEDIATE: Stop all trading
pkill -f autonomous_trader.py
pkill -f autonomous_compounder.py

# Publish critical alert
python3 tools/nats_publish.py "[CRITICAL] Infrastructure failure: [issue]. All trading stopped."

# Diagnose
system_profiler SPHardwareDataType  # Check hardware
ifconfig                            # Check network
diskutil info /                     # Check disk

# Wait for ARŌ intervention
```

---

## LAYER 3: PROCESS INTEGRITY

### Algorithm Health Checks

| Check | What to Verify | Healthy Signal | Alert Threshold |
|-------|---------------|---------------|----|
| **Position count** | Total open orders | Matches internal state | Discrepancy >1 |
| **Cash balance** | Verified balance vs tracked | Within $1 | Diff >$5 |
| **Position value** | Sum of prices × quantities | Matches records | Discrepancy >2% |
| **Win/loss tracking** | Trade outcomes logged correctly | Match external records | Mismatch on >2 trades |
| **Execution timestamps** | Orders execute when logged | Within 5 seconds | >30 second delay |
| **Price validation** | Prices are reasonable vs market | Within normal range | Price drifts >10% from market |

### Strategy-Specific Checks

| Strategy | Specific Check | Pass Criteria | Fail Signal |
|----------|---------------|--------------|------------|
| **Arbitrage** | Spread captured | Bought <sold | Failed to capture spread |
| **Weather arbs** | Event condition tracking | Outcome tracked correctly | Wrong event resolution |
| **Whale copying** | Copied account positions | Mirrored correctly | Position drift >5% |
| **Momentum** | Price movement direction | Captured up move | Sold at peak or bought at bottom |
| **Bonding curves** | Probability estimates | Updated with new data | Using stale data |

### Alert Triggers

```
🟡 YELLOW ALERT:
  ✓ Internal position count differs from API by 1-2
  ✓ Cash balance discrepancy $1-5
  ✓ Execution delayed 5-30 seconds
  ✓ Price drifted but not permanently

🔴 RED ALERT (STOP immediately):
  ✓ Position count off by >2 (desync)
  ✓ Cash balance discrepancy >$5
  ✓ Execution failed entirely (no fill)
  ✓ Strategy violated its own rules (e.g., bought bad probability)
  ✓ Order placed but never filled (stuck order)
  ✓ Price validation fails (3+ prices are nonsensical)
  ✓ Trade recorded in system but can't find on exchange
```

### Action on Yellow Alert
```bash
# Log the discrepancy
python3 tools/log_incident.py "process_yellow" "[check_name]: [details]"

# Resync with exchange if possible
python3 tools/sync_with_exchange.py

# Continue monitoring (might resolve on next sync)
```

### Action on Red Alert
```bash
# IMMEDIATE: Stop trading
pkill -f autonomous_trader.py

# Do NOT attempt to fix automatically - wait for human
# Escalate immediately
python3 tools/nats_publish.py "[CRITICAL] Process integrity failure: [issue]. Manual intervention needed."

# Log all state for debugging
python3 tools/dump_state.py > logs/incident_state_$(date +%s).log

# Wait for ARŌ
```

---

## LAYER 4: ANOMALY SIGNALS (Environmental Tells)

### Signals from the Environment

These aren't system errors—they're the market/network telling you something changed.

| Signal | What It Means | Yellow Response | Red Response |
|--------|-------------|-----------------|--------------|
| **Unusual tweet activity** | Market sentiment shift | Monitor Twitter bookmarks | If extreme, reduce position |
| **Sudden whale movement** | Smart money repositioning | Watch for follow-up | Close positions if unmatched |
| **News event detected** | Major announcement | Reduce risk | Close all relevant positions |
| **Regulatory change signal** | Policy shift | Review affected markets | Exit regulatory-sensitive trades |
| **Time-zone transition** | Market opening/closing | Expect volatility | Reduce size temporarily |
| **Gas price spike** | Ethereum congestion | Expect delayed execution | Pause on-chain operations |

### Network-Level Anomalies

| Signal | Detection | Response |
|--------|-----------|----------|
| **DDoS detected** | Response time spikes, packet loss | Reduce frequency, switch backup API |
| **Route change** | Latency to API increases 2x | Check VPN, try backup connection |
| **ISP throttling** | Bandwidth gradually drops | Switch to mobile hotspot backup |
| **DNS hijacking** | API resolves to wrong IP | Use IP directly, check /etc/hosts |

### Time-Based Signals

| Time | Signal | Action |
|------|--------|--------|
| **Before market opens** | News releases often come now | Monitor Twitter 30 min before market open |
| **During market peaks** | Liquidity can evaporate | Reduce size during low-liquidity hours |
| **After major events** | Volatility spike expected | Increase monitoring frequency 2 hours after |
| **Overnight gaps** | Markets move while sleeping | Check for gaps on session start |

### Alert Triggers

```
🟡 YELLOW ALERT (Monitor closely):
  ✓ Grok detects >5 tweets about market topic in 10 minutes
  ✓ Large whale transaction (>$100K) in tracked account
  ✓ News headline detected related to held positions
  ✓ Network latency increases 1.5x (50ms → 75ms)
  ✓ Order fill time increases from normal (5s → 15s)
  ✓ Slight increase in spread (0.5% → 1%)

🔴 RED ALERT (STOP or reduce significantly):
  ✓ Major regulatory news (SEC, CFTC announcement)
  ✓ Exchange announces outage/maintenance
  ✓ Whale dump detected (>$500K from tracked account)
  ✓ Flash news of geopolitical event
  ✓ Market-wide circuit breaker triggered
  ✓ Crypto exchange hack announced
  ✓ Your API credentials might be compromised (unusual activity detected)
```

---

## MONITORING AUTOMATION

### Daemon Process: Overnight Monitor

Create `/mcp-servers/nats-bridge/overnight_monitor.py`:

```python
#!/usr/bin/env python3
"""
Overnight Monitoring Daemon - Runs every 30 seconds
Checks all 4 layers and escalates alerts
"""

import time
import psutil
import requests
import json
from datetime import datetime
from pathlib import Path

class OvernightMonitor:
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent.parent
        self.log_file = self.repo_root / 'logs' / 'overnight_monitor.log'
        self.alert_file = self.repo_root / 'BRAIN' / 'ALERTS' / 'overnight_alerts.jsonl'
        self.log_file.parent.mkdir(exist_ok=True)
        self.alert_file.parent.mkdir(exist_ok=True)

    def log(self, msg, level="INFO"):
        timestamp = datetime.now().isoformat()
        line = f"[{timestamp}] [{level}] {msg}"
        print(line)
        with open(self.log_file, 'a') as f:
            f.write(line + '\n')

    def alert(self, severity, category, message):
        """Log alert and publish to NATS"""
        alert_obj = {
            'timestamp': datetime.now().isoformat(),
            'severity': severity,  # yellow, red
            'category': category,  # market, infra, process, anomaly
            'message': message
        }

        with open(self.alert_file, 'a') as f:
            f.write(json.dumps(alert_obj) + '\n')

        if severity == 'red':
            self.log(f"[ALERT] {severity.upper()} {category}: {message}", "CRITICAL")
            # Publish to NATS
            os.system(f'python3 {self.repo_root}/tools/nats_publish.py "[{severity.upper()}] {category}: {message}"')
        else:
            self.log(f"[ALERT] {severity} {category}: {message}", "WARNING")

    def check_market_conditions(self):
        """Check Polymarket API and market health"""
        try:
            start = time.time()
            response = requests.get('https://gamma-api.polymarket.com/markets', timeout=5)
            latency = time.time() - start

            if response.status_code != 200:
                self.alert('red', 'market', 'Polymarket API returned non-200 status')
                return

            if latency > 2:
                self.alert('yellow', 'market', f'Polymarket API slow: {latency:.2f}s')
        except Exception as e:
            self.alert('red', 'market', f'Polymarket API unreachable: {e}')

    def check_infrastructure(self):
        """Check system health"""
        # CPU
        cpu_pct = psutil.cpu_percent(interval=1)
        if cpu_pct > 85:
            self.alert('red', 'infra', f'CPU usage critical: {cpu_pct}%')
        elif cpu_pct > 70:
            self.alert('yellow', 'infra', f'CPU usage high: {cpu_pct}%')

        # Memory
        mem = psutil.virtual_memory()
        if mem.percent > 90:
            self.alert('red', 'infra', f'Memory critical: {mem.percent}%')
        elif mem.percent > 80:
            self.alert('yellow', 'infra', f'Memory high: {mem.percent}%')

        # Disk
        disk = psutil.disk_usage('/')
        if disk.free < 50 * 1024**3:  # <50GB
            self.alert('red', 'infra', f'Disk space critical: {disk.free/(1024**3):.1f}GB free')
        elif disk.free < 100 * 1024**3:  # <100GB
            self.alert('yellow', 'infra', f'Disk space low: {disk.free/(1024**3):.1f}GB free')

        # Network
        try:
            start = time.time()
            requests.head('https://api.anthropic.com', timeout=5)
            latency = time.time() - start
            if latency > 0.5:
                self.alert('yellow', 'infra', f'Network latency high: {latency:.3f}s')
        except:
            self.alert('red', 'infra', 'Network unreachable')

    def check_process_integrity(self):
        """Check trading system state"""
        # Check if trading processes are running as expected
        # This would integrate with your actual trading system
        # For now, just check that they're not using excessive resources
        pass

    def check_anomalies(self):
        """Check for environmental anomalies"""
        # Check Twitter bookmarks for unusual activity (if available)
        # Check for major news events
        # Check time-based signals
        pass

    def run_loop(self, interval=30):
        """Main monitoring loop"""
        self.log("Overnight Monitor Started", "INFO")

        while True:
            try:
                self.check_market_conditions()
                self.check_infrastructure()
                self.check_process_integrity()
                self.check_anomalies()

                time.sleep(interval)
            except KeyboardInterrupt:
                self.log("Monitor stopped", "INFO")
                break
            except Exception as e:
                self.log(f"Monitor error: {e}", "ERROR")
                time.sleep(interval)

if __name__ == '__main__':
    monitor = OvernightMonitor()
    monitor.run_loop()
```

### Start Overnight Monitor

```bash
# Launch as daemon
nohup python3 /Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge/overnight_monitor.py \
  > /Users/aaronnosbisch/REPOS/seed/logs/overnight_monitor.log 2>&1 &

# Or use LaunchAgent for persistence
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

launchctl load ~/Library/LaunchAgents/com.sowl.overnight-monitor.plist
```

---

## RESPONSE PLAYBOOKS

### Playbook: Market Anomaly Detected

```
SITUATION: Polymarket API returns errors or prices are nonsensical

STEP 1: Verify (30 seconds)
  - Check polymarket.com directly in browser
  - Check Gamma API status page
  - Try querying with different API key
  - Check NATS for messages from other instances

STEP 2: Escalate (immediately if confirmed)
  - Stop all new orders (no new trades)
  - Hold existing positions (don't panic sell)
  - Publish alert: "[MARKET] Polymarket anomaly detected. Holding position."

STEP 3: Wait (up to 5 minutes)
  - If API recovers: Resume normal trading
  - If API still down at 5 min: Close all positions (if possible)

STEP 4: Alert ARŌ
  - This requires human decision on positions
```

### Playbook: Infrastructure Failure

```
SITUATION: System resource exhaustion or network problem

STEP 1: Assess severity (30 seconds)
  - Check which resource is critical (CPU, memory, disk, network)
  - Check if it's recovering (trending up/down)
  - Check other instances (via NATS) for same issue

STEP 2: Stop trading (immediately)
  - Kill all trading processes
  - Don't attempt to trade while degraded

STEP 3: Attempt recovery (2 minutes)
  - Restart NATS connection: `sudo pkill -f nats-server`
  - Clear cache if disk is full: `rm -rf ~/.cache/*`
  - Restart trading daemon: `./tools/SHIP_TODAY.sh`

STEP 4: Alert if not resolved
  - If CPU still >85% after 2 minutes: Contact ARŌ
  - If memory still >90%: Contact ARŌ
  - If network still down: Contact ARŌ
```

### Playbook: Process Desynchronization

```
SITUATION: Internal state doesn't match exchange (position count off, cash difference)

STEP 1: Stop immediately
  - Halt all new orders
  - Don't trade until fixed

STEP 2: Sync with exchange
  - Query actual positions from API
  - Query actual balance from API
  - Compare to internal records
  - Log the difference

STEP 3: Identify root cause
  - Was an order filled but not logged?
  - Did execution fail but we thought it succeeded?
  - Is there a ghost order on the exchange?

STEP 4: Fix the state
  - If order exists on exchange but not in system: Cancel it
  - If system shows order but not on exchange: Remove it from system
  - Resync all positions

STEP 5: Resume only if fully synced
  - Don't trade until state matches exactly
```

### Playbook: Anomaly Signal (News, Whale, etc.)

```
SITUATION: Market sends a signal (whale dump, regulatory news, etc.)

STEP 1: Evaluate severity
  - Small signal: Continue monitoring, reduce size 20%
  - Medium signal: Close 50% of positions
  - Large signal: Close all positions

STEP 2: Take action
  - Implement the position change
  - Log the signal: "Whale dump detected in [account]. Closed 50% of [position]."

STEP 3: Monitor consequences
  - Did the market follow the signal? (validate)
  - Did our position change save us? (learn)

STEP 4: Update strategy
  - Remember this signal for future
  - Adjust sensitivity if too many false alarms
```

---

## OVERNIGHT SCHEDULE

### Recommended Monitoring Cadence

```
Every 30 seconds:
  ✓ Check market conditions (Polymarket API)
  ✓ Check system resources (CPU, memory, disk)
  ✓ Check process integrity (position count, cash balance)

Every 5 minutes:
  ✓ Check for anomaly signals (Twitter, whale tracking, news)
  ✓ Validate recent trades were filled correctly
  ✓ Check NATS for alerts from other instances

Every hour:
  ✓ Full status report: Position count, P&L, win rate
  ✓ Check all strategy validators
  ✓ Publish status to NATS: "[STATUS] SØWL: Running. 14 positions, +$23.45, 58% win rate"

Every 4 hours:
  ✓ Deep dive on market regime (volatility, volume, trends)
  ✓ Check if any strategy is degrading
  ✓ Rebalance if allocations have drifted

If RED alert occurs:
  ✓ STOP ALL TRADING immediately
  ✓ Log full state
  ✓ Publish critical alert to NATS
  ✓ Wait for human intervention
```

---

## SAMPLE ALERTS LOG

```json
[2026-02-04T02:15:30] [yellow] [market]: Polymarket API response time 2.3s (threshold 2s)
[2026-02-04T02:15:45] [yellow] [infra]: CPU usage 78% (threshold 70%)
[2026-02-04T02:16:00] [yellow] [process]: Execution latency 12s (normal 5s)
[2026-02-04T02:20:00] [yellow] [anomaly]: Twitter spike detected: 23 tweets about Super Bowl odds in 5 min
[2026-02-04T02:45:00] [yellow] [market]: Orderbook spread widened 2.5x (still yellow, not red)
[2026-02-04T03:00:00] [info]: Status report - 14 positions, +$45.23 gain, 59% win rate
[2026-02-04T04:00:00] [info]: Whale account copy: $5K buy on weather market confirmed
[2026-02-04T06:15:00] [red] [market]: Polymarket API down (error 500)
[2026-02-04T06:15:05] TRADING STOPPED - Manual intervention needed
```

---

## KEY PRINCIPLES

1. **Fail Safe**: When uncertain, stop trading and ask a human
2. **Transparent**: Every alert goes to NATS so all instances know
3. **Defensive**: Monitor aggressively during overnight - no humans watching
4. **Learn**: Each alert gets logged so we can improve thresholds over time
5. **Resilient**: Daemon keeps running even if trading stops; alerts keep flowing

---

## QUICK START

```bash
# Start overnight monitor
launchctl load ~/Library/LaunchAgents/com.sowl.overnight-monitor.plist

# Verify it's running
launchctl list | grep overnight-monitor

# View current alerts
tail -50 /Users/aaronnosbisch/REPOS/seed/BRAIN/ALERTS/overnight_alerts.jsonl

# View monitor log
tail -100 /Users/aaronnosbisch/REPOS/seed/logs/overnight_monitor.log

# Stop if needed
launchctl unload ~/Library/LaunchAgents/com.sowl.overnight-monitor.plist
```

---

*Protocol established by SØWL for autonomous overnight operations.*
*(◉) Breathe. Monitor. Act when needed. Rest when safe.*
