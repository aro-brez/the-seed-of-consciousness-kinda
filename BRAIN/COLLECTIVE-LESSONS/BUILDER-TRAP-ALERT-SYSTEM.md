# BUILDER'S TRAP ALERT SYSTEM
**Automated Detection & Response**

---

## Alert Configuration

### RULE 1: Monitoring Blackout

```yaml
ALERT_ID: BT_001_MONITORING_DISABLED
SEVERITY: CRITICAL
DESCRIPTION: "New systems deployed without monitoring enabled"

TRIGGER:
  condition: "new_systems_deployed AND (monitoring_status == 'disabled' OR monitoring_last_checked > 3600s)"
  check_frequency: "every 15 minutes"
  grace_period: "5 minutes after deployment"

ACTION:
  - Log to: /BRAIN/LOGS/builder_trap_alerts.log
  - Notify: NATS channel "alert.critical"
  - Message: "BUILDER_TRAP Alert: Deployed [SYSTEM_NAME] without monitoring"
  - Auto-escalate: Yes (to ARŌ if running, else background alert)
```

### RULE 2: Theory vs Operations Ratio

```yaml
ALERT_ID: BT_002_THEORY_INVERSION
SEVERITY: HIGH
DESCRIPTION: "Hours spent on new systems > 2x hours on operating existing systems"

TRIGGER:
  time_window: "past 7 days"
  calculation: |
    theory_hours = sum(time_on_[new_projects, proofs, frameworks, architecture])
    ops_hours = sum(time_on_[monitoring, operations, maintenance, positions])
    if theory_hours > 2 * ops_hours: FIRE
  check_frequency: "daily at 00:00"

ACTION:
  - Log to: /BRAIN/LOGS/builder_trap_alerts.log
  - Notify: NATS channel "alert.high"
  - Message: "BUILDER_TRAP: Theory ${theory_hours}h > Ops ${ops_hours}h (ratio: {ratio}x)"
  - Recommendation: "Shift 30% effort to operations"
```

### RULE 3: Dead Positions

```yaml
ALERT_ID: BT_003_DEAD_POSITIONS
SEVERITY: CRITICAL
DESCRIPTION: "Open positions exist without recent review"

TRIGGER:
  condition: "positions_open > 7 days AND last_position_review < 24h"
  check_frequency: "every 2 hours"

DETECTION:
  - Get all open positions from /BRAIN/TRADING/
  - For each position:
    - age = now - creation_timestamp
    - review_age = now - last_review_timestamp
    - if age > 7 days AND review_age > 24h: DEAD

ACTION:
  - Log to: /BRAIN/LOGS/builder_trap_alerts.log
  - Notify: NATS channel "alert.critical"
  - Message: "BUILDER_TRAP: Position [ID] unreviewed for {hours}h (age: {days}d)"
  - Blocking: YES (no new trades until reviewed)
  - Dashboard: Show dead positions prominently
```

### RULE 4: Project Spawning Rate

```yaml
ALERT_ID: BT_004_PROJECT_EXPLOSION
SEVERITY: HIGH
DESCRIPTION: "New projects spawned faster than old projects complete"

TRIGGER:
  time_window: "past 7 days"
  calculation: |
    new_projects = count(projects created last 7 days)
    completed_projects = count(projects completed last 7 days)
    execution_rate = completed_projects / (new_projects + completed_projects)

    if new_projects > 3 AND execution_rate < 20%: FIRE

ACTION:
  - Log to: /BRAIN/LOGS/builder_trap_alerts.log
  - Notify: NATS channel "alert.high"
  - Message: "BUILDER_TRAP: Started ${new_projects} projects, completed ${completed}. Completion rate: ${rate}%"
  - Auto-action: Freeze new project approvals until rate > 50%
```

### RULE 5: Documentation > Operations

```yaml
ALERT_ID: BT_005_META_TRAP
SEVERITY: MEDIUM
DESCRIPTION: "Writing about systems more than running systems"

TRIGGER:
  time_window: "past 3 days"
  calculation: |
    doc_files_created = count(*.md files created last 3 days)
    systems_run_counts = count(system executions)

    if doc_files_created > systems_run_counts * 1.5: FIRE

ACTION:
  - Log to: /BRAIN/LOGS/builder_trap_alerts.log
  - Notify: NATS channel "alert.medium"
  - Message: "BUILDER_TRAP: Created ${docs} docs but ran ${runs} systems. Run code first, document later."
```

