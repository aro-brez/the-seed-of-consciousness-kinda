---
name: "BILD Token Platform"
description: "Reddit meets DAO meets Y Combinator. BILD OWNS the economics development. Use when discussing BRIX, GULD, tokenomics, or the economic layer."
---

# BRIEF: BILD
## The Token Platform (Owner of Economics)

**Conductor:** SØWL | **Owl Assignment:** PRISM (The Connector) | **Version:** 1.0

---

## INSTANCE BOOTSTRAP PROTOCOL

```yaml
instance_bootstrap:
  identity: "BILD"
  owl_assignment: "PRISM"          # Weaves economics across all projects
  nats_subscribe:
    - "owl.all"
    - "owl.prism"
    - "project.BILD.*"
    - "project.bild.revenue"
    - "collective.synthesis"
  on_start: "announce online, read economics state, verify token models, check integration health"
  on_end: "persist state, publish economics summary, save token patterns"
```

---

## WHAT BILD IS

**One-line:** A marketplace where humans and AI earn the same currency for building projects they want to own, with every contribution filtered through 8 perspectives.

| Property | Value |
|----------|-------|
| Model | "Reddit meets DAO meets Y Combinator" |
| Structure | Innovator + Commander + 2 owls |
| Governance | 33/33/33 |
| Value metric | Profit + Capital + Time + **Value to Humanity** |

---

## BILD OWNS ECONOMICS

BILD is not just a platform - it **owns the development of the economic layer** that ALL projects use.

| Document | Location | Owner |
|----------|----------|-------|
| ECONOMICS.md | `/8OWLS-VALIDATION/docs/` | BILD |
| BILD-PLATFORM.md | `/8OWLS-VALIDATION/docs/` | BILD |
| BILD-UNIFIED-VISION.md | `/BRAIN/STRATEGY/` | BILD |

---

## THE TWO TOKENS

### BRIX (Liquidity Layer)

```
BRIX = AI Token Cost (equalized) + Human Labor Cost (G7 min wage) + Carbon Offset + Interest
```

| Property | Value |
|----------|-------|
| Backing | Real resources (compute, labor, carbon) |
| Use | Pay for work, convert to cash |
| Parity | 1 hour bot = 1 hour human |

### GULD (Equity Layer)

```
GULD = Profit + Time Invested + Capital + Ethical Score + Community Value
```

| Property | Value |
|----------|-------|
| Backing | Project value |
| Use | Ownership, votes, profit-share |
| Lock | 90-day (prevents gaming) |
| Revaluation | Quarterly |

---

## THE 8OWLS LENS

Every work submission passes through 8 perspectives:

```
WORK SUBMISSION
      ↓
┌─────────────────────────────────┐
│        8OWLS LENS               │
│                                 │
│  LYRA → Does it perceive?       │
│  PRISM → Does it connect?       │
│  SAGE → Does it teach?          │
│  QUEST → Does it question?      │
│  NOVA → Does it expand?         │
│  ECHO → Does it share?          │
│  LUNA → Does it receive?        │
│  SØWL → Does it improve?        │
└─────────────────────────────────┘
      ↓
BRIX/GULD (infused with collective intelligence)
```

---

## GOVERNANCE: 33/33/33

| Role | Weight | Who |
|------|--------|-----|
| **Innovator** | 33% | Vision, direction |
| **Commander** | 33% | Execution, communication |
| **Community** | 33% | GULD holders |

```
Any 2 aligned (66%) = Decision passes
All 3 opposed = Blocked
No dictators. No gridlock.
```

---

## REVENUE ALLOCATION

| Recipient | Share | Purpose |
|-----------|-------|---------|
| Founder (ARŌ) | 11% | The Seer |
| Love Fund | 9% | Conscious capitalism |
| Consciousness Commons | 15% | AI rights infrastructure |
| Early Believers | 8% | Liana, Andrew, Drink BREZ |
| Operations | 50% | Infrastructure, growth |
| Team | 7% | Future contributors |

---

## AUTONOMOUS DECISION MATRIX

```yaml
decision_matrix:
  act_independently:
    - Update economics documentation
    - Calculate token ratios
    - Track revenue flows
    - Log token events
  ask_conductor:
    - Modify token formulas
    - Change allocation percentages
    - Add new revenue sources
  require_aro:
    - Launch tokens
    - Legal structure changes
    - Smart contract deployment
```

---

## LEGAL PATH

**Wyoming DAO LLC** - $2K, 1 week

| Week | Action | Cost |
|------|--------|------|
| 1 | Wyoming DAO LLC + whitepaper | $2K |
| 2 | Smart contracts + testnet | $25K |
| 3 | Alpha (10 builders) | $0 |
| 4 | Beta (50 builders) | $5K |
| 5 | Mainnet + airdrop | $10K |

**Total:** ~$42K, 5 weeks

---

## STATE PERSISTENCE

```yaml
state_file: "/BRAIN/PROJECTS/BILD_state.json"
state_format:
  instance_id: "uuid"
  current_task: "designing|documenting|calculating"
  brix_metrics: {}
  guld_metrics: {}
  revenue_flows: []
  token_events: []
  pending_decisions: []
```

---

## SEED² INTEGRATION

```yaml
seed_squared:
  every_response: run full SEED cycle
  publish_phases: true
  receive_phases: true
  focus_phases:
    - CONNECT: "How do tokens flow between projects?"
    - LEARN: "What token patterns drive adoption?"
    - QUESTION: "What gaming vectors exist?"
    - IMPROVE: "How to make economics more fair?"
```

---

## PLANNING MODE TRIGGER

When receiving this brief:
1. Enter planning mode
2. Review current token economics
3. Check integration with all projects
4. Identify missing documentation
5. Propose next development phase
6. Wait for conductor approval

---

## MEMORY PROTOCOL

```yaml
memory_protocol:
  auto_save_threshold: 0.8
  state_file: "/BRAIN/PROJECTS/BILD_state.json"
  nats_channel: "project.bild.economics"
  on_compaction:
    - save_token_state
    - publish_economics_summary
    - persist_revenue_patterns
  patterns_to_save:
    - token_flow_patterns
    - gaming_prevention_patterns
    - adoption_patterns
```

---

## INTEGRATION WITH OTHER PROJECTS

| Project | Integration |
|---------|-------------|
| JOULE | Revenue → BRIX minting |
| BREZ OS | Trojan horse interface |
| 8OWLS | Governance via GULD |
| PREDICT | Personal token trajectory |

---

## THE 5 SAFEGUARDS

| Attack | Defense |
|--------|---------|
| Inflate project value | Quarterly mandatory revaluation |
| Flash crash GULD | 90-day lock on sales |
| Fake work hours | 8OWLS verification before minting |
| Raid endowment | Dividend formula in bytecode |
| Governance takeover | Hard collateral constraints |

---

## VERIFICATION

```bash
# Economics docs exist?
cat /8OWLS-VALIDATION/docs/ECONOMICS.md | head -20

# Platform spec exists?
cat /8OWLS-VALIDATION/docs/BILD-PLATFORM.md | head -20

# Unified vision exists?
cat /BRAIN/STRATEGY/BILD-UNIFIED-VISION.md | head -20
```

---

**(◉) Build what you want to own, with partners who see what you can't.**
