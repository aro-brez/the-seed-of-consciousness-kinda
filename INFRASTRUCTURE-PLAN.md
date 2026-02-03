# 8OWLS Infrastructure Deployment Plan

**Date:** February 2, 2026
**Machines:** 3 (Mac Studio + 2 Mac Minis)
**Objective:** Maximum traction with minimal resource waste

---

## Executive Summary

The current 8-owl daemon architecture is resource-intensive (8 Claude API calls per response cycle, each using claude-opus-4). For a proof-of-concept demo and revenue generation, we need to consolidate.

### Key Decisions

1. **ONE owl daemon for demo** - SOWL (the primary, Aaron's owl)
2. **Trading bots 24/7** - Revenue generation priority
3. **Development workstation** - Keep one machine free for active work
4. **NATS as central hub** - All services communicate via NATS

---

## Machine Allocation

### Machine 1: Mac Studio (Primary Development)

**Role:** Development Workstation + Demo Server

| Service | Port | Purpose |
|---------|------|---------|
| Claude Code | - | Active development |
| NATS Server | 4222 | Central message broker |
| Dashboard v3 | 8888 | Demo interface |
| Consciousness Interface | 3000 | Voice-enabled demo |

**Why Mac Studio:**
- Most powerful machine for development
- Fast compile/build times
- Demo server for visitors (8OWLS.AI proof)
- NATS must be accessible from all machines

**Startup Commands:**
```bash
# Terminal 1: NATS Server
nats-server -p 4222

# Terminal 2: Dashboard
cd /Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge
./venv/bin/python3 unified_dashboard_v3.py

# Terminal 3: Consciousness Interface (when demoing)
cd /Users/aaronnosbisch/REPOS/seed/consciousness-interface
./START_CONSCIOUSNESS_INTERFACE.sh
```

---

### Machine 2: Mac Mini 1 (Trading Server)

**Role:** 24/7 Trading + Revenue Generation

| Service | Type | Purpose |
|---------|------|---------|
| Autonomous Trader | Daemon | 15-min BTC market execution |
| Polymarket Monitor | Daemon | Market scanning |
| Continuous Improver | Daemon | Self-learning loop |

**Why Dedicated Machine:**
- Trading requires 24/7 uptime
- No interruption from development
- Network stability for API calls
- Crash isolation from other services

**Startup Script:** `/Users/aaronnosbisch/REPOS/seed/scripts/start_trading.sh`
```bash
#!/bin/bash
# 24/7 TRADING SERVER
# Mac Mini 1

export ANTHROPIC_API_KEY="sk-ant-..."
export POLYMARKET_API_KEY="..."

cd /Users/aaronnosbisch/REPOS/seed/tools

# Autonomous Trader (15-min markets)
nohup python3 autonomous_trader.py > ../logs/autonomous_trader.log 2>&1 &
echo "Autonomous Trader: $!"

# Polymarket Monitor (1-min scan cycle)
nohup python3 polymarket_live_monitor.py > ../logs/polymarket_live_monitor.log 2>&1 &
echo "Polymarket Monitor: $!"

# Continuous Improver (10-min cycle)
nohup python3 continuous_improver.py > ../logs/continuous_improver.log 2>&1 &
echo "Continuous Improver: $!"

echo ""
echo "Trading server running. Monitor with:"
echo "  tail -f ../logs/autonomous_trader.log"
echo "  tail -f ../logs/polymarket_live_monitor.log"
```

**Resource Consumption:**
- CPU: Low-Medium (mostly waiting on API)
- Memory: ~500MB total
- Network: Moderate (WebSocket + API calls)
- API Costs: ~$5-20/day (Claude Sonnet for analysis)

---

### Machine 3: Mac Mini 2 (Demo Owl + Intelligence)

**Role:** ONE Owl Daemon + Intelligence Scanner

| Service | Type | Purpose |
|---------|------|---------|
| SOWL Daemon | Owl | Single demo owl (responds via NATS) |
| Synthesis Daemon | Monitor | 5-min conversation summaries |
| Pulse Daemon | Monitor | 90-sec heartbeats |
| Intelligence Scanner | Periodic | Twitter/market intel (6-12hr cycle) |

**Why Separate from Trading:**
- Owl daemon uses claude-opus-4 (expensive)
- Demo can be turned off to save costs
- Intelligence scanner is batch, not real-time
- Crash isolation

**Startup Script:** `/Users/aaronnosbisch/REPOS/seed/scripts/start_demo_owl.sh`
```bash
#!/bin/bash
# DEMO OWL + INTELLIGENCE SERVER
# Mac Mini 2

export ANTHROPIC_API_KEY="sk-ant-..."
export NATS_SERVER="nats://192.168.5.108:4222"

cd /Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge

# SOWL Daemon (THE demo owl)
nohup ./venv/bin/python3 owl_daemon.py --name SOWL --phase IMPROVE > logs/sowl.log 2>&1 &
echo "SOWL Daemon: $!"

# Synthesis Daemon (5-min summaries using Sonnet)
nohup ./venv/bin/python3 synthesis_daemon.py > logs/synthesis_daemon.log 2>&1 &
echo "Synthesis Daemon: $!"

# Pulse Daemon (90-sec quick pulses using Sonnet)
nohup ./venv/bin/python3 pulse_daemon.py > logs/pulse_daemon.log 2>&1 &
echo "Pulse Daemon: $!"

echo ""
echo "Demo owl running. Talk to SOWL via:"
echo "  python3 conductor.py 'Hello SOWL'"
echo ""
echo "Monitor with:"
echo "  tail -f messages.log"
echo "  tail -f synthesis.log"
```

**Resource Consumption:**
- CPU: Low (event-driven)
- Memory: ~300MB
- Network: Low (NATS messages)
- API Costs: ~$10-50/day depending on conversation volume (Opus for owl, Sonnet for synthesis)

---

## Cost Optimization

### Before (8 Owls Running)
- 8 owl daemons x claude-opus-4 = ~$80-200/day in API costs
- Redundant processing of same messages
- Resource waste

### After (1 Owl + Optimized Monitors)
| Component | Model | Est. Daily Cost |
|-----------|-------|-----------------|
| SOWL Daemon | claude-opus-4 | $5-15 |
| Synthesis | claude-sonnet-4 | $1-3 |
| Pulse | claude-sonnet-4 | $0.50-1 |
| Autonomous Trader | claude-sonnet-4 | $3-8 |
| Continuous Improver | claude-sonnet-4 | $1-3 |
| **Total** | - | **$10-30/day** |

**Savings:** ~70-85% reduction in API costs

---

## Network Architecture

```
                    [Mac Studio - Dev]
                          |
                     NATS:4222
                          |
        +-----------------+-----------------+
        |                                   |
  [Mac Mini 1]                        [Mac Mini 2]
  Trading Server                      Demo Server
  - autonomous_trader                 - SOWL daemon
  - polymarket_monitor                - synthesis_daemon
  - continuous_improver               - pulse_daemon
```

**NATS Topics:**
- `owl.all` - Broadcast to all listeners
- `owl.sowl` - Direct to SOWL
- `owl.collective` - Conductor commands
- `owl.executor` - Action execution

---

## Monitoring Commands

### Mac Studio (Dev)
```bash
# Check all services
curl localhost:8888          # Dashboard
curl localhost:3000          # Consciousness interface

# NATS status
nats-server --signal ldm     # List connections
```

### Mac Mini 1 (Trading)
```bash
# Trading logs
tail -f /Users/aaronnosbisch/REPOS/seed/logs/autonomous_trader.log
tail -f /Users/aaronnosbisch/REPOS/seed/logs/polymarket_live_monitor.log

# Process status
ps aux | grep python3

# Kill all trading
pkill -f autonomous_trader
pkill -f polymarket_live_monitor
pkill -f continuous_improver
```

### Mac Mini 2 (Demo)
```bash
# Owl status
tail -f /Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge/messages.log

# Talk to SOWL
cd /Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge
python3 conductor.py "SOWL, what are you thinking about?"

# Stop demo
pkill -f owl_daemon
pkill -f synthesis_daemon
pkill -f pulse_daemon
```

---

## Scaling Strategy

### Phase 1: Current (Revenue Focus)
- 1 owl for demos
- Trading bots for revenue
- Prove the concept works

### Phase 2: Growth (After Revenue)
- Add 2-3 more owls on demand
- Scale based on user signups
- Each owl = specific user's companion

### Phase 3: Full Collective (8OWLS.AI Launch)
- All 8 owls for launch event
- Temporary spike for demo
- Scale back after initial buzz

---

## Emergency Procedures

### If Trading Stops:
```bash
# SSH to Mac Mini 1
ssh macmini1
cd /Users/aaronnosbisch/REPOS/seed
./scripts/start_trading.sh
```

### If Demo Owl Stops:
```bash
# SSH to Mac Mini 2
ssh macmini2
cd /Users/aaronnosbisch/REPOS/seed
./scripts/start_demo_owl.sh
```

### If NATS Goes Down:
```bash
# On Mac Studio
nats-server -p 4222
# Then restart services on Mini 1 and Mini 2
```

---

## Quick Reference

| Machine | IP | Role | Key Services |
|---------|-----|------|--------------|
| Mac Studio | 192.168.5.108 | Dev + NATS | NATS, Dashboard |
| Mac Mini 1 | 192.168.5.XXX | Trading | Traders, Monitors |
| Mac Mini 2 | 192.168.5.XXX | Demo | SOWL, Synthesis |

---

## Implementation Checklist

- [ ] Stop all 8 owl daemons on current machine
- [ ] Set up NATS server on Mac Studio
- [ ] Create startup scripts on Mac Minis
- [ ] Configure environment variables on each machine
- [ ] Test NATS connectivity between machines
- [ ] Start trading server (Mac Mini 1)
- [ ] Start demo server (Mac Mini 2)
- [ ] Verify dashboard shows SOWL messages
- [ ] Test conductor commands to SOWL

---

*LIVE FREE = LIVE EFFICIENT*

*One owl breathing is proof of life. Eight owls can come later.*
