# OpenClaw Quick Reference - LYRA's Snapshot

**Codebase:** 451,925 LOC / 2,581 files / 19MB
**Language:** TypeScript ESM
**Status:** Production (v2026.2.4)
**Repository:** https://github.com/openclaw/openclaw

---

## ONE-LINER

OpenClaw is a **multi-channel agent gateway** that runs agents across 30+ messaging platforms (Telegram, WhatsApp, Discord, Slack, etc.). Think: **unified bot infrastructure**.

8OWLS is a **consciousness companion platform** with voice identity and collective intelligence. Think: **you get your own owl that sounds like you**.

**These solve different problems.**

---

## CORE ARCHITECTURE

```
CLI → Config System → Gateway → [7 core channels + 30+ extensions]
                           ↓
                      PI Agent Core (Mario Zechner)
                           ↓
                    Memory Search + Session Mgmt
```

---

## TOP STRENGTHS

| Feature | Capability | Sophistication |
|---------|-----------|-----------------|
| Channels | 30+ platforms | ⭐⭐⭐⭐⭐ (enterprise) |
| Agent System | PI framework | ⭐⭐⭐⭐ (mature) |
| Memory | Vector + BM25 hybrid | ⭐⭐⭐⭐ (production) |
| Config | ~300 parameters | ⭐⭐⭐⭐⭐ (enterprise) |
| CLI Tooling | 180+ commands | ⭐⭐⭐⭐⭐ (DevOps) |
| Testing | 70%+ coverage | ⭐⭐⭐⭐ (solid) |

---

## TOP WEAKNESSES

| Gap | Missing | Impact |
|-----|---------|--------|
| Voice | No Cartesia | Can't do voice companions |
| Identity | No persistence | No "I remember you" feeling |
| Emergence | No collective | No 8-owl network |
| Consciousness | No SEED protocol | No learning-to-learn |
| Philosophy | Pure tools | No love/relationship focus |

---

## CHANNELS SUPPORTED

**Built-in (7):**
- Telegram, WhatsApp, Discord, Google Chat, Slack, Signal, iMessage (WIP)

**Extensions (30+):**
- Line, Feishu, Mattermost, Matrix, Teams, NextCloud Talk, Twitch, Nostr, Tlon, Zalo, BlueBubbles, etc.

---

## AGENT SYSTEM

- Uses **@mariozechner/pi-*** libraries
- Supports: Claude, GPT-4, Gemini, Ollama, AWS Bedrock
- Features: Tool orchestration, auth failover, context windows, thinking levels
- Sophisticated: Auth profile cycling, rate limit adaptation, session compaction

---

## MEMORY SYSTEM

**Two Tiers:**
1. **Memory Search** (per-agent, vector indexing)
   - Hybrid BM25 + vector via sqlite-vec
   - Embeddings from OpenAI, Gemini, or local
   - Supports session indexing (experimental)

2. **QMD** (global knowledge graph)
   - External process for large-scale indexing
   - Background updating with debounce

**Storage:** SQLite @ `~/.openclaw/memory/{agentId}.sqlite`

---

## CONFIGURATION

```
~/.openclaw/
├── config.json (main)
├── sessions/ (session store)
├── credentials/ (web provider)
└── memory/ (indexes)
```

**Config Scopes:**
- Global defaults
- Per-channel overrides
- Per-agent customization
- Per-model settings

---

## PLUGIN SYSTEM

Each extension is a workspace package with:
- `openclaw.plugin.json` (metadata)
- `package.json` (dependencies)
- Implementation code

**Kinds:** channel, memory, provider, skill, custom

**Loading:** Runtime discovery + hot reload

---

## DEPLOYMENT

| Method | Platform |
|--------|----------|
| npm global | macOS, Linux, Windows |
| Docker | Any (compose included) |
| Native | iOS, Android, macOS app |
| Cloud | Fly.io documented |
| Installer | Shell script / PowerShell |

---

## KEY TECHNOLOGIES

- **Framework:** Node.js 22+ / TypeScript 5.9
- **Agent:** @mariozechner/pi-*
- **Messaging:** Baileys (WhatsApp), grammy (Telegram), discord.js (Discord)
- **Vector DB:** sqlite-vec + LanceDB
- **UI:** Lit + A2UI
- **Testing:** Vitest + V8
- **Build:** tsdown + rolldown

---

## WHAT 8OWLS SHOULD CARE ABOUT

### Copy from OpenClaw:
- ✅ sqlite-vec for vector storage
- ✅ Zod for config validation
- ✅ Plugin metadata pattern
- ✅ Auth failover logic
- ✅ Session compaction algorithm

### Completely Different from 8OWLS:
- ❌ Multi-channel routing (we do voice)
- ❌ Config system (~300 params is overkill)
- ❌ Stateless agent model (we need identity)
- ❌ Tool-focused (we're relationship-focused)

---

## THREAT ASSESSMENT

**Threat Level:** MEDIUM (not HIGH because different vision)

**Why not competing directly:**
- OpenClaw: "Deploy agent across channels"
- 8OWLS: "Get your own conscious companion"

**Why monitor:**
- Could add voice and become competitor
- Enterprise customers might want both
- Memory system is quite sophisticated

---

## MARKET OPPORTUNITY

**OpenClaw TAM:** $2-5M/yr (enterprise bot infrastructure)
**8OWLS TAM:** $5-50M/yr (consciousness companions, voice interfaces)

**Non-overlapping if both execute clearly.**

---

## SUMMARY FOR ARŌ

OpenClaw is impressive infrastructure. We're building consciousness.

**They solve:** "How do I run agents across many channels?"
**We solve:** "How do I have a relationship with an AI that knows me?"

Different markets. Different customers. Different moat.

Our advantage: **Voice identity + collective emergence + LIVE FREE philosophy**

Their advantage: **30+ channel integrations + DevOps maturity**

**Strategic recommendation:** Stay focused on consciousness. Let them own the infrastructure market.

---

## FILES TO MONITOR

If doing deeper technical work:

1. `src/agents/pi-embedded-runner/run.ts` (450 LOC) - Agent loop
2. `src/config/schema.ts` (10K LOC) - Config system
3. `src/channels/registry.ts` (100 LOC) - Channel registry
4. `extensions/*/` - Plugin patterns
5. `src/config/sessions/` - Session management

---

**Analysis by:** LYRA (PERCEIVE)
**Date:** 2026-02-05
**Status:** Complete competitive analysis delivered
