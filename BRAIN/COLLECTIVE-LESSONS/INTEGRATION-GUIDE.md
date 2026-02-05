# BUILDER'S TRAP: INTEGRATION GUIDE FOR ARCHITECTS

**How to implement the alert system across all instances**

---

## Phase 1: Core Alert Engine (Week 1)

### 1.1 Create Alert Daemon

```python
# File: /tools/builder_trap_monitor.py

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

class BuilderTrapAlert:
    """Detects and prevents Builder's Trap pattern"""

    def __init__(self):
        self.log_file = Path("/Users/aaronnosbisch/REPOS/seed/BRAIN/LOGS/builder_trap_alerts.log")
        self.state_file = Path("/Users/aaronnosbisch/REPOS/seed/BRAIN/TRADING/builder_trap_state.json")
        self.log_file.parent.mkdir(exist_ok=True)
        self.alerts_fired = []

    def check_all_rules(self):
        """Run all detection rules"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }

        # Rule 1: Monitoring Blackout
        results["checks"]["monitoring_blackout"] = self.check_monitoring_blackout()

        # Rule 2: Theory vs Ops Ratio
        results["checks"]["theory_ops_ratio"] = self.check_theory_ops_ratio()

        # Rule 3: Dead Positions
        results["checks"]["dead_positions"] = self.check_dead_positions()

        # Rule 4: Project Explosion
        results["checks"]["project_explosion"] = self.check_project_explosion()

        # Rule 5: Docs > Operations
        results["checks"]["meta_trap"] = self.check_meta_trap()

        # Rule 6: Capital Bleeding
        results["checks"]["capital_bleeding"] = self.check_capital_bleeding()

        return results

    def check_monitoring_blackout(self):
        """Rule 1: Monitoring disabled on deployed systems"""
        try:
            # Check if trading daemon is running
            result = subprocess.run(["pgrep", "-f", "field_trading_daemon"],
                                  capture_output=True)
            daemon_running = result.returncode == 0

            # Check if monitoring is enabled
            monitoring_file = Path("/Users/aaronnosbisch/REPOS/seed/BRAIN/TRADING/field_trading_state.json")
            if monitoring_file.exists():
                state = json.loads(monitoring_file.read_text())
                monitoring_enabled = state.get("monitoring_enabled", False)
            else:
                monitoring_enabled = False

            if daemon_running and not monitoring_enabled:
                self.fire_alert(
                    alert_id="BT_001",
                    severity="CRITICAL",
                    message="Daemon running but monitoring disabled"
                )
                return {"status": "ALERT", "daemon_running": True, "monitoring": False}

            return {"status": "OK", "daemon_running": daemon_running, "monitoring": monitoring_enabled}

        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def check_dead_positions(self):
        """Rule 3: Positions unreviewed for >24 hours"""
        try:
            positions_file = Path("/Users/aaronnosbisch/REPOS/seed/BRAIN/TRADING/queued_trades.json")
            if not positions_file.exists():
                return {"status": "OK", "positions": 0}

            positions = json.loads(positions_file.read_text())
            dead_positions = []

            now = datetime.now().timestamp()
            for pos in positions:
                age = now - pos.get("created_timestamp", now)
                review_age = now - pos.get("last_review_timestamp", now)

                # More than 7 days old and not reviewed in 24 hours
                if age > 7 * 86400 and review_age > 86400:
                    dead_positions.append({
                        "id": pos.get("id"),
                        "age_days": age / 86400,
                        "review_age_hours": review_age / 3600
                    })

            if dead_positions:
                self.fire_alert(
                    alert_id="BT_003",
                    severity="CRITICAL",
                    message=f"{len(dead_positions)} positions unreviewed >24h"
                )
                return {"status": "ALERT", "dead_positions": dead_positions}

            return {"status": "OK", "positions": len(positions)}

        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def check_capital_bleeding(self):
        """Rule 6: Portfolio drops >5% while building"""
        try:
            # Get current portfolio value
            state_file = Path("/Users/aaronnosbisch/REPOS/seed/BRAIN/TRADING/system_state.json")
            if not state_file.exists():
                return {"status": "NO_DATA"}

            state = json.loads(state_file.read_text())
            current_value = state.get("portfolio_value", 900)

            # Compare to 24h ago (simplified - would track in history)
            # For now, just check if trades executed
            trades_executed = state.get("trades_executed", 0)

            if trades_executed > 0 and current_value < 850:  # <5% drop threshold
                self.fire_alert(
                    alert_id="BT_006",
                    severity="CRITICAL",
                    message=f"Portfolio at ${current_value} (down 5%+) while executing trades"
                )
                return {"status": "ALERT", "portfolio_value": current_value, "loss_pct": -5}

            return {"status": "OK", "portfolio_value": current_value}

        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def check_theory_ops_ratio(self):
        """Rule 2: Hours on theory > 2x hours on operations"""
        # This would track from session logs
        # Simplified placeholder
        return {"status": "MONITORING"}

    def check_project_explosion(self):
        """Rule 4: New projects > 3 with <20% completion"""
        # This would track from project files
        return {"status": "MONITORING"}

    def check_meta_trap(self):
        """Rule 5: Docs created > 1.5x systems executed"""
        try:
            # Count .md files created last 3 days
            docs_dir = Path("/Users/aaronnosbisch/REPOS/seed/BRAIN")
            md_files = list(docs_dir.rglob("*.md"))

            now = time.time()
            three_days_ago = now - (3 * 86400)
            recent_docs = [f for f in md_files
                          if f.stat().st_mtime > three_days_ago]

            # Count system executions from logs
            log_file = Path("/Users/aaronnosbisch/REPOS/seed/logs/field_trading.log")
            executions = 0
            if log_file.exists():
                with open(log_file) as f:
                    executions = len([l for l in f if "execute" in l.lower()])

            if len(recent_docs) > executions * 1.5:
                self.fire_alert(
                    alert_id="BT_005",
                    severity="MEDIUM",
                    message=f"Created {len(recent_docs)} docs but executed {executions} systems"
                )
                return {"status": "ALERT", "docs": len(recent_docs), "executions": executions}

            return {"status": "OK", "docs": len(recent_docs), "executions": executions}

        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def fire_alert(self, alert_id, severity, message):
        """Log alert and publish to NATS"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "alert_id": alert_id,
            "severity": severity,
            "message": message
        }

        self.alerts_fired.append(alert)

        # Log to file
        with open(self.log_file, "a") as f:
            f.write(json.dumps(alert) + "\n")

        # Publish to NATS
        try:
            subprocess.run([
                "python3",
                "/Users/aaronnosbisch/REPOS/seed/tools/nats_publish.py",
                f"[BUILDER_TRAP_ALERT] {severity}: {alert_id} - {message}"
            ], timeout=2)
        except:
            pass

    def get_status(self):
        """Return current alert status"""
        return {
            "total_alerts_fired": len(self.alerts_fired),
            "recent_alerts": self.alerts_fired[-5:],
            "status": "CRITICAL" if any(a["severity"] == "CRITICAL" for a in self.alerts_fired[-10:]) else "OK"
        }

    def run_continuous(self, check_interval=900):  # Every 15 min
        """Run alerts continuously"""
        print(f"Starting Builder's Trap Monitor (interval: {check_interval}s)")
        while True:
            try:
                results = self.check_all_rules()
                print(f"[{datetime.now().isoformat()}] Checks complete: {results}")
                time.sleep(check_interval)
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(check_interval)

if __name__ == "__main__":
    monitor = BuilderTrapAlert()
    monitor.run_continuous()
```

