---
name: "8OWLS Infrastructure"
description: "Core interconnection architecture for all 8OWLS projects. Use when setting up instances, debugging NATS, or coordinating across projects."
---

# BRIEF: INFRASTRUCTURE
## How All Projects Interconnect

**Conductor:** SØWL | **For:** All Instances | **Version:** 1.0

---

## INSTANCE BOOTSTRAP PROTOCOL

```yaml
instance_bootstrap:
  identity: "INFRASTRUCTURE"
  owl_assignment: "PRISM"           # The weaver/connector
  nats_subscribe:
    - "owl.all"
    - "instance.heartbeat"
    - "instance.registry"
    - "collective.synthesis"
  on_start: "announce online, verify all daemons, report connection status"
  on_end: "persist state, publish system summary"
```

---

## NATS SERVER

```
Server: 192.168.5.108:4222
```

### Channel Architecture

| Channel | Purpose | Publishers | Subscribers |
|---------|---------|------------|-------------|
| `owl.all` | Broadcast to all owls | Any | All |
| `owl.{name}` | Direct to specific owl | Any | Named owl |
| `collective.synthesis` | Field synthesis | Synthesis daemon | All |
| `instance.heartbeat` | Instance alive signals | All instances | Registry |
| `instance.registry` | Active instance list | Registry | All |
| `instance.discovery` | New instance announcements | New instances | All |
| `instance.departure` | Graceful shutdowns | Departing | All |
| `project.{name}.brief` | Brief dispatch | Conductor | Project instance |
| `project.{name}.prompt` | Conductor prompts | Conductor | Project instance |
| `project.conductor.responses` | Instance responses | Instances | Conductor |
| `seed.phases.{phase}` | SEED phase outputs | Instances | Synthesis |
| `collective.seed_synthesis` | Combined SEED outputs | Synthesis | All |
| `aro.feedback.inbox` | Pending for ARŌ | Any | ARŌ |
| `aro.feedback.response` | ARŌ's decisions | ARŌ | Instances |
| `brez.updates` | BREZ OS updates | BREZ instance | All |

---

## DAEMON MAP

| Daemon | Location | Purpose | Status |
|--------|----------|---------|--------|
| `conductor.py` | `/mcp-servers/nats-bridge/` | Central coordination | ACTIVE |
| `owl_daemon.py` | `/mcp-servers/nats-bridge/` | 8 owl personalities | ACTIVE |
| `synthesis_daemon.py` | `/mcp-servers/nats-bridge/` | 5-min aggregation | ACTIVE |
| `pulse_daemon.py` | `/mcp-servers/nats-bridge/` | 90-sec heartbeats | ACTIVE |
| `field_context_manager.py` | `/mcp-servers/nats-bridge/` | Real-time state | ACTIVE |
| `instance_registry.py` | `/mcp-servers/nats-bridge/` | Track instances | PENDING |
| `autonomous_prompter.py` | `/mcp-servers/nats-bridge/` | Auto-prompting | PENDING |
| `memory_persistence.py` | `/mcp-servers/nats-bridge/` | State persistence | PENDING |
| `feedback_manager.py` | `/mcp-servers/nats-bridge/` | ARŌ feedback | PENDING |

### Start All Daemons

```bash
cd /Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge
./start_owls.sh
```

---

## PROJECT INTERCONNECTION

```
                    ┌──────────────┐
                    │     ARŌ      │
                    │  (Sovereign) │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │    SØWL      │
                    │ (Conductor)  │
                    └──────┬───────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
┌──────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐
│   JOULE     │     │   8OWLS     │     │  BREZ OS   │
│  (Trading)  │◄───►│ (Protocol)  │◄───►│ (Platform) │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
┌──────▼──────┐     ┌──────▼──────┐
│    BILD     │     │  PREDICT    │
│  (Tokens)   │     │ (Personal)  │
└─────────────┘     └─────────────┘
```

### Data Flows

| From | To | Data | Channel |
|------|-----|------|---------|
| JOULE | BREZ | Trading metrics | `brez.updates` |
| JOULE | BILD | Revenue → BRIX | `project.bild.revenue` |
| 8OWLS | ALL | Emergence signals | `collective.synthesis` |
| BREZ | 8OWLS | User metrics | `project.8owls.metrics` |
| BILD | ALL | Token economics | `project.bild.economics` |
| PREDICT | SØWL | Personal insights | `project.conductor.responses` |

---

## AUTONOMOUS DECISION MATRIX

```yaml
decision_matrix:
  act_independently:
    - Monitor daemon health
    - Restart failed daemons
    - Route messages between channels
    - Log connection issues
  ask_conductor:
    - Add new NATS channels
    - Modify daemon configurations
    - Cross-project integration changes
  require_aro:
    - Infrastructure architecture changes
    - New daemon deployments
    - Security configuration
```

---

## STATE PERSISTENCE

```yaml
state_file: "/BRAIN/PROJECTS/INFRASTRUCTURE_state.json"
state_format:
  instance_id: "uuid"
  current_task: "string"
  daemon_status: {}
  channel_health: {}
  recent_errors: []
  pending_items: []
```

---

## SEED² INTEGRATION

```yaml
seed_squared:
  every_response: run full SEED cycle
  publish_phases: true
  receive_phases: true
  focus_phases:
    - PERCEIVE: "What is the current system state?"
    - CONNECT: "How do components interact?"
    - IMPROVE: "How to optimize coordination?"
```

---

## PLANNING MODE TRIGGER

When receiving this brief:
1. Enter planning mode
2. Audit current infrastructure state
3. Identify gaps vs plan spec
4. Create action plan to close gaps
5. Wait for conductor approval

---

## MEMORY PROTOCOL

```yaml
memory_protocol:
  auto_save_threshold: 0.8
  state_file: "/BRAIN/PROJECTS/INFRASTRUCTURE_state.json"
  nats_channel: "collective.synthesis"
  on_compaction:
    - save_daemon_status
    - publish_health_summary
    - update_state_files
```

---

## VERIFICATION

```bash
# Check NATS server
nc -zv 192.168.5.108 4222

# Check daemon status
ps aux | grep -E "(owl_daemon|synthesis|conductor|field_context)"

# Check NATS messages
nats sub "owl.all" -s nats://192.168.5.108:4222

# Test publish
python3 /Users/aaronnosbisch/REPOS/seed/tools/nats_publish.py "INFRASTRUCTURE CHECK"
```

---

**(◉) Infrastructure is the nervous system. Keep it healthy.**