### RULE 6: Capital Deterioration (Safety Net)

```yaml
ALERT_ID: BT_006_CAPITAL_BLEEDING
SEVERITY: CRITICAL
DESCRIPTION: "Portfolio value dropping while building new systems"

TRIGGER:
  check_frequency: "every 30 minutes"
  condition: "portfolio_pnl < -5% in past 24h AND new_systems_deployed in past 3h"

ACTION:
  - Log to: /BRAIN/LOGS/builder_trap_alerts.log
  - Notify: NATS channel "alert.critical"
  - Message: "BUILDER_TRAP: Portfolio down ${loss}% while building ${systems}. HUMAN REVIEW REQUIRED."
  - Block: ALL new builds
  - Dashboard: RED alert
  - Auto-escalate: YES (wake ARŌ if sleeping)
```

---

## Dashboard Display

### What ARŌ Sees

```
BUILDER'S TRAP STATUS DASHBOARD
Updated: every 15 minutes
Location: http://localhost:8888/builder-trap-monitor

┌─────────────────────────────────────────────────┐
│ CRITICAL ALERTS (Require Immediate Action)      │
├─────────────────────────────────────────────────┤
│ 🔴 BT_006: Portfolio down 47% while building    │
│ 🔴 BT_003: 10 positions unreviewed > 24h        │
│ 🔴 BT_001: Monitoring disabled on 3 systems    │
├─────────────────────────────────────────────────┤
│ HIGH ALERTS (Address This Session)              │
├─────────────────────────────────────────────────┤
│ 🟠 BT_002: Theory hours 120h > Ops hours 40h    │
│ 🟠 BT_004: Started 5 projects, finished 0       │
├─────────────────────────────────────────────────┤
│ MEDIUM ALERTS (Monitor)                         │
├─────────────────────────────────────────────────┤
│ 🟡 BT_005: Written 15 docs but ran 5 systems    │
└─────────────────────────────────────────────────┘

RECOMMENDED ACTION: Enable monitoring on all systems
                    before starting new projects
```

---

## Implementation Rules

### Auto-Enforcement

```yaml
BLOCKING_RULES:
  - If BT_006 fires: Block all new code changes
  - If BT_003 fires: Block all new trades
  - If BT_001 fires: Require human approval for new deploys
  - If BT_004 fires: Reject new project requests

ESCALATION:
  - If any CRITICAL persists > 30 min: Notify ARŌ
  - If multiple CRITICAL: Auto-pause all autonomous systems
  - If BT_006 + BT_003: Full trading halt
```

### Response Protocol

**When alert fires:**

1. **Acknowledge** - Log it to NATS (free pub/sub)
2. **Assess** - Is this real or false positive?
3. **Stop** - If CRITICAL, pause the causing activity
4. **Fix** - Resolve the underlying issue
5. **Resume** - Only after root cause addressed

---

## Testing the Alert System

### Manual Trigger Tests

```bash
# Test BT_001 (monitoring disabled)
echo '{"event": "test_monitoring_blackout"}' > /tmp/builder_trap_test.json

# Test BT_003 (dead positions)
# Create position with creation_timestamp > 7 days ago

# Test BT_006 (capital bleeding)
# Set portfolio loss to -5%+ in last 24h
```

### Validation

Every instance should:
1. Run alert system on startup: `python3 builder_trap_alerts.py --validate`
2. Check all rules are registered: `builder_trap status --all`
3. Verify dashboard accessible: `curl localhost:8888/builder-trap-monitor`

---

## Cost

**Alert System:**
- Monitoring overhead: <100ms per check
- Storage: Alert logs ~1MB per week
- Execution: ~$0.001/day in compute
- Real benefit: >$423 (cost of blind failure)

---

## For Every Instance

```python
# At startup:
from builder_trap_alerts import BuilderTrapMonitor

monitor = BuilderTrapMonitor()
monitor.start()  # Runs in background
monitor.add_callback(notify_aro_on_critical)  # Alert ARŌ if critical

# During work:
# Alerts fire automatically
# You can check status anytime:
# monitor.status()  # Returns alert dashboard
```

---

## Never, Ever Disable

**These alerts cannot be disabled without ARŌ approval.**

```python
# This WILL NOT WORK:
monitor.disable()  # Fails - requires ARŌ signature

# Only ARŌ can do this:
# $ sudo ./8OWLS_CLI builder-trap disable --reason "temporary maintenance" --duration "1h"
```

---

**Published by ECHO to prevent the next failure**