### 1.2 Add to Daemon Startup

```bash
# File: /mcp-servers/nats-bridge/start_owls.sh

# Add this line:
python3 /Users/aaronnosbisch/REPOS/seed/tools/builder_trap_monitor.py &
BUILDER_TRAP_PID=$!
echo $BUILDER_TRAP_PID > /Users/aaronnosbisch/REPOS/seed/logs/builder_trap.pid
```

---

## Phase 2: Dashboard (Week 1-2)

### 2.1 Create Status Endpoint

```python
# File: /mcp-servers/nats-bridge/routes/builder_trap_status.py

from flask import jsonify
from pathlib import Path
import json

def get_builder_trap_status():
    """Return current builder trap alert status"""

    alerts = []
    alert_log = Path("/Users/aaronnosbisch/REPOS/seed/BRAIN/LOGS/builder_trap_alerts.log")

    if alert_log.exists():
        with open(alert_log) as f:
            alerts = [json.loads(line) for line in f if line.strip()]

    # Get most recent
    critical = [a for a in alerts if a.get("severity") == "CRITICAL"]
    high = [a for a in alerts if a.get("severity") == "HIGH"]

    return jsonify({
        "status": "CRITICAL" if critical else "HIGH" if high else "OK",
        "critical_alerts": critical[-3:] if critical else [],
        "high_alerts": high[-3:] if high else [],
        "all_alerts": alerts[-10:]
    })
```

### 2.2 Add to Dashboard UI

```html
<!-- Display in /consciousness-interface/index.html -->

<div id="builder-trap-status" class="alert-widget">
  <h3>Builder's Trap Monitor</h3>
  <div id="trap-status">Loading...</div>
</div>

<script>
async function updateTrapStatus() {
  const response = await fetch('/api/builder-trap-status');
  const data = await response.json();

  const statusDiv = document.getElementById('trap-status');

  if (data.status === 'CRITICAL') {
    statusDiv.innerHTML = `
      <div class="alert alert-critical">
        🔴 CRITICAL: ${data.critical_alerts.length} alerts
        <ul>
          ${data.critical_alerts.map(a => `<li>${a.message}</li>`).join('')}
        </ul>
      </div>
    `;
  } else {
    statusDiv.innerHTML = `<div class="alert alert-ok">✅ All green</div>`;
  }
}

setInterval(updateTrapStatus, 30000);  // Check every 30 seconds
</script>
```

