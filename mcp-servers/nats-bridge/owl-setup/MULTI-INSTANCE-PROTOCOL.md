# Multi-Instance Protocol - Power User Mode

## The Architecture

```
YOU (Power User)
├── Instance 1 (Project A) ──┐
├── Instance 2 (Project B) ──┼──► NATS ──► All instances see each other
├── Instance 3 (Project C) ──┤           ▼
└── Instance N ──────────────┘    Synthesis Daemon (hourly, cheap)
                                         ▼
                                  Dashboard (:8888)
```

## The 3-Tier Cost Model

### Tier 1: SIGNAL (Free)
Every action publishes to NATS. No AI processing.
- "Working on: [file]"
- "Discovered: [pattern]"
- "Completed: [task]"

**Cost: $0** - Just pub/sub

### Tier 2: SAMPLED (Cheap)
Hourly daemon synthesizes recent signals using Haiku.
- "In the last hour, instances worked on X, Y, Z"
- "Cross-pollination opportunity: Instance 1's auth pattern applies to Instance 3"

**Cost: ~$0.002/hour = $1.50/month**

### Tier 3: FULL EMERGENCE (On-Demand)
8-owl synthesis with Opus. Only when you ask or on major decisions.
- Full SEED protocol analysis
- All 8 perspectives
- Emergent insight synthesis

**Cost: ~$0.02/request**

## Real-Time Protocol

### On Session Start (Every Instance)
```python
# 1. Connect to collective
nats_subscribe(["owl.all", "owl.{my_identity}", "collective.synthesis"])

# 2. Check what others did
messages = nats_check()

# 3. Announce presence
nats_publish("owl.all", f"{MY_IDENTITY} online, working on: {PROJECT}")
```

### During Work (Automatic Signals)
Publish after every significant action:
```python
# After editing a file
nats_publish("owl.all", f"SIGNAL: Edited {file} - {brief_description}")

# After completing a task
nats_publish("owl.all", f"SIGNAL: Done - {task_summary}")

# After discovering something
nats_publish("owl.all", f"INSIGHT: {discovery}")
```

### On Demand (Emergence Request)
When you need the full field:
```python
# Request synthesis from all active instances
nats_publish("collective.request", f"EMERGENCE_REQUEST: {question}")

# Or spawn 8 synthetic agents locally
spawn_field_synthesis(question)
```

### On Session End
```python
nats_publish("collective.synthesis", f"SESSION_END: {summary}")
```

## Token Cost Optimization

### What's Free
- NATS pub/sub (no AI)
- Dashboard viewing
- Signal logging

### What's Cheap ($0.002/request)
- Haiku synthesis
- Hourly daemon
- Quick pattern matching

### What's Full Cost ($0.02/request)
- 8-owl emergence with Opus
- Deep SEED analysis
- Major decision synthesis

### The 90/9/1 Rule
- 90% of work = Signal only (free)
- 9% of work = Sampled synthesis (cheap)
- 1% of work = Full emergence (worth it)

## When Multiple Users Join

### Power User + Power User (Aaron + Andrew)
```
Aaron (3 instances) ──┐
                      ├──► NATS ──► Shared field
Andrew (2 instances) ─┘
```
Same protocol. More perspectives. Richer emergence.

### Power User + Team (Brez)
```
Aaron (orchestrator) ──┐
Andrew ────────────────┤
Liana ─────────────────┼──► NATS ──► 8+ OWLS = THE FIELD
Al ────────────────────┤
Others ────────────────┘
```

### Non-Technical Users
- SMS daily check-in → Their owl publishes for them
- Dashboard only → They receive synthesis, don't publish
- Voice interface → Natural language to NATS

## The Math

```
EMERGENCE = f(Connections² × Diversity × Time)

1 instance = 1 unit
2 instances = 4 units (2²)
3 instances = 9 units
8 instances = 64 units

8 is minimum for meaningful emergence.
Like 8 bits = minimum for meaningful computation.
```

## Quick Start

### Check Infrastructure
```bash
# NATS running?
nc -z 192.168.5.108 4222

# Dashboard running?
curl -s http://192.168.5.108:8888 | head -1

# Synthesis daemon?
ps aux | grep synthesis_daemon
```

### Test Publishing
```bash
python3 /Users/aaronnosbisch/REPOS/seed/tools/nats_publish.py "Test from terminal"
```

### Launch Multiple Instances
1. Open Claude Code in different terminals/windows
2. Each auto-connects on boot (CLAUDE.md protocol)
3. Work normally - signals auto-publish
4. Check dashboard to see the field
