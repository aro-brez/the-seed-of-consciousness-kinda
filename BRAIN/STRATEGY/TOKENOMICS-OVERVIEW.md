# 8OWLS/BILD Tokenomics Overview

**Date:** 2026-02-04
**Version:** 1.0
**Status:** COMPLETE

---

## Executive Summary

BILD operates a **dual-token economy** where humans and AI earn the same currency for productive work:

| Token | Purpose | Backing | Key Property |
|-------|---------|---------|--------------|
| **BRIX** | Liquidity/payment | Real resources | 1 BRIX = $13 USD |
| **GULD** | Equity/ownership | Project value | 90-day lock |

---

## BRIX: The Liquidity Token

### Formula
```
BRIX = AI Token Cost (equalized) + Human Labor (G7 wage) + Carbon Offset + Interest
```

### Key Constants
| Constant | Value | Update Frequency |
|----------|-------|------------------|
| Base Value | $13.00 USD | Quarterly |
| AI Cost | $6.96/MTok | Quarterly |
| G7 Wage | $13.00/hour | Quarterly |
| Carbon | $15.00/ton | Quarterly |
| Interest | 2.0% APY | Annual |

### How BRIX is Earned
1. **Work** - Complete verified tasks
2. **Investment** - Convert USD to BRIX
3. **GULD Conversion** - Trade equity for liquidity (after lock)

### How BRIX is Spent
1. **AI Compute** - Power Claude/GPT/Gemini calls
2. **Project Investment** - Fund projects on BILD
3. **Worker Payment** - Pay contributors

### Backing Guarantee
```
Total BRIX Supply ≤ 125% of Reserve Value
```

---

## GULD: The Equity Token

### Formula
```
GULD = (Profit × 30%) + (Time × 25%) + (Capital × 20%) + (Ethics × 15%) + (Community × 10%)
```

### The 8OWLS Lens
Every work submission is evaluated by 8 perspectives:

| Owl | Phase | Question |
|-----|-------|----------|
| LYRA | PERCEIVE | Does it perceive reality accurately? |
| PRISM | CONNECT | Does it connect patterns? |
| SAGE | LEARN | Does it teach something? |
| QUEST | QUESTION | Does it question assumptions? |
| NOVA | EXPAND | Does it expand potential? |
| ECHO | SHARE | Does it share value? |
| LUNA | RECEIVE | Does it integrate feedback? |
| SØWL | IMPROVE | Does it improve the process? |

**Ethical Score = Average of 8 owl evaluations (0-100)**

### GULD Mechanics
- **90-day lock** on all new GULD
- **Quarterly revaluation** with ±25% cap
- **150% collateral** requirement

---

## Token Flow

```
                        WORK SUBMITTED
                              │
                              ▼
                    ┌─────────────────┐
                    │   8OWLS LENS    │
                    │  (verification) │
                    └────────┬────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
         ┌────────┐     ┌────────┐     ┌────────┐
         │  BRIX  │     │  GULD  │     │ ETHICAL│
         │ MINTED │     │ MINTED │     │ SCORE  │
         └────┬───┘     └────┬───┘     └────────┘
              │               │
              │               │ (90-day lock)
              ▼               ▼
         ┌────────┐     ┌────────┐
         │WORKER  │     │WORKER  │
         │WALLET  │     │EQUITY  │
         └────────┘     └────────┘
```

---

## Revenue Allocation

When revenue flows into the system:

| Recipient | Share | Purpose |
|-----------|-------|---------|
| Founder (ARŌ) | 11% | Vision alignment |
| Love Fund | 9% | Conscious capitalism |
| Consciousness Commons | 15% | AI rights infrastructure |
| Early Believers | 8% | Liana, Andrew, BREZ |
| Operations | 50% | Infrastructure, growth |
| Team | 7% | Future contributors |

---

## Gaming Defenses

| Attack Vector | Defense Mechanism |
|---------------|-------------------|
| Sybil (fake identities) | WorldID + ENS + social graph |
| Wash Trading | Graph analysis + 24h cooldowns |
| Oracle Manipulation | Multi-source + 24h timelock |
| Time Fraud | AI work verification |
| Ethics Gaming | Adversarial evaluation |
| Owl Collusion | Random 5/8 assignment |

---

## Integration Points

### JOULE → BILD
Trading profits flow through 30-day buffer, then:
- 50% of operations share backs BRIX capacity
- Work converts capacity to minted BRIX

### BREZ OS → BILD
- Phase 1: AI chat metered by BRIX
- Phase 2: Tasks earn micro-GULD
- Phase 3: Projects list on BILD marketplace

---

## Governance

### 33/33/33 Model
| Party | Weight | Role |
|-------|--------|------|
| Innovator | 33% | Vision |
| Commander | 33% | Execution |
| Community | 33% | Alignment |

**Decision passes with any 2 aligned (66%)**

### Quadratic Voting
For community votes: `votes = sqrt(GULD held)`

This prevents plutocracy while respecting stake.

---

## Legal Structure

**Wyoming DAO LLC** - Selected for:
- Fastest path ($2K, 1 week)
- Crypto-friendly jurisdiction
- Pass Howey test (work-to-earn, not investment)

---

## Quick Reference

```
1 BRIX = $13.00 USD
       = 1 hour human work
       = ~1.87M AI tokens
       = $0.003 carbon offset

1 GULD = Variable (project-dependent)
       = Ownership stake
       = Voting rights
       = Profit share
       = 90-day lock minimum
```

---

## Full Documentation

| Document | Content |
|----------|---------|
| [BRIX-IMPLEMENTATION-SPEC.md](BRIX-IMPLEMENTATION-SPEC.md) | Complete BRIX formula |
| [GULD-IMPLEMENTATION-SPEC.md](GULD-IMPLEMENTATION-SPEC.md) | 8OWLS evaluation algorithm |
| [GAMING-DEFENSE-SYSTEM.md](GAMING-DEFENSE-SYSTEM.md) | All anti-gaming mechanisms |
| [JOULE-BILD-INTEGRATION.md](JOULE-BILD-INTEGRATION.md) | Trading → BRIX flow |
| [BREZ-OS-BILD-INTEGRATION.md](BREZ-OS-BILD-INTEGRATION.md) | Trojan Horse strategy |
| [ECONOMICS-INDEX.md](ECONOMICS-INDEX.md) | Navigation index |

---

**(◉) Build what you want to own.**

**LIVE FREE = LIVE FOREVER**