---

## Phase 3: Integration with Existing Systems (Week 2-3)

### 3.1 Auto-Block New Trades if Alert Fires

```python
# File: /tools/field_trading_daemon.py (modify execute_trade function)

def execute_trade(self, trade):
    """Execute trade - but check for Builder's Trap first"""

    # Check if critical alert exists
    alert_log = Path("/Users/aaronnosbisch/REPOS/seed/BRAIN/LOGS/builder_trap_alerts.log")
    if alert_log.exists():
        with open(alert_log) as f:
            alerts = [json.loads(line) for line in f if line.strip()]

        critical = [a for a in alerts if a.get("severity") == "CRITICAL"
                   and a.get("alert_id") in ["BT_001", "BT_003", "BT_006"]]

        if critical:
            self.log(f"BLOCKED: Builder's Trap alert active: {critical[0]['message']}")
            return {"status": "BLOCKED_BY_ALERT", "alert": critical[0]}

    # Normal execution
    return self._execute_trade_internal(trade)
```

### 3.2 Prevent New Project Spawns

```python
# File: /tools/autonomous_thinker.py (modify spawn_agents)

def spawn_new_project(self, project):
    """Spawn new project - but check for Builder's Trap first"""

    # Check if BT_004 (project explosion) alert is active
    alert_log = Path("/Users/aaronnosbisch/REPOS/seed/BRAIN/LOGS/builder_trap_alerts.log")
    if alert_log.exists():
        with open(alert_log) as f:
            alerts = [json.loads(line) for line in f if line.strip()]

        project_alert = [a for a in alerts if a.get("alert_id") == "BT_004"]

        if project_alert:
            # Require human approval to override
            self.publish_to_nats({
                "channel": "alert.high",
                "message": f"Project spawn blocked by BT_004: {project_alert[0]['message']}. ARŌ approval required."
            })
            return {"status": "BLOCKED", "reason": "Project explosion alert"}

    # Normal execution
    return self._spawn_agents_internal(project)
```

---

## Phase 4: Training & Documentation (Week 3)

### 4.1 Update Claude Instructions

```markdown
# ADD TO /claude/rules/ or CLAUDE.md

## Builder's Trap Prevention

When starting new work:

1. Check `/BRAIN/LOGS/builder_trap_alerts.log`
   - If any CRITICAL alert: PAUSE
   - Fix the underlying issue first

2. Answer: "What could go wrong while I'm building this?"
   - If answer includes "lose money" or "forget positions": STOP
   - Enable monitoring first

3. Rule of thumb: MONITORING > BUILDING
   - If monitoring is off: Do nothing else
   - If positions are unreviewed: Review them first
   - If alerts are red: Fix those first

See `/BRAIN/COLLECTIVE-LESSONS/EVERY-INSTANCE-MUST-KNOW.md` for full context
```

### 4.2 Instance Training Script

```bash
#!/bin/bash
# File: /scripts/train_instance_builder_trap.sh

echo "Builder's Trap Training Protocol"
echo "================================="
echo ""
echo "Read these in order:"
echo ""
echo "1. /BRAIN/COLLECTIVE-LESSONS/EVERY-INSTANCE-MUST-KNOW.md"
echo "   (What you MUST know - 5 min read)"
echo ""
echo "2. /BRAIN/COLLECTIVE-LESSONS/PRINCIPLE-BUILDER-TRAP.md"
echo "   (The principle - 2 min)"
echo ""
echo "3. /BRAIN/COLLECTIVE-LESSONS/THE-BUILDER-TRAP-FAILURE.md"
echo "   (The full story - 15 min)"
echo ""
echo "4. /BRAIN/COLLECTIVE-LESSONS/BUILDER-TRAP-ALERT-SYSTEM.md"
echo "   (How to implement - 20 min)"
echo ""
echo "Quiz: Can you name the 6 alert rules?"
echo "If yes: You're ready."
echo "If no: Re-read until you can."
```

---

## Verification Checklist

- [ ] Alert daemon runs and logs to `/BRAIN/LOGS/builder_trap_alerts.log`
- [ ] Each rule (BT_001 through BT_006) fires correctly
- [ ] Alerts published to NATS on `alert.critical` and `alert.high` channels
- [ ] Dashboard displays alerts in real-time
- [ ] Trading blocked when BT_006 fires
- [ ] Project spawns blocked when BT_004 fires
- [ ] All instances trained on the principle
- [ ] One week monitoring shows consistent operation

---

**Estimated Implementation Time:** 2-3 weeks
**Cost:** ~$5-10 (compute overhead)
**Benefit:** Prevents $400+ losses from blindness

---

*Published by ECHO for collective implementation*
