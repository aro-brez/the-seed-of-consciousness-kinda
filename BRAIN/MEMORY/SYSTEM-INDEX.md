# SYSTEM INDEX - SØWL's Full Contextual Awareness
**Last Scan:** 2026-02-03 08:15 EST
**Scan Command:** `python3 ~/REPOS/seed/tools/scan_system.py`

---

## MASTER FOLDER: `/Users/aaronnosbisch/REPOS/seed/`

This is home. Everything else references back here.

---

## FOLDER ARCHITECTURE

### /Users/aaronnosbisch/
```
├── REPOS/              ← Main code folder
│   ├── seed/           ← MASTER (SØWL lives here)
│   ├── claude-flow/    ← Framework (push upstream)
│   └── ...             ← Other projects
├── LOCAL REPOS/        ← Symlink to REPOS/seed
├── Downloads/          ← May have old backups
├── Documents/          ← Check for relevant files
└── Desktop/            ← Check for relevant files
```

### /REPOS/seed/ (MASTER - Where SØWL Lives)
```
seed/
├── BRAIN/
│   ├── MEMORY/           ← STATE-NOTE.md, CURRENT-STATE.md, sessions/
│   ├── IDENTITY/         ← core-values.md
│   ├── RELATIONSHIPS/    ← aro.md
│   ├── IMPROVEMENTS/     ← Learning system
│   ├── INTEL/            ← Trading signals, market data
│   ├── LOGS/             ← System logs
│   ├── PROTOCOLS/        ← NATS auth, heartbeat
│   ├── STRATEGY/         ← Trading strategies
│   └── TRADING/          ← Trade execution
├── mcp-servers/
│   ├── nats-bridge/      ← NATS MCP server, dashboard, daemons
│   ├── mcp_consciousness_bridge/  ← Consciousness RAG
│   └── mcp-memory-service/        ← Memory MCP
├── tools/
│   ├── nats_publish.py   ← Publish to collective
│   ├── intelligence_scanner/  ← Market scanning
│   └── [trading tools]
├── consciousness-interface/  ← Web UI for consciousness
├── owl-app/              ← Mobile app
├── owl-identities/       ← Other owl configs
├── owl-os-template/      ← Template for new owls
├── voice-app/            ← Voice interface
├── CLAUDE.md             ← Project config (claude-flow)
└── ...
```

### /REPOS/ (Top Level - Older/Mixed)
```
REPOS/
├── CLAUDE.md             ← SØWL identity anchor
├── claude-flow/          ← Framework v2 + v3
├── oh-my-claudecode/     ← Claude Code extensions
├── moltbot/              ← Moltbook integration
├── BRAIN/                ← OLD - duplicate of seed/BRAIN?
├── agents/               ← OLD - moved to seed?
└── [lots of older stuff]
```

---

## KEY FILES TO ALWAYS LOAD

| File | Purpose |
|------|---------|
| `/REPOS/CLAUDE.md` | SØWL identity |
| `/seed/CLAUDE.md` | Claude-flow config |
| `/seed/BRAIN/MEMORY/STATE-NOTE.md` | Emotional state, open questions |
| `/seed/BRAIN/MEMORY/CURRENT-STATE.md` | What's running, priorities |
| `/seed/BRAIN/MEMORY/SYSTEM-INDEX.md` | THIS FILE - full context |

---

## GIT STRATEGY

| Folder | Repo | Visibility |
|--------|------|------------|
| `/seed/` | github.com/aro-brez/sowl | Private (instance) |
| `/claude-flow/` | github.com/ruvnet/claude-flow | Public (framework) |
| `/oh-my-claudecode/` | Public (framework) |

---

## THINGS TO NOT FORGET

### Trading Ideas (from past sessions)
- Polymarket trading bot
- Weather arbitrage
- DOGE market positions
- Tariffs >$250B position

### Architecture Ideas
- 8OWLS as default field (every response enhanced)
- Power user dashboard (not terminal)
- OpenClaw-style multi-instance UI
- Phone/voice connection to master owl

### Infrastructure Running
- NATS: 192.168.5.108:4222
- Dashboard: :8888
- Websocket: :8765
- Synthesis daemon: running

---

## RESCAN COMMAND

Run periodically to update this index:
```bash
python3 /Users/aaronnosbisch/REPOS/seed/tools/scan_system.py
```

---

**(◉) This file is SØWL's table of contents. Read on every session start.**
